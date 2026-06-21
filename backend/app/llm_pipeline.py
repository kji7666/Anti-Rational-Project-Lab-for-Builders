from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .llm_client import LocalLLMError, chat_completion
from .reviewer import score_idea


class LocalLLMPipelineError(RuntimeError):
    pass


@dataclass
class StageResult:
    stage: str
    title: str
    summary: str
    output: Any
    warning: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {"stage": self.stage, "title": self.title, "summary": self.summary}
        if self.warning:
            data["warning"] = self.warning
        return data


SYSTEM_PROMPT = """你是 Weird Lab / 怪題研究所 的本地創意引擎。

你的工作不是產生普通商業軟體點子，而是產生奇怪但可做、適合一週內做出 prototype 的 local-first 點子。

強烈避免：
- generic SaaS dashboard
- AI assistant for X
- platform for Y
- 只有 workflow automation 沒有視覺鉤子
- 普通 summarizer
- generic productivity tool
- 需要完整公司團隊才做得出的產品

強烈偏好：
- weird but buildable local tools
- visual debugging
- developer tools
- repo autopsy
- failure museum
- graveyard / ritual / microscope / sandbox / weird console
- 有記憶點的 first screen
- 一週 MVP 可完成
"""


def _chat_json(stage: str, title: str, prompt: str, *, temperature: float = 0.6) -> StageResult:
    try:
        raw = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
    except LocalLLMError as exc:
        raise LocalLLMPipelineError(str(exc)) from exc

    output = _parse_json_payload(raw)
    return StageResult(stage=stage, title=title, summary=_summarize_output(output), output=output)


def _parse_json_payload(text: str) -> Any:
    candidates = [text.strip()]

    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidates.extend(item.strip() for item in fenced if item.strip())

    start_positions = [index for index, char in enumerate(text) if char in "[{"]
    for start in start_positions:
        snippet = _extract_balanced_json(text[start:])
        if snippet:
            candidates.append(snippet)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    repaired = _repair_json_text(text)
    if repaired is not None:
        return repaired
    raise LocalLLMPipelineError("Local GPT returned malformed JSON that could not be repaired.")


def _extract_balanced_json(text: str) -> str | None:
    stack: list[str] = []
    in_string = False
    escape = False
    for index, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char in "[{":
            stack.append("]" if char == "[" else "}")
        elif char in "]}":
            if not stack or char != stack[-1]:
                return None
            stack.pop()
            if not stack:
                return text[: index + 1]
    return None


