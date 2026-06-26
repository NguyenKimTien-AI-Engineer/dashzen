from __future__ import annotations

import json
from collections.abc import Sequence

from core.llm.types import LLMMessage
from db.models.message import Message

from agents.context.thinking_codec import decode_thinking

_TOOL_PLACEHOLDER = "[Tool result truncated]"


def build_compact_summary_message(summary: str) -> LLMMessage:
    return LLMMessage(
        role="user",
        content=(
            "The following is a compressed summary of earlier conversation. "
            "Use it for context; recent messages follow.\n\n"
            f"{summary}"
        ),
    )


def _parse_assistant_content(content: str) -> tuple[str, list[dict] | None]:  # type: ignore[type-arg]
    stripped = content.rstrip()
    if not stripped.startswith("[") and "[" in stripped:
        idx = stripped.rfind("\n[")
        if idx == -1:
            idx = stripped.rfind("[")
        candidate = stripped[idx:].lstrip()
        if candidate.startswith("["):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                    if "id" in parsed[0] and "name" in parsed[0]:
                        text = stripped[:idx].rstrip() if idx > 0 else ""
                        return text, parsed
            except json.JSONDecodeError:
                pass
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                if "id" in parsed[0] and "name" in parsed[0]:
                    return "", parsed
        except json.JSONDecodeError:
            pass
    return content, None


def _thinking_content(thinking_json: str | None) -> str | list:  # type: ignore[type-arg]
    decoded = decode_thinking(thinking_json)
    if decoded is None:
        return ""
    if isinstance(decoded, list):
        return decoded
    if isinstance(decoded, dict):
        if decoded.get("type") == "activity_log":
            return ""
        return decoded.get("blocks", decoded)
    return ""


def build_history(db_messages: Sequence[Message]) -> list[LLMMessage]:
    compact_summary: str | None = None
    result: list[LLMMessage] = []

    for msg in db_messages:
        if msg.role == "compact":
            compact_summary = msg.content
            continue
        if msg.role == "user":
            result.append(LLMMessage(role="user", content=msg.content))
        elif msg.role == "assistant":
            text, tool_calls = _parse_assistant_content(msg.content)
            thinking = _thinking_content(msg.thinking)
            content: str | list = thinking if thinking else text  # type: ignore[assignment]
            if thinking and text:
                content = text
            result.append(
                LLMMessage(
                    role="assistant",
                    content=content,
                    tool_calls=tool_calls,
                )
            )
        elif msg.role == "tool":
            result.append(LLMMessage(role="tool", content=msg.content))

    _assign_tool_call_ids(result)

    if compact_summary:
        return [build_compact_summary_message(compact_summary), *result]
    return result


def _assign_tool_call_ids(messages: list[LLMMessage]) -> None:
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.role == "assistant" and msg.tool_calls:
            for j, tc in enumerate(msg.tool_calls):
                tool_idx = i + 1 + j
                if tool_idx < len(messages) and messages[tool_idx].role == "tool":
                    messages[tool_idx].tool_call_id = tc.get("id")
            i += 1 + len(msg.tool_calls)
        else:
            i += 1


def microcompact_tool_messages(messages: list[LLMMessage]) -> list[LLMMessage]:
    tool_indices = [i for i, m in enumerate(messages) if m.role == "tool"]
    if len(tool_indices) < 2:
        return messages
    half = len(tool_indices) // 2
    old_indices = set(tool_indices[:half])
    compacted: list[LLMMessage] = []
    for i, msg in enumerate(messages):
        if i in old_indices and isinstance(msg.content, str) and msg.content != _TOOL_PLACEHOLDER:
            compacted.append(
                LLMMessage(
                    role=msg.role,
                    content=_TOOL_PLACEHOLDER,
                    tool_call_id=msg.tool_call_id,
                )
            )
        else:
            compacted.append(msg)
    return compacted
