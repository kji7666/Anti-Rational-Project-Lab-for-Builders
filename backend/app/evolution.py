from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any

STOP_WORDS = {
    "ai", "agent", "tool", "tools", "platform", "dashboard", "system", "app", "the", "and", "for", "with",
    "一個", "工具", "系統", "平台", "自動", "幫你", "可以", "專案", "產品", "題目",
}

FAMILY_LABELS = [
    ("repo 可執行性驗證", {"repo", "github", "readme", "setup", "build", "test", "container", "docker", "安裝", "容器", "測謊", "屍檢", "復活"}),
    ("AI coding 事故分析", {"codex", "opencode", "claude", "agent", "失控", "事故", "犯罪", "現場", "diff", "run", "log"}),
    ("開源探索與盲盒", {"open", "source", "github", "trending", "blind", "box", "盲盒", "怪物", "圖鑑", "探索", "每日"}),
    ("視覺驗收與產品 QA", {"visual", "ui", "ux", "screenshot", "figma", "playwright", "畫面", "驗收", "視覺", "設計"}),
    ("MCP / 工具權限治理", {"mcp", "tool", "permission", "approval", "audit", "權限", "批准", "工具", "治理"}),
]


def tokenize_text(text: str) -> set[str]:
    text = (text or "").lower()
    ascii_tokens = re.findall(r"[a-z0-9_+#.-]{2,}", text)
    zh_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    tokens = set()
    for token in ascii_tokens + zh_tokens:
        cleaned = token.strip("._-#")
        if cleaned and cleaned not in STOP_WORDS:
            tokens.add(cleaned)
    # Add overlapping Chinese bigrams for short name matching.
    for block in zh_tokens:
        if len(block) >= 2:
            tokens.update(block[i : i + 2] for i in range(len(block) - 1))
    return tokens


def idea_text(idea: dict[str, Any]) -> str:
    parts = [
        idea.get("name", ""),
        idea.get("one_liner", ""),
        idea.get("weird_angle", ""),
        idea.get("real_pain", ""),
        idea.get("first_screen", ""),
        idea.get("mvp", ""),
        " ".join((idea.get("scores") or {}).keys()),
    ]
    return "\n".join(parts)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def similarity_score(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, list[str]]:
    tokens_a = tokenize_text(idea_text(a))
    tokens_b = tokenize_text(idea_text(b))
    overlap = sorted(tokens_a & tokens_b)
    base = jaccard(tokens_a, tokens_b)

    # Bonus if source signals overlap.
    sources_a = set(a.get("source_signal_ids") or [])
    sources_b = set(b.get("source_signal_ids") or [])
    source_bonus = 0.15 if sources_a and sources_a & sources_b else 0.0

    # Bonus for status lineage: dead/revive candidates can still belong to active clusters.
    score = min(1.0, base + source_bonus)
    reasons = []
    if overlap:
        reasons.append("共同關鍵詞：" + "、".join(overlap[:8]))
    if source_bonus:
        reasons.append("使用了相同來源素材")
    if not reasons:
        reasons.append("語意接近度較低，建議人工判斷")
    return round(score, 3), reasons


