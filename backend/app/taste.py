from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from . import crud
from .schemas import TasteFeedbackCreate

POSITIVE_STATUSES = {"saved", "deep_dive", "mvp_draft", "prototype_ready", "prototype", "revive_candidate"}
NEGATIVE_STATUSES = {"rejected", "dead", "merged"}
ACTION_WEIGHTS = {
    "like": 3,
    "love": 5,
    "save": 3,
    "prototype": 6,
    "deep_dive": 4,
    "dislike": -3,
    "reject": -4,
    "too_boring": -5,
    "too_saas": -5,
    "not_for_me": -3,
}
SCORE_KEYS = [
    "surprise",
    "weirdness",
    "memorability",
    "visual_imagination",
    "real_pain",
    "mvp_feasibility",
    "differentiation",
    "personal_fit",
    "anti_saas",
    "revival_potential",
]

POSITIVE_WORDS = ["測謊", "屍檢", "怪物", "盲盒", "犯罪", "事故", "復活", "偵探", "博物館", "考古", "動物園", "repo", "README", "agent", "開源", "實驗", "失敗"]
BORING_WORDS = ["dashboard", "platform", "workflow", "SaaS", "marketplace", "assistant", "copilot", "productivity", "automation", "collaboration", "enterprise"]


def _tokens(text: str) -> list[str]:
    cleaned = text.replace("/", " ").replace("-", " ").replace("_", " ").replace("，", " ").replace("。", " ")
    return [token.strip().lower() for token in cleaned.split() if len(token.strip()) >= 2]


def _idea_text(idea: dict[str, Any]) -> str:
    return "\n".join([
        idea.get("name", ""),
        idea.get("one_liner", ""),
        idea.get("weird_angle", ""),
        idea.get("real_pain", ""),
        idea.get("first_screen", ""),
        idea.get("mvp", ""),
    ])


def _implicit_weight(idea: dict[str, Any]) -> int:
    status = idea.get("status")
    if status == "prototype":
        return 6
    if status == "prototype_ready":
        return 5
    if status == "mvp_draft":
        return 4
    if status == "deep_dive":
        return 3
    if status == "saved":
        return 2
    if status == "revive_candidate":
        return 2
    if status in NEGATIVE_STATUSES:
        return -3
    return 0


def _explicit_feedback_by_idea() -> dict[str, int]:
    result: dict[str, int] = defaultdict(int)
    for item in crud.list_taste_feedback():
        result[item["idea_id"]] += int(item.get("weight") or ACTION_WEIGHTS.get(item.get("action", ""), 0))
    return result


def build_taste_profile() -> dict[str, Any]:
    ideas = crud.list_ideas()
    feedback_weights = _explicit_feedback_by_idea()
    liked: list[dict[str, Any]] = []
    disliked: list[dict[str, Any]] = []
    keyword_scores: Counter[str] = Counter()
    score_totals: dict[str, list[float]] = defaultdict(list)
    boring_hits: Counter[str] = Counter()

    for idea in ideas:
        weight = _implicit_weight(idea) + feedback_weights.get(idea["id"], 0)
        text = _idea_text(idea)
        if weight > 0:
            liked.append(idea)
        elif weight < 0:
            disliked.append(idea)
        for token in _tokens(text):
            keyword_scores[token] += weight
        for word in POSITIVE_WORDS:
            if word.lower() in text.lower():
                keyword_scores[word.lower()] += max(weight, 1 if weight >= 0 else weight)
        for word in BORING_WORDS:
            if word.lower() in text.lower():
                boring_hits[word] += 1
                keyword_scores[word.lower()] -= 2
        for key, value in (idea.get("scores") or {}).items():
            if key in SCORE_KEYS and weight > 0:
                try:
                    score_totals[key].append(float(value))
                except Exception:
                    pass

    preferred_keywords = [kw for kw, score in keyword_scores.most_common(20) if score > 0]
    disliked_keywords = [kw for kw, score in keyword_scores.most_common()[:-21:-1] if score < 0]
    average_positive_scores = {
        key: round(sum(values) / len(values), 1)
        for key, values in score_totals.items()
        if values
    }
    profile = {
        "summary": make_profile_summary(liked, disliked, preferred_keywords, disliked_keywords),
        "liked_count": len(liked),
        "disliked_count": len(disliked),
        "preferred_keywords": preferred_keywords,
        "disliked_keywords": disliked_keywords,
        "boring_words_seen": dict(boring_hits.most_common(12)),
        "average_positive_scores": average_positive_scores,
        "recommendation_rule": "偏好：怪味、記憶點、開源/agent/repo/失敗分析；扣分：dashboard/SaaS/platform/workflow 味太重。",
    }
    return profile


