from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class LLMMessage:
    role: str
    content: str | list[Any]
    tool_calls: list[Any] | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None

    def or_zero(self) -> tuple[int, int]:
        return self.input_tokens or 0, self.output_tokens or 0


@dataclass(frozen=True)
class LLMChatResult:
    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)


DeltaKind = Literal["text_delta", "thinking_delta", "tool_call", "done", "error"]


@dataclass
class LLMDelta:
    kind: DeltaKind
    text: str | None = None
    thinking: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_args_json: str | None = None
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    error_message: str | None = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
