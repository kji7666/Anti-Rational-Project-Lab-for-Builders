from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .db import ROOT_DIR

EXPORT_ROOT = ROOT_DIR / "exports" / "ideas"


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_-]+", "-", text.strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned[:64] or "idea"


def _score_line(idea: dict[str, Any]) -> str:
    scores = idea.get("scores") or {}
    if not scores:
        return "尚未評分。"
    labels = {
        "surprise": "驚喜感",
        "weirdness": "怪味",
        "memorability": "記憶點",
        "visual_imagination": "畫面感",
        "real_pain": "真痛點",
        "mvp_feasibility": "一週可做性",
        "differentiation": "差異化",
        "personal_fit": "個人適配",
        "anti_saas": "反 SaaS 感",
        "revival_potential": "復活潛力",
    }
    return "\n".join(f"- {labels.get(key, key)}：{value}/10" for key, value in scores.items())


def build_mvp_draft(idea: dict[str, Any]) -> dict[str, Any]:
    name = idea.get("name") or "未命名題目"
    one_liner = idea.get("one_liner") or "尚未填寫一句話。"
    weird_angle = idea.get("weird_angle") or "尚未填寫怪味角度。"
    real_pain = idea.get("real_pain") or "尚未填寫真痛點。"
    first_screen = idea.get("first_screen") or "尚未填寫第一個畫面。"
    mvp = idea.get("mvp") or "尚未填寫 MVP 初稿。"

    inputs = _infer_inputs(idea)
    outputs = _infer_outputs(idea)
    do_items = _infer_do_items(idea)
    dont_items = _infer_dont_items(idea)
    tasks = _infer_tasks(idea)
    acceptance = _infer_acceptance(idea)
    risks = _infer_risks(idea)

    markdown = f"""# {name} MVP 草案

## 一句話
{one_liner}

## 怪在哪裡
{weird_angle}

## 背後真痛點
{real_pain}

## 第一個使用畫面
{first_screen}

## 第一版 MVP
{mvp}

## 第一版只做
{_bullets(do_items)}

## 第一版不做
{_bullets(dont_items)}

## 輸入
{_bullets(inputs)}

## 輸出
{_bullets(outputs)}

## 一週 Prototype 任務
{_numbered(tasks)}

## 驗收標準
{_bullets(acceptance)}

## 主要風險
{_bullets(risks)}

## 評分
{_score_line(idea)}
"""

    return {
        "idea_id": idea["id"],
        "name": name,
        "markdown": markdown,
        "inputs": inputs,
        "outputs": outputs,
        "do_items": do_items,
        "dont_items": dont_items,
        "tasks": tasks,
        "acceptance": acceptance,
        "risks": risks,
    }


def export_task_package(idea: dict[str, Any]) -> dict[str, Any]:
    slug = slugify(idea.get("name") or idea["id"])
    out_dir = EXPORT_ROOT / f"{slug}-{idea['id'][-6:]}"
    out_dir.mkdir(parents=True, exist_ok=True)

    draft = build_mvp_draft(idea)
    files = {
        "idea-card.md": build_idea_card(idea),
        "mvp.md": draft["markdown"],
        "tasks.md": build_tasks_md(idea, draft),
        "acceptance.md": build_acceptance_md(idea, draft),
        "codex-prompt.md": build_codex_prompt(idea, draft),
        "context.md": build_context_md(idea, draft),
    }

    written: list[str] = []
    for filename, content in files.items():
        path = out_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(ROOT_DIR)))

    return {
        "idea_id": idea["id"],
        "directory": str(out_dir.relative_to(ROOT_DIR)),
        "files": written,
    }


def build_idea_card(idea: dict[str, Any]) -> str:
    return f"""# {idea.get('name', '未命名題目')}

## 一句話
{idea.get('one_liner') or '尚未填寫'}

## 怪在哪裡
{idea.get('weird_angle') or '尚未填寫'}

## 背後真痛點
{idea.get('real_pain') or '尚未填寫'}

## 第一個畫面
{idea.get('first_screen') or '尚未填寫'}

## MVP 初稿
{idea.get('mvp') or '尚未填寫'}

## 狀態
{idea.get('status')}

## 評分
{_score_line(idea)}
"""


def build_tasks_md(idea: dict[str, Any], draft: dict[str, Any]) -> str:
    return f"""# {idea.get('name')} Prototype Tasks

## 任務清單
{_checkboxes(draft['tasks'])}

## 不做事項
{_bullets(draft['dont_items'])}
"""


def build_acceptance_md(idea: dict[str, Any], draft: dict[str, Any]) -> str:
    return f"""# {idea.get('name')} Acceptance Criteria

## 驗收標準
{_checkboxes(draft['acceptance'])}

## 輸入
{_bullets(draft['inputs'])}

## 預期輸出
{_bullets(draft['outputs'])}
"""


def build_codex_prompt(idea: dict[str, Any], draft: dict[str, Any]) -> str:
    return f"""你要實作「{idea.get('name')}」的 v0.1 prototype。

## 目標
{idea.get('one_liner') or draft['markdown']}

## 背後痛點
{idea.get('real_pain') or '尚未填寫'}

## 第一版只做
{_bullets(draft['do_items'])}

## 第一版不做
{_bullets(draft['dont_items'])}

## 任務
{_numbered(draft['tasks'])}

## 驗收標準
{_bullets(draft['acceptance'])}

## 開發要求
- 先做最小可跑版本。
- 保持改動小而清楚。
- 不要擴大 scope。
- 完成後列出修改檔案、測試方式、尚未完成項目。
"""


