from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.artifacts.buffer import ArtifactBuffer


@dataclass
class RuntimeContext:
    task_id: uuid.UUID
    user_id: uuid.UUID
    db: AsyncSession
    artifact_buffer: ArtifactBuffer
    mode: str  # "auto"
    thinking_enabled: bool
    user_instructions: str
    abort_signal: asyncio.Event
    emit: Callable[[Any], None]


async def run_task(
    ctx: RuntimeContext,
    user_message: str,
    parent_id: uuid.UUID | None,
) -> None:
    """Entry point for starting an agent run. Calls main_loop."""
    from agents.orchestration.main_loop import main_loop

    await main_loop(ctx, user_message, parent_id)
