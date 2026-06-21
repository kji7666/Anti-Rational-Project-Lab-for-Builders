from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Any

from . import crud
from .collectors import collect_many
from .evolution import build_family_suggestions, revive_suggestions
from .generator import generated_idea_payloads
from .llm_pipeline import LocalLLMPipelineError, run_local_llm_pipeline
from .schemas import IdeaCreate, SignalCreate

TICK_SECONDS = 60


def local_now() -> datetime:
    return datetime.now().astimezone()


def to_iso(dt: datetime | None) -> str:
    return dt.isoformat() if dt else ""


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_time_of_day(value: str | None) -> tuple[int, int]:
    text = (value or "").strip() or "09:00"
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = max(0, min(23, int(hour_text)))
        minute = max(0, min(59, int(minute_text)))
        return hour, minute
    except Exception:
        return 9, 0


def normalize_idea_name(value: str) -> str:
    return " ".join((value or "").lower().split())


def compute_next_run(job: dict[str, Any], from_dt: datetime | None = None) -> str:
    if not job.get("enabled"):
        return ""

    base = from_dt or local_now()
    schedule_type = job.get("schedule_type") or "daily"
    time_of_day = job.get("time_of_day") or "09:00"
    hour, minute = parse_time_of_day(time_of_day)

    if schedule_type == "interval":
        interval_minutes = int(job.get("interval_minutes") or 60)
        last_run = parse_iso(job.get("last_run_at"))
        next_dt = (last_run or base) + timedelta(minutes=max(5, interval_minutes))
        if next_dt <= base:
            next_dt = base + timedelta(minutes=max(5, interval_minutes))
        return to_iso(next_dt)

    next_dt = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if schedule_type == "weekly":
        target_day = int(job.get("day_of_week") or 0)
        days_ahead = (target_day - next_dt.weekday()) % 7
        if days_ahead == 0 and next_dt <= base:
            days_ahead = 7
        next_dt = next_dt + timedelta(days=days_ahead)
        return to_iso(next_dt)

    if next_dt <= base:
        next_dt = next_dt + timedelta(days=1)
    return to_iso(next_dt)


def default_jobs() -> list[dict[str, Any]]:
    return [
        {
            "job_key": "daily_signal_collection",
            "name": "每日訊號收集",
            "description": "每日從安全公開來源收集新素材，保留去重與內建補位行為。",
            "enabled": True,
            "schedule_type": "daily",
            "time_of_day": "09:00",
            "config_json": {
                "query": "AI developer tools agent repo setup build test",
                "sources": ["github", "hacker_news", "arxiv"],
                "limit_per_source": 3,
            },
        },
        {
            "job_key": "daily_weird_idea_generation",
            "name": "每日怪題產生",
            "description": "使用近期高品質素材產生少量怪題，Local GPT 不可用時會改用模板產生。",
            "enabled": False,
            "schedule_type": "daily",
            "time_of_day": "09:30",
            "config_json": {"count": 3, "max_signals": 6, "min_quality_score": 60},
        },
        {
            "job_key": "weekly_graveyard_review",
            "name": "每週墳場巡檢",
            "description": "每週整理可復活題目建議，不會自動改動狀態。",
            "enabled": False,
            "schedule_type": "weekly",
            "time_of_day": "10:00",
            "day_of_week": 0,
            "config_json": {"limit": 8},
        },
        {
            "job_key": "weekly_idea_evolution",
            "name": "每週題目演化整理",
            "description": "每週計算題目家族與相似群，不會自動合併題目。",
            "enabled": False,
            "schedule_type": "weekly",
            "time_of_day": "10:30",
            "day_of_week": 0,
            "config_json": {},
        },
    ]


