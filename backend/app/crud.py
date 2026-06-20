from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import get_connection
from .schemas import ExperimentCreate, IdeaCreate, IdeaUpdate, ReviewCreate, SignalCreate


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def decode(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return fallback


def signal_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = decode(item.get("tags", "[]"), [])
    return item


def idea_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["source_signal_ids"] = decode(item.get("source_signal_ids", "[]"), [])
    item["scores"] = decode(item.get("scores", "{}"), {})
    return item


def review_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["passes"] = bool(item["passes"])
    item["flags"] = decode(item.get("flags", "[]"), [])
    item["suggestions"] = decode(item.get("suggestions", "[]"), [])
    return item


def experiment_from_row(row: Any) -> dict[str, Any]:
    return dict(row)


def export_from_row(row: Any) -> dict[str, Any]:
    return dict(row)


def create_signal(payload: SignalCreate) -> dict[str, Any]:
    item_id = new_id("sig")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO signals (
                id, title, source_type, source_url, summary, raw_text,
                tags, weirdness, pain_signal, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                payload.title,
                payload.source_type,
                payload.source_url,
                payload.summary,
                payload.raw_text,
                encode(payload.tags),
                payload.weirdness,
                payload.pain_signal,
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    return get_signal(item_id)


def list_signals() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM signals ORDER BY created_at DESC").fetchall()
    return [signal_from_row(row) for row in rows]


def get_signal(signal_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
    if row is None:
        raise KeyError(signal_id)
    return signal_from_row(row)


def create_idea(payload: IdeaCreate) -> dict[str, Any]:
    item_id = new_id("idea")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ideas (
                id, name, one_liner, weird_angle, real_pain, first_screen,
                mvp, status, status_note, rejection_reason, revival_condition,
                source_signal_ids, scores, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                payload.name,
                payload.one_liner,
                payload.weird_angle,
                payload.real_pain,
                payload.first_screen,
                payload.mvp,
                payload.status,
                payload.status_note,
                payload.rejection_reason,
                payload.revival_condition,
                encode(payload.source_signal_ids),
                encode(payload.scores),
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    return get_idea(item_id)


def list_ideas(status: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM ideas WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM ideas ORDER BY created_at DESC").fetchall()
    return [idea_from_row(row) for row in rows]


def get_idea(idea_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    if row is None:
        raise KeyError(idea_id)
    return idea_from_row(row)


def update_idea(idea_id: str, payload: IdeaUpdate) -> dict[str, Any]:
    current = get_idea(idea_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return current

    columns: list[str] = []
    values: list[Any] = []
    # If an idea is revived or moved out of the graveyard, keep the note fields.
    # They are useful history for why it once died.
    for key, value in update_data.items():
        columns.append(f"{key} = ?")
        if key in {"source_signal_ids", "scores"}:
            values.append(encode(value))
        else:
            values.append(value)
    columns.append("updated_at = ?")
    values.append(now_iso())
    values.append(idea_id)

    with get_connection() as conn:
        conn.execute(f"UPDATE ideas SET {', '.join(columns)} WHERE id = ?", values)
        conn.commit()
    return get_idea(idea_id)


def create_review(payload: ReviewCreate) -> dict[str, Any]:
    item_id = new_id("review")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO reviews (
                id, idea_id, review_type, passes, flags, comment, suggestions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                payload.idea_id,
                payload.review_type,
                int(payload.passes),
                encode(payload.flags),
                payload.comment,
                encode(payload.suggestions),
                timestamp,
            ),
        )
        conn.commit()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (item_id,)).fetchone()
    return review_from_row(row)


def list_reviews(idea_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE idea_id = ? ORDER BY created_at DESC",
            (idea_id,),
        ).fetchall()
    return [review_from_row(row) for row in rows]


def create_experiment(payload: ExperimentCreate) -> dict[str, Any]:
    item_id = new_id("exp")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO experiments (
                id, idea_id, title, goal, method, success_criteria,
                result_status, result_summary, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                payload.idea_id,
                payload.title,
                payload.goal,
                payload.method,
                payload.success_criteria,
                payload.result_status,
                payload.result_summary,
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM experiments WHERE id = ?", (item_id,)).fetchone()
    return experiment_from_row(row)


def list_experiments(idea_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM experiments WHERE idea_id = ? ORDER BY created_at DESC",
            (idea_id,),
        ).fetchall()
    return [experiment_from_row(row) for row in rows]


def create_export_record(idea_id: str, export_type: str, path: str) -> dict[str, Any]:
    item_id = new_id("export")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO exports (id, idea_id, export_type, path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, idea_id, export_type, path, timestamp),
        )
        conn.commit()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM exports WHERE id = ?", (item_id,)).fetchone()
    return export_from_row(row)


def list_exports(idea_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM exports WHERE idea_id = ? ORDER BY created_at DESC",
            (idea_id,),
        ).fetchall()
    return [export_from_row(row) for row in rows]


def idea_event_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["related_idea_ids"] = decode(item.get("related_idea_ids", "[]"), [])
    item["metadata"] = decode(item.get("metadata", "{}"), {})
    return item


def create_idea_event(payload: Any) -> dict[str, Any]:
    item_id = new_id("event")
    timestamp = now_iso()
    # payload can be a Pydantic model or dict-like object.
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO idea_events (
                id, idea_id, event_type, title, note, related_idea_ids, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                data.get("idea_id"),
                data.get("event_type", "note"),
                data.get("title", ""),
                data.get("note", ""),
                encode(data.get("related_idea_ids", [])),
                encode(data.get("metadata", {})),
                timestamp,
            ),
        )
        conn.commit()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM idea_events WHERE id = ?", (item_id,)).fetchone()
    return idea_event_from_row(row)


def list_idea_events(idea_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM idea_events WHERE idea_id = ? ORDER BY created_at DESC",
            (idea_id,),
        ).fetchall()
    return [idea_event_from_row(row) for row in rows]


def prototype_workspace_from_row(row: Any) -> dict[str, Any]:
    return dict(row)


def prototype_run_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["changed_files"] = decode(item.get("changed_files", "[]"), [])
    item["test_commands"] = decode(item.get("test_commands", "[]"), [])
    return item


def create_prototype_workspace(idea_id: str, title: str, worker: str, directory: str, notes: str = "") -> dict[str, Any]:
    item_id = new_id("workspace")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prototype_workspaces (
                id, idea_id, title, worker, directory, status, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, idea_id, title, worker, directory, "created", notes, timestamp, timestamp),
        )
        conn.commit()
    return get_prototype_workspace(item_id)


def get_prototype_workspace(workspace_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM prototype_workspaces WHERE id = ?", (workspace_id,)).fetchone()
    if row is None:
        raise KeyError(workspace_id)
    return prototype_workspace_from_row(row)


def list_prototype_workspaces(idea_id: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if idea_id:
            rows = conn.execute(
                "SELECT * FROM prototype_workspaces WHERE idea_id = ? ORDER BY created_at DESC",
                (idea_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM prototype_workspaces ORDER BY created_at DESC").fetchall()
    return [prototype_workspace_from_row(row) for row in rows]


def update_prototype_workspace(workspace_id: str, **updates: Any) -> dict[str, Any]:
    if not updates:
        return get_prototype_workspace(workspace_id)
    columns = []
    values = []
    for key, value in updates.items():
        columns.append(f"{key} = ?")
        values.append(value)
    columns.append("updated_at = ?")
    values.append(now_iso())
    values.append(workspace_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE prototype_workspaces SET {', '.join(columns)} WHERE id = ?", values)
        conn.commit()
    return get_prototype_workspace(workspace_id)


def create_prototype_run(payload: Any) -> dict[str, Any]:
    item_id = new_id("run")
    timestamp = now_iso()
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prototype_runs (
                id, idea_id, workspace_id, title, worker, status, goal, summary,
                changed_files, test_commands, result, next_step, report_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                data.get("idea_id"),
                data.get("workspace_id"),
                data.get("title", ""),
                data.get("worker", "manual"),
                data.get("status", "planned"),
                data.get("goal", ""),
                data.get("summary", ""),
                encode(data.get("changed_files", [])),
                encode(data.get("test_commands", [])),
                data.get("result", ""),
                data.get("next_step", ""),
                data.get("report_path", ""),
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    return get_prototype_run(item_id)


def get_prototype_run(run_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM prototype_runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise KeyError(run_id)
    return prototype_run_from_row(row)


def list_prototype_runs(idea_id: str | None = None, workspace_id: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if workspace_id:
            rows = conn.execute(
                "SELECT * FROM prototype_runs WHERE workspace_id = ? ORDER BY created_at DESC",
                (workspace_id,),
            ).fetchall()
        elif idea_id:
            rows = conn.execute(
                "SELECT * FROM prototype_runs WHERE idea_id = ? ORDER BY created_at DESC",
                (idea_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM prototype_runs ORDER BY created_at DESC").fetchall()
    return [prototype_run_from_row(row) for row in rows]


def update_prototype_run(run_id: str, payload: Any) -> dict[str, Any]:
    current = get_prototype_run(run_id)
    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else dict(payload)
    if not data:
        return current
    columns = []
    values = []
    for key, value in data.items():
        columns.append(f"{key} = ?")
        if key in {"changed_files", "test_commands"}:
            values.append(encode(value))
        else:
            values.append(value)
    columns.append("updated_at = ?")
    values.append(now_iso())
    values.append(run_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE prototype_runs SET {', '.join(columns)} WHERE id = ?", values)
        conn.commit()
    return get_prototype_run(run_id)


def repo_experiment_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    for key in [
        "detected_stack",
        "evidence",
        "setup_commands",
        "build_commands",
        "test_commands",
        "start_commands",
        "risks",
        "logs",
    ]:
        item[key] = decode(item.get(key, "[]"), [])
    return item


def create_repo_experiment(idea_id: str, payload: Any, result: dict[str, Any] | None = None) -> dict[str, Any]:
    item_id = new_id("repoexp")
    timestamp = now_iso()
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
    result = result or {}
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO repo_experiments (
                id, idea_id, title, repo_url, run_mode, status, summary,
                detected_stack, evidence, setup_commands, build_commands, test_commands,
                start_commands, risks, report_path, workspace_dir, logs, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                idea_id,
                data.get("title", "Repo Probe Experiment"),
                data.get("repo_url", ""),
                data.get("run_mode", "inspect_only"),
                result.get("status", "planned"),
                result.get("summary", ""),
                encode(result.get("detected_stack", [])),
                encode(result.get("evidence", [])),
                encode(result.get("setup_commands", [])),
                encode(result.get("build_commands", [])),
                encode(result.get("test_commands", [])),
                encode(result.get("start_commands", [])),
                encode(result.get("risks", [])),
                result.get("report_path", ""),
                result.get("workspace_dir", ""),
                encode(result.get("logs", [])),
                data.get("notes", ""),
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    return get_repo_experiment(item_id)


def get_repo_experiment(experiment_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM repo_experiments WHERE id = ?", (experiment_id,)).fetchone()
    if row is None:
        raise KeyError(experiment_id)
    return repo_experiment_from_row(row)


def list_repo_experiments(idea_id: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if idea_id:
            rows = conn.execute(
                "SELECT * FROM repo_experiments WHERE idea_id = ? ORDER BY created_at DESC",
                (idea_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM repo_experiments ORDER BY created_at DESC").fetchall()
    return [repo_experiment_from_row(row) for row in rows]


def taste_feedback_from_row(row: Any) -> dict[str, Any]:
    return dict(row)


def create_taste_feedback(payload: Any, weight: int) -> dict[str, Any]:
    item_id = new_id("taste")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO taste_feedback (id, idea_id, action, weight, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_id, payload.idea_id, payload.action, int(weight), payload.note, timestamp),
        )
        conn.commit()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM taste_feedback WHERE id = ?", (item_id,)).fetchone()
    return taste_feedback_from_row(row)


def list_taste_feedback(idea_id: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if idea_id:
            rows = conn.execute(
                "SELECT * FROM taste_feedback WHERE idea_id = ? ORDER BY created_at DESC",
                (idea_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM taste_feedback ORDER BY created_at DESC").fetchall()
    return [taste_feedback_from_row(row) for row in rows]


def set_user_preference(key: str, value: Any) -> dict[str, Any]:
    timestamp = now_iso()
    payload = encode(value)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, payload, timestamp),
        )
        conn.commit()
    return {"key": key, "value": value, "updated_at": timestamp}


def get_user_preference(key: str, fallback: Any = None) -> Any:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM user_preferences WHERE key = ?", (key,)).fetchone()
    if row is None:
        return fallback
    return decode(row["value"], fallback)
