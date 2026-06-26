from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from core.llm.types import LLMDelta, LLMMessage, ToolDefinition


@runtime_checkable
class LLMClient(Protocol):
    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str: ...

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition],
        *,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        thinking_enabled: bool = False,
    ) -> AsyncGenerator[LLMDelta, None]: ...