def similar_ideas(target: dict[str, Any], ideas: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for idea in ideas:
        if idea["id"] == target["id"]:
            continue
        score, reasons = similarity_score(target, idea)
        if score >= 0.08:
            items.append({"idea": idea, "score": score, "reasons": reasons})
    return sorted(items, key=lambda item: item["score"], reverse=True)[:limit]


def family_name_for(tokens: set[str]) -> str:
    best_label = "未命名題目族群"
    best_score = 0
    for label, keywords in FAMILY_LABELS:
        score = len(tokens & keywords)
        if score > best_score:
            best_label = label
            best_score = score
    if best_score == 0:
        top = [token for token, _ in Counter(tokens).most_common(3)]
        return " / ".join(top) if top else best_label
    return best_label


def build_family_suggestions(ideas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Greedy grouping by pairwise similarity.
    remaining = {idea["id"]: idea for idea in ideas}
    groups: list[list[dict[str, Any]]] = []

    for idea in ideas:
        if idea["id"] not in remaining:
            continue
        group = [idea]
        del remaining[idea["id"]]
        for other_id, other in list(remaining.items()):
            score, _ = similarity_score(idea, other)
            if score >= 0.14:
                group.append(other)
                del remaining[other_id]
        if len(group) >= 2:
            groups.append(group)

    suggestions: list[dict[str, Any]] = []
    for group in groups:
        all_tokens: list[str] = []
        for idea in group:
            all_tokens.extend(tokenize_text(idea_text(idea)))
        token_counts = Counter(all_tokens)
        shared_tokens = [token for token, count in token_counts.items() if count >= 2]
        label = family_name_for(set(all_tokens))
        suggestions.append(
            {
                "family_name": label,
                "idea_ids": [idea["id"] for idea in group],
                "ideas": group,
                "shared_keywords": shared_tokens[:12],
                "merge_options": merge_name_options(group, label),
                "reason": f"這 {len(group)} 張題目卡共享素材、語意或使用場景，適合檢查是否合併。",
            }
        )
    return suggestions


def merge_name_options(ideas: list[dict[str, Any]], family_label: str) -> list[dict[str, str]]:
    names = "、".join(idea.get("name", "") for idea in ideas[:4])
    options = [
        {"style": "功能型", "name": family_label, "description": "清楚描述題目族群，適合當內部分類。"},
        {"style": "怪味型", "name": "README 測謊局" if "repo" in family_label.lower() or "Repo" in names or "README" in names else "怪題變異室", "description": "有畫面感，適合作為產品名稱候選。"},
        {"style": "報告型", "name": "事故檔案室" if "事故" in family_label or "AI" in family_label else "題目屍檢室", "description": "偏分析報告與失敗解剖。"},
        {"style": "遊戲化", "name": "Open Source 怪物圖鑑" if "repo" in family_label.lower() or "開源" in family_label else "點子怪物圖鑑", "description": "偏每日探索與收藏體驗。"},
    ]
    return options


def revive_suggestions(ideas: list[dict[str, Any]], signals: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    active = [idea for idea in ideas if idea.get("status") not in {"dead", "rejected", "merged"}]
    dead = [idea for idea in ideas if idea.get("status") in {"dead", "rejected"}]
    recent_signal_text = "\n".join(
        f"{s.get('title','')} {s.get('summary','')} {s.get('raw_text','')} {' '.join(s.get('tags') or [])}" for s in signals[:20]
    )
    signal_tokens = tokenize_text(recent_signal_text)
    results: list[dict[str, Any]] = []
    for idea in dead:
        idea_tokens = tokenize_text(idea_text(idea))
        signal_overlap = sorted(idea_tokens & signal_tokens)
        best_active = None
        best_score = 0.0
        for other in active:
            score, _ = similarity_score(idea, other)
            if score > best_score:
                best_score = score
                best_active = other
        revival_score = min(10, int(round(best_score * 10)) + min(3, len(signal_overlap)))
        if revival_score >= 3 or idea.get("revival_condition"):
            reasons = []
            if signal_overlap:
                reasons.append("近期素材重新出現：" + "、".join(signal_overlap[:8]))
            if best_active:
                reasons.append(f"與目前題目「{best_active.get('name')}」接近")
            if idea.get("revival_condition"):
                reasons.append("原本有復活條件：" + idea.get("revival_condition"))
            results.append({"idea": idea, "score": revival_score, "reasons": reasons})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


def build_merged_idea_payload(ideas: list[dict[str, Any]], selected_name: str | None = None) -> dict[str, Any]:
    tokens = set()
    for idea in ideas:
        tokens |= tokenize_text(idea_text(idea))
    family = family_name_for(tokens)
    name = selected_name or merge_name_options(ideas, family)[0]["name"]
    source_ids: list[str] = []
    for idea in ideas:
        for signal_id in idea.get("source_signal_ids") or []:
            if signal_id not in source_ids:
                source_ids.append(signal_id)
    return {
        "name": name,
        "one_liner": " / ".join([idea.get("one_liner", "") for idea in ideas if idea.get("one_liner")][:2])[:220],
        "weird_angle": "這是由多個相近怪題合併出的題目族群，保留不同名字的怪味與同一個底層痛點。",
        "real_pain": "合併來源題目都指向同一類尚未被好好解決的痛點：" + "、".join([idea.get("name", "") for idea in ideas[:4]]),
        "first_screen": "左側顯示題目族譜，右側顯示不同產品風格：功能型、怪味型、報告型、遊戲化。",
        "mvp": "先把這組題目整理成一張母題卡，保留來源題目的死因、復活條件、MVP 草案與下一步實驗。",
        "status": "deep_dive",
        "source_signal_ids": source_ids,
        "scores": {"surprise": 7, "weirdness": 8, "memorability": 8, "real_pain": 7, "mvp_feasibility": 7, "differentiation": 7, "anti_saas": 8},
        "status_note": "Phase 6 自動合併產生。",
    }
