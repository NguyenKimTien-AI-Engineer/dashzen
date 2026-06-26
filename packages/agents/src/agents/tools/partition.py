from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.tools.registry import is_concurrent_safe


@dataclass
class ToolCall:
    call_id: str
    name: str
    args: dict[str, Any]


def partition_batches(calls: list[ToolCall]) -> list[list[ToolCall]]:
    """Group tool calls into concurrent-safe batches and serial batches."""
    batches: list[list[ToolCall]] = []
    for call in calls:
        safe = is_concurrent_safe(call.name)
        if batches and safe and is_concurrent_safe(batches[-1][0].name):
            batches[-1].append(call)
        else:
            batches.append([call])
    return batches
