from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8788/v1"
DEFAULT_MODEL = "chatgpt-web-local"
DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_API_KEY = "local-dev"


class LocalLLMError(RuntimeError):
    pass


@dataclass
class LocalLLMSettings:
    base_url: str
    model: str
    api_key: str | None
    timeout_seconds: float

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key)


def get_llm_settings() -> LocalLLMSettings:
    base_url = os.getenv("WEIRDLAB_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("WEIRDLAB_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    api_key = os.getenv("WEIRDLAB_LLM_API_KEY", DEFAULT_API_KEY).strip()
    timeout_raw = os.getenv("WEIRDLAB_LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()
    try:
        timeout_seconds = max(5.0, float(timeout_raw))
    except ValueError:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    return LocalLLMSettings(
        base_url=base_url,
        model=model,
        api_key=api_key or None,
        timeout_seconds=timeout_seconds,
    )


def _request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = get_llm_settings()
    url = f"{settings.base_url}{path}"
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(request, timeout=settings.timeout_seconds) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
            if response.status != 200:
                raise LocalLLMError(f"Local GPT returned HTTP {response.status}.")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LocalLLMError(f"Local GPT returned HTTP {exc.code}: {body[:240]}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise LocalLLMError(f"Could not reach Local GPT API: {reason}") from exc
    except TimeoutError as exc:
        raise LocalLLMError("Local GPT API request timed out.") from exc

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise LocalLLMError("Local GPT API returned invalid JSON.") from exc


def list_models() -> dict[str, Any]:
    return _request_json("GET", "/models")


def chat_completion(
    *,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    response_format: dict[str, Any] | None = None,
) -> str:
    settings = get_llm_settings()
    payload: dict[str, Any] = {
        "model": settings.model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if response_format:
        payload["response_format"] = response_format

    data = _request_json("POST", "/chat/completions", payload)
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LocalLLMError("Local GPT response did not include choices.")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise LocalLLMError("Local GPT response did not include message content.")
    return content.strip()


def check_local_llm() -> dict[str, Any]:
    settings = get_llm_settings()
    try:
        models = list_models()
        available = False
        for item in models.get("data", []):
            if isinstance(item, dict) and item.get("id") == settings.model:
                available = True
                break
        return {
            "base_url": settings.base_url,
            "model": settings.model,
            "timeout_seconds": settings.timeout_seconds,
            "api_key_configured": settings.api_key_configured,
            "available": available or bool(models.get("data")),
            "status": "ok" if (available or bool(models.get("data"))) else "degraded",
            "detail": "" if (available or bool(models.get("data"))) else "Local GPT endpoint responded, but the configured model was not listed.",
        }
    except LocalLLMError as exc:
        return {
            "base_url": settings.base_url,
            "model": settings.model,
            "timeout_seconds": settings.timeout_seconds,
            "api_key_configured": settings.api_key_configured,
            "available": False,
            "status": "offline",
            "detail": str(exc),
        }
