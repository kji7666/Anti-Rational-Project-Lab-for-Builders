from __future__ import annotations

from pathlib import Path
from typing import Any

from .db import ROOT_DIR
from .mvp import build_mvp_draft, build_idea_card, build_tasks_md, build_acceptance_md, build_codex_prompt, build_context_md, slugify

PROTOTYPE_ROOT = ROOT_DIR / "prototypes"


def build_workspace_files(idea: dict[str, Any], worker: str = "manual") -> dict[str, str]:
    draft = build_mvp_draft(idea)
    worker_prompt = build_worker_prompt(idea, draft, worker)
    return {
        "docs/idea-card.md": build_idea_card(idea),
        "docs/mvp.md": draft["markdown"],
        "docs/tasks.md": build_tasks_md(idea, draft),
        "docs/acceptance.md": build_acceptance_md(idea, draft),
        "docs/context.md": build_context_md(idea, draft),
        "prompts/codex-prompt.md": build_codex_prompt(idea, draft),
        "prompts/opencode-prompt.md": build_worker_prompt(idea, draft, "opencode"),
        "prompts/worker-prompt.md": worker_prompt,
        "runs/README.md": build_runs_readme(idea),
        "README.md": build_workspace_readme(idea, worker),
    }


def create_prototype_workspace_files(idea: dict[str, Any], worker: str = "manual", overwrite: bool = False) -> dict[str, Any]:
    slug = slugify(idea.get("name") or idea["id"])
    workspace_dir = PROTOTYPE_ROOT / f"{slug}-{idea['id'][-6:]}"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    files = build_workspace_files(idea, worker)
    written: list[str] = []
    skipped: list[str] = []
    for relative_path, content in files.items():
        path = workspace_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            skipped.append(str(path.relative_to(ROOT_DIR)))
            continue
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(ROOT_DIR)))

    for dirname in ["src", "logs", "runs", "scratch"]:
        (workspace_dir / dirname).mkdir(exist_ok=True)

    return {
        "directory": str(workspace_dir.relative_to(ROOT_DIR)),
        "written_files": written,
        "skipped_files": skipped,
        "worker": worker,
    }


def build_workspace_readme(idea: dict[str, Any], worker: str) -> str:
    return f"""# {idea.get('name')} Prototype Workspace

這個資料夾由怪題研究所 Phase 7 產生，用來把題目卡推進到可實作 prototype。

## 題目
{idea.get('one_liner') or '尚未填寫一句話。'}

## 建議 worker
{worker}

## 目錄
- `docs/`：題目卡、MVP、任務、驗收標準與 context。
- `prompts/`：可貼給 Codex / OpenCode / 人類 worker 的 prompt。
- `src/`：prototype 實作區。
- `runs/`：每次實作或驗收紀錄。
- `logs/`：執行 log。
- `scratch/`：臨時研究與草稿。

## 建議流程
1. 先讀 `docs/mvp.md` 與 `docs/acceptance.md`。
2. 使用 `prompts/worker-prompt.md` 交給指定 worker。
3. 實作結果寫入 `src/`。
4. 每次執行後在怪題研究所 UI 新增 prototype run。
5. 根據結果決定：繼續、重想、丟進墳場、或進下一版。
"""


def build_runs_readme(idea: dict[str, Any]) -> str:
    return f"""# Runs

這裡存放「{idea.get('name')}」每次 prototype 執行、驗收或人工測試的紀錄。

建議每次 run 建立一個 markdown：

```text
runs/2026-xx-xx-run-01.md
```

每次 run 建議記錄：

- 使用 worker：Codex / OpenCode / Manual
- 做了什麼
- 修改了哪些檔案
- 跑了哪些測試
- 成功或失敗
- 下一步
"""


def build_worker_prompt(idea: dict[str, Any], draft: dict[str, Any], worker: str) -> str:
    worker_name = {
        "codex": "Codex",
        "opencode": "OpenCode",
        "manual": "人類開發者",
    }.get(worker, worker)
    return f"""你現在要擔任「{worker_name}」worker，協助實作「{idea.get('name')}」prototype。

## 任務目標
{idea.get('one_liner') or '尚未填寫'}

## 背後痛點
{idea.get('real_pain') or '尚未填寫'}

## 怪味定位
{idea.get('weird_angle') or '尚未填寫'}

## 第一版只做
{_bullets(draft['do_items'])}

## 第一版不做
{_bullets(draft['dont_items'])}

## 任務清單
{_numbered(draft['tasks'])}

## 驗收標準
{_bullets(draft['acceptance'])}

## 工作規則
- 先做最小可跑版本，不要擴大 scope。
- 盡量把改動放在 prototype workspace 裡。
- 完成後回報：修改檔案、如何啟動、如何驗收、已知問題、下一步。
- 遇到不確定時，優先保持題目的怪味與 MVP 邊界。
"""


def build_run_markdown(run: dict[str, Any]) -> str:
    return f"""# Prototype Run: {run.get('title') or run.get('id')}

## Worker
{run.get('worker')}

## 狀態
{run.get('status')}

## 目標
{run.get('goal') or '尚未填寫'}

## 摘要
{run.get('summary') or '尚未填寫'}

## 修改檔案
{_bullets(run.get('changed_files') or [])}

## 測試指令
{_bullets(run.get('test_commands') or [])}

## 結果
{run.get('result') or '尚未填寫'}

## 下一步
{run.get('next_step') or '尚未填寫'}
"""


def write_run_markdown(workspace_directory: str, run: dict[str, Any]) -> str | None:
    if not workspace_directory:
        return None
    workspace = ROOT_DIR / workspace_directory
    runs_dir = workspace / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{run['id']}.md"
    path.write_text(build_run_markdown(run), encoding="utf-8")
    return str(path.relative_to(ROOT_DIR))


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 尚未填寫"


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{index + 1}. {item}" for index, item in enumerate(items)) if items else "1. 尚未填寫"