def make_profile_summary(liked: list[dict[str, Any]], disliked: list[dict[str, Any]], preferred: list[str], disliked_words: list[str]) -> str:
    if not liked and not disliked:
        return "還沒有足夠行為資料。先收藏、淘汰、深挖或回饋幾張題目，系統會開始學你的品味。"
    bits = []
    if preferred:
        bits.append("目前偏好的味道包含：" + "、".join(preferred[:8]))
    if disliked_words:
        bits.append("目前容易扣分的味道包含：" + "、".join(disliked_words[:6]))
    bits.append(f"已從 {len(liked)} 個正向題目與 {len(disliked)} 個負向題目推估。")
    return " ".join(bits)


def score_taste_fit(idea: dict[str, Any]) -> dict[str, Any]:
    profile = build_taste_profile()
    text = _idea_text(idea).lower()
    scores = idea.get("scores") or {}
    score = 50
    reasons: list[str] = []
    warnings: list[str] = []

    for kw in profile.get("preferred_keywords", [])[:16]:
        if kw.lower() in text:
            score += 4
            reasons.append(f"命中偏好關鍵字：{kw}")
    for kw in profile.get("disliked_keywords", [])[:12]:
        if kw.lower() in text:
            score -= 5
            warnings.append(f"命中負向關鍵字：{kw}")
    for word in BORING_WORDS:
        if word.lower() in text:
            score -= 5
            warnings.append(f"有普通商業工具味：{word}")
    for key in ["weirdness", "memorability", "surprise", "anti_saas", "personal_fit"]:
        try:
            value = float(scores.get(key, 0))
        except Exception:
            value = 0
        if value >= 8:
            score += 3
            reasons.append(f"{key} 分數高：{value:g}")
        elif 0 < value <= 4:
            score -= 2
            warnings.append(f"{key} 分數偏低：{value:g}")

    # Cold start defaults: reward the product's intended weird builder taste.
    if profile.get("liked_count", 0) == 0 and profile.get("disliked_count", 0) == 0:
        for word in POSITIVE_WORDS:
            if word.lower() in text:
                score += 3
                reasons.append(f"冷啟動偏好命中：{word}")

    score = max(0, min(100, score))
    if score >= 78:
        verdict = "很符合你的怪題品味，建議深挖或收斂 MVP。"
    elif score >= 60:
        verdict = "有一定適配度，建議先補真痛點或改名。"
    elif score >= 40:
        verdict = "普通，可能需要更怪的角度。"
    else:
        verdict = "不太符合目前品味，建議淘汰或大幅改寫。"
    return {
        "idea_id": idea["id"],
        "score": score,
        "verdict": verdict,
        "reasons": reasons[:8],
        "warnings": warnings[:8],
        "profile_summary": profile.get("summary", ""),
    }


def recommendations(limit: int = 10) -> list[dict[str, Any]]:
    ranked = []
    for idea in crud.list_ideas():
        if idea.get("status") in {"dead", "rejected", "merged"}:
            continue
        fit = score_taste_fit(idea)
        ranked.append({"idea": idea, "fit": fit})
    ranked.sort(key=lambda item: item["fit"]["score"], reverse=True)
    return ranked[:limit]


def create_feedback(payload: TasteFeedbackCreate) -> dict[str, Any]:
    weight = payload.weight
    if weight == 0:
        weight = ACTION_WEIGHTS.get(payload.action, 0)
    return crud.create_taste_feedback(payload, weight)