def build_context_md(idea: dict[str, Any], draft: dict[str, Any]) -> str:
    return f"""# Context

## 題目
{idea.get('name')}

## 為什麼不是普通 SaaS
{idea.get('weird_angle') or '尚未填寫'}

## 使用者第一眼看到什麼
{idea.get('first_screen') or '尚未填寫'}

## 主要風險
{_bullets(draft['risks'])}

## 來源素材 ID
{', '.join(idea.get('source_signal_ids') or []) or '無'}
"""


def _infer_inputs(idea: dict[str, Any]) -> list[str]:
    blob = _blob(idea)
    if _has(blob, ["repo", "github", "readme"]):
        return ["GitHub repo URL", "可選：指定分支或子目錄", "可選：使用者補充的 setup 線索"]
    if _has(blob, ["agent", "codex", "opencode", "diff"]):
        return ["任務描述", "agent 執行 log", "git diff", "測試輸出"]
    if _has(blob, ["ui", "網站", "畫面", "figma", "visual"]):
        return ["目標 URL 或截圖", "任務描述", "baseline 截圖或設計參考"]
    return ["題目素材", "使用者補充限制", "預期輸出格式"]


def _infer_outputs(idea: dict[str, Any]) -> list[str]:
    blob = _blob(idea)
    if _has(blob, ["repo", "github", "readme"]):
        return ["setup/build/test 狀態", "失敗步驟與錯誤摘要", "真正可用的執行 recipe", "Markdown 報告"]
    if _has(blob, ["agent", "codex", "opencode", "diff"]):
        return ["事故時間線", "第一個可疑改動", "風險摘要", "下一輪修正 prompt"]
    if _has(blob, ["ui", "網站", "畫面", "figma", "visual"]):
        return ["畫面問題清單", "前後差異摘要", "可重現步驟", "修正建議 prompt"]
    return ["題目卡", "MVP 草案", "任務清單", "驗收標準"]


def _infer_do_items(idea: dict[str, Any]) -> list[str]:
    blob = _blob(idea)
    if _has(blob, ["repo", "github", "readme"]):
        return ["支援公開 GitHub repo", "在隔離資料夾或容器中執行", "擷取 README / package metadata", "嘗試 setup/build/test", "產生 Markdown 報告"]
    if _has(blob, ["agent", "codex", "opencode"]):
        return ["讀取任務描述與 agent log", "整理 git diff", "標記可疑步驟", "產生事故報告", "產生下一輪修正 prompt"]
    return ["建立最小 CLI 或本地 UI", "保存輸入與輸出", "產生可讀報告", "支援 3～5 個手動測試案例"]


def _infer_dont_items(idea: dict[str, Any]) -> list[str]:
    return ["不做登入與多人協作", "不做大型 dashboard", "不自動處理所有邊界案例", "不把 scope 擴成平台", "不在主機上執行不可信程式碼"]


def _infer_tasks(idea: dict[str, Any]) -> list[str]:
    blob = _blob(idea)
    if _has(blob, ["repo", "github", "readme"]):
        return ["建立輸入 repo URL 的 CLI/API", "clone repo 到隔離工作區", "讀取 README 與常見設定檔", "推斷 install/build/test 指令", "執行指令並記錄 stdout/stderr", "產生 Markdown 報告", "用 3 個 repo 做 smoke test"]
    if _has(blob, ["agent", "codex", "opencode"]):
        return ["定義 agent run log 輸入格式", "解析 git diff 與測試輸出", "建立事故時間線", "標記第一個可疑行為", "產生事故報告", "產生下一輪修正 prompt"]
    return ["建立資料模型", "建立最小輸入表單", "建立核心處理函式", "建立 Markdown 報告輸出", "建立 3 個範例案例", "補 README 與啟動方式"]


def _infer_acceptance(idea: dict[str, Any]) -> list[str]:
    blob = _blob(idea)
    if _has(blob, ["repo", "github", "readme"]):
        return ["輸入 repo URL 後會產生一份報告", "報告包含 setup/build/test 三段狀態", "失敗時能指出失敗指令與錯誤摘要", "至少 3 個測試 repo 可完成流程", "所有外部執行都有 timeout"]
    return ["可以從空資料啟動", "可以建立一個範例題目", "可以輸出 Markdown 任務包", "README 含完整啟動步驟", "至少一條 happy path 通過"]


def _infer_risks(idea: dict[str, Any]) -> list[str]:
    blob = _blob(idea)
    risks = ["題目可能只是 prompt 包裝", "MVP scope 可能膨脹", "產出可能仍然太合理、缺少記憶點"]
    if _has(blob, ["repo", "github", "readme"]):
        risks.extend(["執行陌生 repo 有安全風險，必須 sandbox", "各語言生態差異大，第一版要限制範圍", "很多 repo 需要 API key 或外部服務"])
    if _has(blob, ["agent", "codex", "opencode"]):
        risks.extend(["不同 agent log 格式不一致", "事故歸因可能不準", "容易變成普通 log viewer"])
    return risks


def _blob(idea: dict[str, Any]) -> str:
    return "\n".join(str(idea.get(key) or "") for key in ["name", "one_liner", "weird_angle", "real_pain", "first_screen", "mvp"]).lower()


def _has(blob: str, words: list[str]) -> bool:
    return any(word.lower() in blob for word in words)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _checkboxes(items: list[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items)


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{index + 1}. {item}" for index, item in enumerate(items))
