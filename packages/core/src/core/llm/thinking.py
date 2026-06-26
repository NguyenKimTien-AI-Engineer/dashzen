from __future__ import annotations

import json
import uuid
from typing import Literal

from core.llm.types import LLMDelta

OllamaThinkParam = bool | str
OllamaThinkLevel = Literal["low", "medium", "high", "max"]
_GPT_OSS_LEVELS = frozenset({"low", "medium", "high"})
_THINK_LEVELS = _GPT_OSS_LEVELS | frozenset({"max"})


def resolve_thinking_enabled(
    request_value: bool | None,
    *,
    provider: str,
    ollama_thinking_enabled: bool,
) -> bool:
    """Resolve effective thinking flag: explicit client value wins, else provider default."""
    if request_value is not None:
        return request_value
    if provider == "ollama":
        return ollama_thinking_enabled
    return False


def resolve_ollama_think_param(
    *,
    enabled: bool,
    level: str,
    model: str,
) -> OllamaThinkParam | None:
    """Map DashZen thinking flag to Ollama ``think`` payload value.

    Returns ``None`` when the field should be omitted (Ollama legacy behavior).
    """
    if not enabled:
        return None

    normalized_level = level.strip().lower()
    model_lower = model.lower()

    if "gpt-oss" in model_lower:
        if normalized_level in _GPT_OSS_LEVELS:
            return normalized_level
        return "medium"

    if normalized_level in _THINK_LEVELS:
        return normalized_level

    return True


def is_ollama_think_rejection(exc: Exception) -> bool:
    """True when an HTTP error likely means the model rejected the ``think`` field."""
    import httpx

    if not isinstance(exc, httpx.HTTPStatusError):
        return False
    if exc.response.status_code not in (400, 422):
        return False
    detail = exc.response.text.lower()
    if not detail:
        detail = str(exc).lower()
    return "think" in detail or "thinking" in detail


def deltas_from_ollama_message(msg: dict) -> list[LLMDelta]:  # type: ignore[type-arg]
    """Parse one Ollama stream chunk into provider-neutral deltas."""
    deltas: list[LLMDelta] = []

    thinking = msg.get("thinking", "")
    if thinking:
        deltas.append(LLMDelta(kind="thinking_delta", thinking=thinking))

    content = msg.get("content", "")
    if content:
        deltas.append(LLMDelta(kind="text_delta", text=content))

    for tc in msg.get("tool_calls", []):
        fn = tc.get("function", {})
        call_id = str(uuid.uuid4())
        args = fn.get("arguments", {})
        args_json = json.dumps(args) if isinstance(args, dict) else str(args)
        deltas.append(
            LLMDelta(
                kind="tool_call",
                tool_call_id=call_id,
                tool_name=fn.get("name"),
                tool_args_json=args_json,
            )
        )

    return deltas
