from __future__ import annotations

import json

from core.llm.budget import INITIAL_TOKENS_PER_CHAR
from core.llm.types import LLMMessage


def estimate_chars(messages: list[LLMMessage]) -> int:
    total = 0
    for msg in messages:
        content = msg.content
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            total += len(json.dumps(content))
        if msg.tool_calls:
            total += len(json.dumps(msg.tool_calls))
        if msg.tool_call_id:
            total += len(msg.tool_call_id)
    return total


def calibrate_tokens_per_char(real_prompt_tokens: int, messages: list[LLMMessage]) -> float:
    chars = estimate_chars(messages)
    if chars <= 0:
        return INITIAL_TOKENS_PER_CHAR
    return real_prompt_tokens / chars
