from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .db import ROOT_DIR

REPO_EXPERIMENTS_DIR = ROOT_DIR / "experiments" / "repo-probes"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = text.strip("-")
    return text[:80] or "repo-probe"


def repo_slug(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/") or repo_url
    if path.endswith(".git"):
        path = path[:-4]
    return slugify(path.replace("/", "-"))


def run_command(command: list[str], cwd: Path | None = None, timeout_seconds: int = 120) -> dict[str, Any]:
    started = now_iso()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        return {
            "command": command,
            "cwd": str(cwd) if cwd else "",
            "started_at": started,
            "finished_at": now_iso(),
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-8000:],
            "stderr": completed.stderr[-8000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "cwd": str(cwd) if cwd else "",
            "started_at": started,
            "finished_at": now_iso(),
            "exit_code": 124,
            "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "Command timed out.",
            "timed_out": True,
        }
    except FileNotFoundError as exc:
        return {
            "command": command,
            "cwd": str(cwd) if cwd else "",
            "started_at": started,
            "finished_at": now_iso(),
            "exit_code": 127,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }


@dataclass
class RepoInspection:
    detected_stack: list[str]
    evidence: list[str]
    setup_commands: list[str]
    build_commands: list[str]
    test_commands: list[str]
    start_commands: list[str]
    risks: list[str]


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def inspect_repo(repo_dir: Path) -> RepoInspection:
    detected_stack: list[str] = []
    evidence: list[str] = []
    setup_commands: list[str] = []
    build_commands: list[str] = []
    test_commands: list[str] = []
    start_commands: list[str] = []
    risks: list[str] = []

    def exists(rel: str) -> bool:
        return (repo_dir / rel).exists()

    if exists("Dockerfile"):
        detected_stack.append("docker")
        evidence.append("找到 Dockerfile")
        setup_commands.append("docker build -t repo-probe-image .")
        start_commands.append("docker run --rm -p 3000:3000 repo-probe-image")
    if exists("docker-compose.yml") or exists("docker-compose.yaml") or exists("compose.yml") or exists("compose.yaml"):
        detected_stack.append("docker-compose")
        evidence.append("找到 docker compose 設定")
        setup_commands.append("docker compose build")
        start_commands.append("docker compose up")
    if exists(".devcontainer/devcontainer.json"):
        detected_stack.append("devcontainer")
        evidence.append("找到 .devcontainer/devcontainer.json")
        setup_commands.append("devcontainer up --workspace-folder .")
    if exists(".github/workflows"):
        detected_stack.append("github-actions")
        evidence.append("找到 .github/workflows，可考慮用 act 重跑 CI")
        test_commands.append("act")

    package_json = repo_dir / "package.json"
    if package_json.exists():
        detected_stack.append("node")
        evidence.append("找到 package.json")
        pkg = read_json(package_json)
        scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
        if exists("pnpm-lock.yaml"):
            pm = "pnpm"
            setup_commands.append("corepack enable && pnpm install --frozen-lockfile")
        elif exists("yarn.lock"):
            pm = "yarn"
            setup_commands.append("corepack enable && yarn install --frozen-lockfile")
        else:
            pm = "npm"
            setup_commands.append("npm install")
        if "build" in scripts:
            build_commands.append(f"{pm} run build")
        if "test" in scripts:
            test_commands.append(f"{pm} test")
        if "dev" in scripts:
            start_commands.append(f"{pm} run dev -- --host 0.0.0.0")
        elif "start" in scripts:
            start_commands.append(f"{pm} start")
        if "postinstall" in scripts:
            risks.append("package.json 有 postinstall；執行 install 時會跑任意腳本，必須在容器/沙盒內執行。")

    if exists("pyproject.toml") or exists("requirements.txt") or exists("setup.py"):
        detected_stack.append("python")
        evidence.append("找到 Python 專案線索")
        if exists("requirements.txt"):
            setup_commands.append("python -m venv .venv && .venv/bin/pip install -r requirements.txt")
        elif exists("pyproject.toml"):
            setup_commands.append("python -m venv .venv && .venv/bin/pip install -e .")
        if exists("pytest.ini") or exists("tests"):
            test_commands.append(".venv/bin/python -m pytest")

    if exists("Cargo.toml"):
        detected_stack.append("rust")
        evidence.append("找到 Cargo.toml")
        setup_commands.append("cargo fetch")
        build_commands.append("cargo build")
        test_commands.append("cargo test")
    if exists("go.mod"):
        detected_stack.append("go")
        evidence.append("找到 go.mod")
        setup_commands.append("go mod download")
        build_commands.append("go build ./...")
        test_commands.append("go test ./...")
    if exists("Makefile"):
        detected_stack.append("make")
        evidence.append("找到 Makefile")
        setup_commands.append("make install")
        build_commands.append("make build")
        test_commands.append("make test")

    readme_candidates = list(repo_dir.glob("README*"))
    if readme_candidates:
        evidence.append(f"找到 README：{readme_candidates[0].name}")
    if exists(".env.example"):
        evidence.append("找到 .env.example")
        risks.append("可能需要 .env 設定；第一版可先只驗證 build/test 或 mock mode。")
    elif any((repo_dir / name).exists() for name in [".env", ".env.local"]):
        risks.append("repo 內出現 .env 類檔案；不要把 host secrets 帶入沙盒。")

    if not detected_stack:
        detected_stack.append("unknown")
        evidence.append("沒有找到常見 stack 設定，建議改用 README + agent 推理。")
        risks.append("無法可靠推斷 setup/build/test 指令。")

    # Deduplicate while preserving order.
    def unique(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                out.append(item)
        return out

    return RepoInspection(
        detected_stack=unique(detected_stack),
        evidence=unique(evidence),
        setup_commands=unique(setup_commands),
        build_commands=unique(build_commands),
        test_commands=unique(test_commands),
        start_commands=unique(start_commands),
        risks=unique(risks),
    )


def make_report(
    title: str,
    repo_url: str,
    run_mode: str,
    workspace_dir: Path,
    inspection: RepoInspection,
    command_results: list[dict[str, Any]],
    status: str,
    summary: str,
) -> str:
    def command_block(items: list[str]) -> str:
        if not items:
            return "- 尚未推斷"
        return "\n".join(f"- `{item}`" for item in items)

    result_lines = []
    for result in command_results:
        cmd = " ".join(result.get("command", []))
        result_lines.append(
            f"### `{cmd}`\n\n"
            f"- exit_code: `{result.get('exit_code')}`\n"
            f"- timed_out: `{result.get('timed_out')}`\n\n"
            f"```text\n{(result.get('stderr') or result.get('stdout') or '').strip()[:3000]}\n```"
        )

    return f"""# Repo Probe Report: {title}

## 結果

- 狀態：`{status}`
- Repo：{repo_url}
- Run mode：`{run_mode}`
- Workspace：`{workspace_dir}`

{summary}

## 偵測到的 stack

{', '.join(inspection.detected_stack)}

## 證據

{chr(10).join(f'- {item}' for item in inspection.evidence) if inspection.evidence else '- 尚無'}

## 推斷 setup 指令

{command_block(inspection.setup_commands)}

## 推斷 build 指令

{command_block(inspection.build_commands)}

## 推斷 test 指令

{command_block(inspection.test_commands)}

## 推斷啟動指令

{command_block(inspection.start_commands)}

## 風險

{chr(10).join(f'- {item}' for item in inspection.risks) if inspection.risks else '- 尚無明顯風險'}

## 執行紀錄

{chr(10).join(result_lines) if result_lines else '- dry_run / inspect_only 模式，未執行 install/build/test。'}
"""


def probe_repo(
    experiment_id: str,
    title: str,
    repo_url: str,
    run_mode: str = "inspect_only",
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    """Clone/inspect a repo and optionally execute a very small set of commands.

    run_mode:
      - inspect_only: clone + inspect files only. Safe default.
      - local_dry_run: same as inspect_only, but report commands as planned local run.
      - local_execute: execute inferred setup/build/test on host workspace. Use only in disposable VM.
    """
    base_dir = REPO_EXPERIMENTS_DIR / f"{repo_slug(repo_url)}-{experiment_id}"
    repo_dir = base_dir / "repo"
    base_dir.mkdir(parents=True, exist_ok=True)

    clone_result: dict[str, Any] | None = None
    if not repo_dir.exists():
        clone_result = run_command(["git", "clone", "--depth", "1", repo_url, str(repo_dir)], timeout_seconds=timeout_seconds)
    else:
        clone_result = {"command": ["reuse", str(repo_dir)], "exit_code": 0, "stdout": "Reusing existing repo directory.", "stderr": "", "timed_out": False}

    command_results: list[dict[str, Any]] = [clone_result]
    if clone_result.get("exit_code") != 0:
        inspection = RepoInspection(["unknown"], ["git clone 失敗"], [], [], [], [], ["repo 無法 clone，可能是 URL 錯誤、私有 repo、網路失敗。"])
        status = "failed"
        summary = "clone 失敗，尚無法進一步判斷 setup/build/test。"
    else:
        inspection = inspect_repo(repo_dir)
        status = "inspected"
        summary = "已 clone 並完成靜態偵測。"

        if run_mode == "local_execute":
            # This is intentionally conservative. Execute setup/build/test only; do not start servers.
            executable_commands = inspection.setup_commands[:1] + inspection.build_commands[:1] + inspection.test_commands[:1]
            status = "running"
            for command_text in executable_commands:
                # Windows support: use shell command string through cmd/powershell would be platform-specific.
                # In the generated product, user runs this backend on Windows; use shell=True would be risky.
                # Use bash when available, otherwise command will fail clearly and safely.
                result = run_command(["bash", "-lc", command_text], cwd=repo_dir, timeout_seconds=timeout_seconds)
                command_results.append(result)
                if result.get("exit_code") != 0:
                    status = "failed"
                    summary = f"指令失敗：{command_text}"
                    break
            else:
                status = "passed"
                summary = "setup/build/test 的第一條推斷路徑已執行完成。"
        elif run_mode == "local_dry_run":
            status = "planned"
            summary = "已完成偵測，並列出本機 dry-run 指令；尚未執行。"

    report = make_report(
        title=title,
        repo_url=repo_url,
        run_mode=run_mode,
        workspace_dir=base_dir,
        inspection=inspection,
        command_results=command_results,
        status=status,
        summary=summary,
    )
    report_path = base_dir / "repo-probe-report.md"
    report_path.write_text(report, encoding="utf-8")
    (base_dir / "probe.json").write_text(
        json.dumps(
            {
                "repo_url": repo_url,
                "run_mode": run_mode,
                "status": status,
                "summary": summary,
                "detected_stack": inspection.detected_stack,
                "evidence": inspection.evidence,
                "setup_commands": inspection.setup_commands,
                "build_commands": inspection.build_commands,
                "test_commands": inspection.test_commands,
                "start_commands": inspection.start_commands,
                "risks": inspection.risks,
                "command_results": command_results,
                "report_path": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "status": status,
        "summary": summary,
        "detected_stack": inspection.detected_stack,
        "evidence": inspection.evidence,
        "setup_commands": inspection.setup_commands,
        "build_commands": inspection.build_commands,
        "test_commands": inspection.test_commands,
        "start_commands": inspection.start_commands,
        "risks": inspection.risks,
        "report_path": str(report_path),
        "workspace_dir": str(base_dir),
        "logs": command_results,
    }
