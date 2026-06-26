from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ToolContext:
    task_id: uuid.UUID
    user_id: uuid.UUID
    db: AsyncSession
    artifact_buffer: Any  # ArtifactBuffer — avoid circular import
    read_cache: Any  # ReadCache
    emit: Callable[[Any], None]  # emit SSE event
    mode: str = "auto"
    thinking_enabled: bool = False
    abort_signal: asyncio.Event | None = None
    agent_name: str | None = None
    current_call_id: str | None = None
    current_message_id: uuid.UUID | None = None
    # Orchestrator turn guards (one user message / main_loop run)
    orchestrator_list_file_calls: int = 0
    orchestrator_spawn_attempted: set[str] = field(default_factory=set)
    # Sub-agent: one write_file per output path per spawn
    agent_written_paths: set[str] = field(default_factory=set)