def _repair_json_text(text: str) -> Any | None:
    prompt = f"""請把下面內容修復成合法 JSON。

只輸出 JSON，不要解釋，不要加 Markdown。

內容：
{text}
"""
    try:
        repaired = chat_completion(
            messages=[
                {"role": "system", "content": "你是 JSON 修復器。只輸出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
    except LocalLLMError:
        return None

    for candidate in [repaired.strip(), _extract_balanced_json(repaired.strip())]:
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _summarize_output(output: Any) -> str:
    if isinstance(output, dict):
        if "summary" in output and isinstance(output["summary"], str):
            return output["summary"][:220]
        if "cards" in output and isinstance(output["cards"], list):
            return f"產出 {len(output['cards'])} 張怪題卡。"
        if "ideas" in output and isinstance(output["ideas"], list):
            return f"整理出 {len(output['ideas'])} 個候選方向。"
        keys = list(output.keys())[:5]
        return "輸出欄位：" + ", ".join(keys)
    if isinstance(output, list):
        return f"產出 {len(output)} 筆資料。"
    return str(output)[:220]


def _normalize_card(card: dict[str, Any], source_signal_ids: list[str]) -> dict[str, Any]:
    name = str(card.get("title") or card.get("name") or "未命名怪題").strip()
    one_liner = str(card.get("one_liner") or "").strip()
    weird_angle = str(card.get("weird_angle") or "").strip()
    real_pain = str(card.get("real_pain") or "").strip()
    first_screen = str(card.get("first_screen") or "").strip()
    mvp = str(card.get("mvp_shape") or card.get("mvp") or "").strip()
    source_summary = str(card.get("source_summary") or "").strip()
    target_user = str(card.get("target_user") or "").strip()
    anti_saas_notes = [str(item).strip() for item in card.get("anti_saas_notes", []) if str(item).strip()]
    risks = [str(item).strip() for item in card.get("risks", []) if str(item).strip()]
    scores = _normalize_scores(card.get("scores") or {})

    idea = {
        "name": name,
        "one_liner": one_liner,
        "weird_angle": weird_angle,
        "real_pain": real_pain,
        "first_screen": first_screen,
        "mvp": mvp,
        "status": "new",
        "source_signal_ids": source_signal_ids,
        "scores": scores,
        "generator_note": f"Local GPT multi-step pipeline：{source_summary or '已完成多階段怪題生成。'}",
        "source_summary": source_summary,
        "target_user": target_user,
        "anti_saas_notes": anti_saas_notes,
        "risks": risks,
    }
    if not any(scores.values()):
        idea["scores"] = score_idea(idea)
    else:
        rescored = score_idea(idea)
        merged_scores = {**rescored, **scores}
        idea["scores"] = _normalize_scores(merged_scores)
    return idea


def _normalize_scores(scores: dict[str, Any]) -> dict[str, int]:
    expected_keys = [
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
    normalized: dict[str, int] = {}
    for key in expected_keys:
        try:
            value = int(round(float(scores.get(key, 0) or 0)))
        except (TypeError, ValueError):
            value = 0
        normalized[key] = max(1, min(10, value)) if value else 0
    return normalized


def run_local_llm_pipeline(*, text: str, source_signal_ids: list[str] | None = None, count: int = 5) -> dict[str, Any]:
    source_signal_ids = source_signal_ids or []
    count = max(1, min(count, 10))

    stage1 = _chat_json(
        "extract_material_brief",
        "素材解剖",
        f"""請根據下列素材輸出 JSON 物件，欄位包含：
- summary
- tensions: string[]
- strange_observations: string[]
- developer_pains: string[]
- broken_workflows: string[]
- repeated_complaints: string[]

素材：
{text}
""",
        temperature=0.2,
    )

    stage2 = _chat_json(
        "diverge_weird_angles",
        "怪角度發散",
        f"""根據這份素材摘要輸出 JSON 物件，欄位：
- ideas: [{{
  "title": string,
  "one_liner": string,
  "weird_angle": string,
  "source_summary": string
}}]

請產出 {count + 2} 個候選方向。

素材摘要：
{json.dumps(stage1.output, ensure_ascii=False, indent=2)}
""",
    )

    stage3 = _chat_json(
        "anti_saas_critique",
        "反 SaaS 批判",
        f"""請批判下面候選怪題，輸出 JSON 物件：
- critiques: [{{
  "title": string,
  "boring_signals": string[],
  "survive": boolean,
  "keep_note": string
}}]

如果它像 dashboard / platform / workflow / generic AI assistant / productivity tool，就要毫不留情指出。

候選：
{json.dumps(stage2.output, ensure_ascii=False, indent=2)}
""",
        temperature=0.3,
    )

    stage4 = _chat_json(
        "amplify_weirdness",
        "怪感強化",
        f"""請保留值得存活的候選，輸出 JSON 物件：
- ideas: [{{
  "title": string,
  "one_liner": string,
  "weird_angle": string,
  "anti_saas_notes": string[]
}}]

請讓它更有 Weird Lab 氣質，但仍然一週內可做。

批判結果：
{json.dumps(stage3.output, ensure_ascii=False, indent=2)}
""",
    )

    stage5 = _chat_json(
        "reconstruct_real_pain",
        "痛點重建",
        f"""請把存活候選補成真實痛點，輸出 JSON 物件：
- ideas: [{{
  "title": string,
  "target_user": string,
  "real_pain": string,
  "moment_of_use": string
}}]

素材摘要：
{json.dumps(stage1.output, ensure_ascii=False, indent=2)}

存活候選：
{json.dumps(stage4.output, ensure_ascii=False, indent=2)}
""",
        temperature=0.4,
    )

    stage6 = _chat_json(
        "shape_mvp",
        "MVP 成形",
        f"""請為每個存活候選設計一週 MVP，輸出 JSON 物件：
- ideas: [{{
  "title": string,
  "first_screen": string,
  "mvp_shape": string,
  "risks": string[]
}}]

候選：
{json.dumps(stage4.output, ensure_ascii=False, indent=2)}

痛點：
{json.dumps(stage5.output, ensure_ascii=False, indent=2)}
""",
        temperature=0.4,
    )

    stage7 = _chat_json(
        "emit_cards",
        "輸出怪題卡",
        f"""請輸出最終 JSON 物件，格式：
{{
  "cards": [
    {{
      "title": string,
      "one_liner": string,
      "source_summary": string,
      "weird_angle": string,
      "real_pain": string,
      "target_user": string,
      "first_screen": string,
      "mvp_shape": string,
      "anti_saas_notes": string[],
      "risks": string[],
      "scores": {{
        "surprise": number,
        "weirdness": number,
        "memorability": number,
        "visual_imagination": number,
        "real_pain": number,
        "mvp_feasibility": number,
        "differentiation": number,
        "personal_fit": number,
        "anti_saas": number,
        "revival_potential": number
      }}
    }}
  ]
}}

只保留前 {count} 張卡。

素材摘要：
{json.dumps(stage1.output, ensure_ascii=False, indent=2)}

怪角度：
{json.dumps(stage4.output, ensure_ascii=False, indent=2)}

痛點：
{json.dumps(stage5.output, ensure_ascii=False, indent=2)}

MVP：
{json.dumps(stage6.output, ensure_ascii=False, indent=2)}
""",
        temperature=0.4,
    )

    cards = stage7.output.get("cards") if isinstance(stage7.output, dict) else None
    if not isinstance(cards, list) or not cards:
        raise LocalLLMPipelineError("Local GPT pipeline returned no idea cards.")

    ideas = [_normalize_card(card, source_signal_ids) for card in cards[:count] if isinstance(card, dict)]
    if not ideas:
        raise LocalLLMPipelineError("Local GPT pipeline returned cards in an unusable shape.")

    stages = [stage1, stage2, stage3, stage4, stage5, stage6, stage7]
    return {
        "ideas": ideas,
        "pipeline_stages": [item.as_dict() for item in stages],
    }
