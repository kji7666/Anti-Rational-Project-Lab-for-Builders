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


SYSTEM_PROMPT = """You are the local creative engine for Weird Lab / 怪題研究所.

Your job is to turn raw research material into weird-but-buildable local-first product ideas.

Avoid:
- generic SaaS dashboards
- generic AI assistants
- generic workflow automation
- bland summarizers
- generic productivity tools

Prefer:
- weird but buildable local tools
- developer tools
- repo autopsy
- failure museum
- graveyard / ritual / microscope / sandbox / weird console
- strong first-screen imagination
- small but vivid MVP shapes
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
    prompt = f"""Repair the following text into valid JSON only.
Do not include Markdown fences or commentary.

{text}
"""
    try:
        repaired = chat_completion(
            messages=[
                {"role": "system", "content": "You repair malformed JSON and reply with JSON only."},
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
            return f"Produced {len(output['cards'])} idea cards."
        if "ideas" in output and isinstance(output["ideas"], list):
            return f"Produced {len(output['ideas'])} candidate ideas."
        keys = list(output.keys())[:5]
        return "Keys: " + ", ".join(keys)
    if isinstance(output, list):
        return f"Produced {len(output)} items."
    return str(output)[:220]


def _normalize_card(card: dict[str, Any], source_signal_ids: list[str]) -> dict[str, Any]:
    name = str(card.get("title") or card.get("name") or "Untitled weird idea").strip()
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
        "generator_note": f"Local GPT 3-stage pipeline. {source_summary or 'No source summary provided.'}",
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
        "Material Brief",
        f"""Summarize the following material into JSON:
{{
  "summary": string,
  "tensions": string[],
  "strange_observations": string[],
  "developer_pains": string[],
  "broken_workflows": string[],
  "repeated_complaints": string[]
}}

Material:
{text}
""",
        temperature=0.2,
    )

    stage2 = _chat_json(
        "develop_ideas",
        "Develop Ideas",
        f"""Turn the material brief into Weird Lab idea skeletons and respond with JSON:
{{
  "ideas": [
    {{
      "title": string,
      "one_liner": string,
      "source_summary": string,
      "weird_angle": string,
      "target_user": string,
      "real_pain": string,
      "first_screen": string,
      "mvp_shape": string,
      "anti_saas_notes": string[],
      "risks": string[]
    }}
  ]
}}

Requirements:
- Keep the ideas weird but buildable.
- Avoid generic SaaS, dashboards, platforms, workflow automation, and generic AI assistants.
- Each idea must include weird_angle, target_user, real_pain, first_screen, and mvp_shape.
- anti_saas_notes should briefly explain why the idea does not collapse into generic SaaS.
- Propose exactly {count} ideas when possible.
- Each idea should feel distinct in angle, target user, or first-screen hook.

Material brief:
{json.dumps(stage1.output, ensure_ascii=False, indent=2)}
""",
        temperature=0.4,
    )

    stage3 = _chat_json(
        "emit_cards",
        "Emit Cards",
        f"""Convert the developed ideas into final card JSON:
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

Return exactly {count} cards when possible.

Material brief:
{json.dumps(stage1.output, ensure_ascii=False, indent=2)}

Developed ideas:
{json.dumps(stage2.output, ensure_ascii=False, indent=2)}
""",
        temperature=0.4,
    )

    cards = stage3.output.get("cards") if isinstance(stage3.output, dict) else None
    if not isinstance(cards, list) or not cards:
        raise LocalLLMPipelineError("Local GPT pipeline returned no idea cards.")

    ideas = [_normalize_card(card, source_signal_ids) for card in cards[:count] if isinstance(card, dict)]
    if not ideas:
        raise LocalLLMPipelineError("Local GPT pipeline returned cards in an unusable shape.")

    stages = [stage1, stage2, stage3]
    return {
        "ideas": ideas,
        "pipeline_stages": [item.as_dict() for item in stages],
    }