class SchedulerManager:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._running_job_keys: set[str] = set()
        self._started = False
        self._current_job_key = ""
        self._last_tick_at = ""

    def start(self) -> None:
        if self._started:
            return
        self.seed_default_jobs()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="weirdlab-scheduler", daemon=True)
        self._thread.start()
        self._started = True

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        self._thread = None
        self._started = False
        self._current_job_key = ""

    def get_status(self) -> dict[str, Any]:
        return {
            "status": "running" if self._started else "stopped",
            "running": self._started,
            "backend_note": "排程只會在 backend 行程存活時運作，backend 停止後不會自動補跑。",
            "timezone": time.tzname[0] if time.tzname else "local",
            "tick_seconds": TICK_SECONDS,
            "current_job_key": self._current_job_key,
            "last_tick_at": self._last_tick_at,
        }

    def seed_default_jobs(self) -> None:
        now = local_now()
        for job in default_jobs():
            current = crud.get_scheduled_job_by_key(job["job_key"])
            payload = {**job}
            if current:
                payload["enabled"] = current.get("enabled", job["enabled"])
                payload["last_run_at"] = current.get("last_run_at", "")
                payload["last_status"] = current.get("last_status", "idle")
                payload["last_message"] = current.get("last_message", "")
                payload["config_json"] = current.get("config_json") or job.get("config_json", {})
                payload["interval_minutes"] = current.get("interval_minutes", job.get("interval_minutes"))
                payload["time_of_day"] = current.get("time_of_day", job.get("time_of_day", ""))
                payload["day_of_week"] = current.get("day_of_week", job.get("day_of_week"))
                payload["schedule_type"] = current.get("schedule_type", job.get("schedule_type", "daily"))
            payload["next_run_at"] = compute_next_run(payload, from_dt=now)
            crud.upsert_scheduled_job(payload)

    def list_jobs(self) -> list[dict[str, Any]]:
        return crud.list_scheduled_jobs()

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return crud.list_scheduled_job_runs(limit=limit)

    def update_job(self, job_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        job = crud.get_scheduled_job(job_id)
        payload = dict(updates)
        merged = {**job, **payload}
        if "time_of_day" in payload and payload["time_of_day"] is None:
            payload["time_of_day"] = job.get("time_of_day", "")
            merged["time_of_day"] = payload["time_of_day"]
        payload["next_run_at"] = compute_next_run(merged, from_dt=local_now())
        return crud.update_scheduled_job(job_id, payload)

    def run_job_now(self, job_id: str) -> dict[str, Any]:
        job = crud.get_scheduled_job(job_id)
        return self._run_job(job)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._last_tick_at = to_iso(local_now())
            try:
                self.seed_default_jobs()
                due_jobs = []
                now = local_now()
                for job in crud.list_scheduled_jobs():
                    if not job.get("enabled"):
                        continue
                    next_run = parse_iso(job.get("next_run_at"))
                    if next_run and next_run <= now:
                        due_jobs.append(job)
                for job in due_jobs:
                    self._run_job(job)
            except Exception:
                pass
            self._stop_event.wait(TICK_SECONDS)

    def _run_job(self, job: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if job["job_key"] in self._running_job_keys:
                return {
                    "job": job,
                    "run": None,
                    "message": "這個排程目前正在執行中，已略過重複觸發。",
                }
            self._running_job_keys.add(job["job_key"])
            self._current_job_key = job["job_key"]

        run = crud.create_scheduled_job_run(job["id"], job["job_key"], status="running")
        started = local_now()
        status = "passed"
        summary = ""
        warning = ""
        error = ""
        result_json: dict[str, Any] = {}

        try:
            result_json = self._dispatch_job(job)
            summary = result_json.get("summary", "")
            warning = result_json.get("warning", "")
            status = result_json.get("status", "passed")
        except Exception as exc:
            status = "failed"
            error = str(exc)
            summary = "排程執行失敗。"
            result_json = {"summary": summary, "error": error}

        finished = local_now()
        duration_seconds = round((finished - started).total_seconds(), 3)
        updated_run = crud.update_scheduled_job_run(
            run["id"],
            {
                "status": status,
                "finished_at": to_iso(finished),
                "duration_seconds": duration_seconds,
                "summary": summary,
                "warning": warning,
                "error": error,
                "result_json": result_json,
            },
        )

        next_run_at = compute_next_run(job, from_dt=finished)
        updated_job = crud.update_scheduled_job(
            job["id"],
            {
                "last_run_at": to_iso(finished),
                "last_status": status,
                "last_message": warning or error or summary,
                "next_run_at": next_run_at,
            },
        )

        with self._lock:
            self._running_job_keys.discard(job["job_key"])
            self._current_job_key = ""

        return {"job": updated_job, "run": updated_run, "message": warning or summary}

    def _dispatch_job(self, job: dict[str, Any]) -> dict[str, Any]:
        job_key = job["job_key"]
        if job_key == "daily_signal_collection":
            return self._run_daily_signal_collection(job)
        if job_key == "daily_weird_idea_generation":
            return self._run_daily_weird_idea_generation(job)
        if job_key == "weekly_graveyard_review":
            return self._run_weekly_graveyard_review(job)
        if job_key == "weekly_idea_evolution":
            return self._run_weekly_idea_evolution(job)
        return {"status": "failed", "summary": "未知排程工作。", "error": job_key}

    def _run_daily_signal_collection(self, job: dict[str, Any]) -> dict[str, Any]:
        config = job.get("config_json") or {}
        existing_signals = crud.list_signals()
        result = collect_many(
            sources=config.get("sources") or ["github", "hacker_news", "arxiv"],
            query=config.get("query") or "AI developer tools agent repo setup build test",
            limit_per_source=int(config.get("limit_per_source") or 3),
            feed_urls=config.get("feed_urls") or [],
            custom_urls=config.get("custom_urls") or [],
            existing_signals=existing_signals,
        )
        saved_count = 0
        for item in result.get("signals", []):
            crud.create_signal(SignalCreate(**item))
            saved_count += 1
        stats = result.get("stats", {})
        summary = f"已完成訊號收集，新增 {saved_count} 則素材。"
        warning = "；".join(result.get("warnings") or [])
        return {
            "status": "passed",
            "summary": summary,
            "warning": warning,
            "saved_count": saved_count,
            "stats": stats,
            "errors": result.get("errors", []),
        }

    def _run_daily_weird_idea_generation(self, job: dict[str, Any]) -> dict[str, Any]:
        config = job.get("config_json") or {}
        max_signals = int(config.get("max_signals") or 6)
        min_quality_score = int(config.get("min_quality_score") or 60)
        candidate_signals = [
            signal
            for signal in crud.list_signals()
            if (signal.get("quality_score") or 0) >= min_quality_score
        ][:max_signals]
        if not candidate_signals:
            candidate_signals = crud.list_signals()[:max_signals]
        if not candidate_signals:
            return {
                "status": "passed",
                "summary": "沒有可用素材，因此略過怪題產生。",
                "warning": "素材箱目前是空的。",
                "saved_count": 0,
            }

        source_signal_ids = [item["id"] for item in candidate_signals]
        combined_text = "\n\n".join(
            "\n".join(part for part in [signal.get("title", ""), signal.get("summary", ""), signal.get("raw_text", "")] if part)
            for signal in candidate_signals
        )
        count = int(config.get("count") or 3)
        warnings: list[str] = []
        provider_used = "heuristic"
        try:
            generated = run_local_llm_pipeline(text=combined_text, source_signal_ids=source_signal_ids, count=count)["ideas"]
            provider_used = "local_gpt"
        except LocalLLMPipelineError as exc:
            warnings.append(f"Local GPT 無法使用，已改用模板產生：{exc}")
            generated = generated_idea_payloads(text=combined_text, source_signal_ids=source_signal_ids, count=count)
            provider_used = "template_fallback"

        existing_names = {normalize_idea_name(item.get("name", "")) for item in crud.list_ideas()}
        saved_count = 0
        duplicate_titles = 0
        for item in generated:
            normalized_name = normalize_idea_name(item.get("name", ""))
            if normalized_name in existing_names:
                duplicate_titles += 1
                continue
            save_payload = {
                "name": item.get("name", ""),
                "one_liner": item.get("one_liner", ""),
                "weird_angle": item.get("weird_angle", ""),
                "real_pain": item.get("real_pain", ""),
                "first_screen": item.get("first_screen", ""),
                "mvp": item.get("mvp", ""),
                "status": item.get("status", "new"),
                "source_signal_ids": item.get("source_signal_ids") or [],
                "scores": item.get("scores") or {},
                "status_note": item.get("status_note", ""),
                "rejection_reason": item.get("rejection_reason", ""),
                "revival_condition": item.get("revival_condition", ""),
            }
            crud.create_idea(IdeaCreate(**save_payload))
            existing_names.add(normalized_name)
            saved_count += 1

        summary = f"已完成怪題產生，新增 {saved_count} 張題目卡。"
        if duplicate_titles:
            warnings.append(f"略過 {duplicate_titles} 張重複題名的題目卡。")
        return {
            "status": "passed",
            "summary": summary,
            "warning": "；".join(warnings),
            "saved_count": saved_count,
            "duplicate_titles": duplicate_titles,
            "provider_used": provider_used,
            "source_signal_ids": source_signal_ids,
        }

    def _run_weekly_graveyard_review(self, job: dict[str, Any]) -> dict[str, Any]:
        config = job.get("config_json") or {}
        items = revive_suggestions(crud.list_ideas(), crud.list_signals(), limit=int(config.get("limit") or 8))
        return {
            "status": "passed",
            "summary": f"已完成墳場巡檢，目前有 {len(items)} 則復活建議。",
            "warning": "",
            "suggestion_count": len(items),
            "top_ideas": [item["idea"].get("name", "") for item in items[:5]],
        }

    def _run_weekly_idea_evolution(self, job: dict[str, Any]) -> dict[str, Any]:
        families = build_family_suggestions(crud.list_ideas())
        return {
            "status": "passed",
            "summary": f"已完成題目演化整理，目前有 {len(families)} 組題目家族。",
            "warning": "",
            "family_count": len(families),
            "family_names": [item.get("family_name", "") for item in families[:5]],
        }


_scheduler_manager: SchedulerManager | None = None


def get_scheduler_manager() -> SchedulerManager:
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager
