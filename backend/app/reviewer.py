from __future__ import annotations

import re
from typing import Any

BORING_KEYWORDS: dict[str, list[str]] = {
    "too_saas": ["saas", "enterprise", "b2b", "subscription", "crm"],
    "dashboard_smell": ["dashboard", "console", "panel", "analytics", "insights", "報表", "儀表板", "控制台"],
    "platform_smell": ["platform", "marketplace", "ecosystem", "hub", "平台", "市集"],
    "workflow_smell": ["workflow", "automation", "pipeline", "orchestration", "流程", "自動化"],
    "generic_ai_tool": ["ai assistant", "copilot", "agent platform", "智能助手", "助理", "副駕"],
    "productivity_smell": ["productivity", "collaboration", "team", "效率", "協作", "團隊"],
}

WEIRD_MARKERS = [
    "測謊", "屍檢", "墳場", "盲盒", "怪物", "圖鑑", "偵探", "犯罪", "現場", "博物館",
    "復活", "煉金", "動物園", "實驗室", "標本", "吸血鬼", "招魂", "法醫", "審問",
]

VISUAL_MARKERS = [
    "畫面", "卡", "圖鑑", "現場", "實驗室", "博物館", "地圖", "時間線", "筆錄", "展櫃",
    "first screen", "timeline", "card", "map", "gallery",
]

ACTIONABLE_MARKERS = [
    "輸入", "輸出", "第一版", "mvp", "repo", "url", "container", "docker", "markdown", "report",
    "測試", "安裝", "build", "test", "setup", "產生", "支援",
]

SCORE_KEYS = {
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

RENAME_PATTERNS = [
    "{noun} 測謊機",
    "{noun} 屍檢室",
    "{noun} 怪物圖鑑",
    "{noun} 犯罪現場",
    "{noun} 盲盒",
    "{noun} 復活師",
    "{noun} 標本館",
    "{noun} 偵探局",
    "{noun} 墳場",
    "{noun} 煉金爐",
]

THEME_NOUNS = {
    "repo": ["README", "Repo", "開源工具", "安裝事故", "API Key", "Dockerfile", "依賴"],
    "agent": ["Agent", "Codex", "工具呼叫", "AI 事故", "Prompt", "Diff"],
    "visual": ["UI", "畫面", "設計", "網站", "遊戲", "截圖"],
    "generic": ["專題", "點子", "產品", "靈感", "怪題"],
}


def _text_blob(idea: dict[str, Any]) -> str:
    parts = [
        idea.get("name", ""),
        idea.get("one_liner", ""),
        idea.get("weird_angle", ""),
        idea.get("real_pain", ""),
        idea.get("first_screen", ""),
        idea.get("mvp", ""),
    ]
    return "\n".join(str(part or "") for part in parts).lower()


def detect_boring_flags(idea: dict[str, Any]) -> list[str]:
    blob = _text_blob(idea)
    flags: list[str] = []
    for flag, keywords in BORING_KEYWORDS.items():
        if any(keyword.lower() in blob for keyword in keywords):
            flags.append(flag)
    name = str(idea.get("name", ""))
    if len(name) > 28 and not any(marker in name for marker in WEIRD_MARKERS):
        flags.append("name_too_plain")
    if not str(idea.get("weird_angle", "")).strip():
        flags.append("missing_weird_angle")
    if not str(idea.get("real_pain", "")).strip():
        flags.append("missing_real_pain")
    if not str(idea.get("mvp", "")).strip():
        flags.append("missing_mvp")
    return sorted(set(flags))


def detect_theme(idea: dict[str, Any]) -> str:
    blob = _text_blob(idea)
    if any(word in blob for word in ["repo", "github", "readme", "build", "setup", "docker", "container", "依賴"]):
        return "repo"
    if any(word in blob for word in ["agent", "codex", "opencode", "claude", "tool call", "mcp", "diff"]):
        return "agent"
    if any(word in blob for word in ["ui", "visual", "figma", "website", "frontend", "game", "design", "畫面", "設計"]):
        return "visual"
    return "generic"


def _contains_any(text: str, markers: list[str]) -> bool:
    return any(marker.lower() in text.lower() for marker in markers)


def score_idea(idea: dict[str, Any]) -> dict[str, int]:
    original = idea.get("scores") or {}
    scores: dict[str, int] = {key: int(original.get(key, 6) or 6) for key in SCORE_KEYS}

    name = str(idea.get("name", ""))
    one_liner = str(idea.get("one_liner", ""))
    weird_angle = str(idea.get("weird_angle", ""))
    real_pain = str(idea.get("real_pain", ""))
    first_screen = str(idea.get("first_screen", ""))
    mvp = str(idea.get("mvp", ""))
    blob = _text_blob(idea)
    flags = detect_boring_flags(idea)

    if _contains_any(name + weird_angle, WEIRD_MARKERS):
        scores["weirdness"] += 2
        scores["surprise"] += 1
        scores["memorability"] += 2
    if _contains_any(first_screen + name, VISUAL_MARKERS):
        scores["visual_imagination"] += 2
    if len(name) <= 14 and _contains_any(name, WEIRD_MARKERS):
        scores["memorability"] += 1
    if len(real_pain) > 30:
        scores["real_pain"] += 2
    if _contains_any(mvp, ACTIONABLE_MARKERS):
        scores["mvp_feasibility"] += 2
    if any(word in blob for word in ["codex", "opencode", "github", "repo", "mcp", "visual", "agent"]):
        scores["personal_fit"] += 1
    if not flags:
        scores["anti_saas"] += 2
        scores["differentiation"] += 1
    else:
        penalty = min(4, len(flags))
        scores["anti_saas"] -= penalty
        scores["surprise"] -= min(2, penalty)
        scores["differentiation"] -= min(2, penalty)
    if str(idea.get("status", "")) in {"dead", "rejected", "revive_candidate"}:
        scores["revival_potential"] += 1

    return {key: max(1, min(10, value)) for key, value in scores.items()}


def make_suggestions(idea: dict[str, Any], flags: list[str] | None = None) -> list[str]:
    flags = flags or detect_boring_flags(idea)
    theme = detect_theme(idea)
    nouns = THEME_NOUNS.get(theme, THEME_NOUNS["generic"])
    suggestions: list[str] = []
    for noun in nouns:
        for pattern in RENAME_PATTERNS[:4]:
            suggestions.append(pattern.format(noun=noun))
            if len(suggestions) >= 10:
                break
        if len(suggestions) >= 10:
            break

    # Add targeted rewrites based on common boring flags.
    if "dashboard_smell" in flags:
        suggestions.insert(0, f"{nouns[0]} 犯罪現場")
    if "platform_smell" in flags or "workflow_smell" in flags:
        suggestions.insert(0, f"{nouns[0]} 煉金爐")
    if "generic_ai_tool" in flags:
        suggestions.insert(0, f"{nouns[0]} 反助手")

    unique: list[str] = []
    for item in suggestions:
        if item not in unique:
            unique.append(item)
    return unique[:10]


def review_idea(idea: dict[str, Any]) -> dict[str, Any]:
    flags = detect_boring_flags(idea)
    scores = score_idea(idea)
    passes = scores["anti_saas"] >= 6 and scores["weirdness"] >= 6 and scores["memorability"] >= 6 and len(flags) <= 2

    if passes:
        comment = "通過。這個題目有明確怪味或畫面感，沒有太重的普通 SaaS 味，且能看出第一版方向。"
    else:
        reasons = "、".join(flags) if flags else "怪味與記憶點不足"
        comment = f"未通過。主要問題：{reasons}。建議先改名、補強第一個畫面，避免 dashboard / platform / workflow 味。"

    return {
        "review_type": "anti_rational",
        "passes": passes,
        "flags": flags,
        "comment": comment,
        "suggestions": make_suggestions(idea, flags),
        "scores": scores,
    }


def commercial_smell_report(idea: dict[str, Any]) -> dict[str, Any]:
    flags = detect_boring_flags(idea)
    labels = {
        "too_saas": "太像 SaaS",
        "dashboard_smell": "太像 dashboard / 控制台",
        "platform_smell": "太像 platform / marketplace",
        "workflow_smell": "太像 workflow / automation",
        "generic_ai_tool": "太像一般 AI assistant / copilot",
        "productivity_smell": "太像生產力 / 團隊協作工具",
        "name_too_plain": "名字太長或太普通",
        "missing_weird_angle": "缺少怪在哪裡",
        "missing_real_pain": "缺少真痛點",
        "missing_mvp": "缺少 MVP",
    }
    return {
        "flags": flags,
        "labels": [labels.get(flag, flag) for flag in flags],
        "severity": min(10, len(flags) * 2),
    }
