from __future__ import annotations

import uuid

from core.llm.factory import get_llm_client
from core.llm.types import LLMMessage
from db.services.task_service import set_title_if_untitled
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestration.constants import TITLE_FORCE_BY_TURN
from agents.orchestration.title_normalize import normalize_task_title
from agents.registry.loader import load_prompt_file
from agents.usage.accumulator import UsageAccumulator
from agents.usage.recorder import record_turn_usage


async def generate_title(
    db: AsyncSession,
    task_id: uuid.UUID,
    conversation_so_far: str,
    turn_number: int,
    *,
    user_id: uuid.UUID | None = None,
    turn_id: uuid.UUID | None = None,
    turn_usage: UsageAccumulator | None = None,
    emit: object | None = None,
) -> str | None:
    """Generate a short task title. Returns None if not yet determinable."""
    force = turn_number >= TITLE_FORCE_BY_TURN
    template = load_prompt_file("system", "task-title.md")
    prompt = (
        f"{template}\n\nforce={str(force).lower()}\n\nConversation:\n{conversation_so_far[:800]}"
    )
    try:
        client = get_llm_client()
        result = await client.chat(
            [LLMMessage(role="user", content=prompt)],
            max_tokens=32,
            temperature=0.3,
        )
        in_t, out_t = result.usage.or_zero()
        if user_id and turn_id and turn_usage is not None and (in_t or out_t):
            await record_turn_usage(
                db,
                user_id=user_id,
                task_id=task_id,
                turn_id=turn_id,
                source="title",
                input_tokens=in_t,
                output_tokens=out_t,
                turn_usage=turn_usage,
                emit=emit,  # type: ignore[arg-type]
            )
        title = normalize_task_title(result.content)
        if not title:
            return None
        return title
    except Exception:
        return None


async def try_set_title(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_message: str,
    turn_number: int,
    *,
    user_id: uuid.UUID | None = None,
    turn_id: uuid.UUID | None = None,
    turn_usage: UsageAccumulator | None = None,
    emit: object | None = None,
) -> str | None:
    title = await generate_title(
        db,
        task_id,
        user_message,
        turn_number,
        user_id=user_id,
        turn_id=turn_id,
        turn_usage=turn_usage,
        emit=emit,
    )
    if title:
        await set_title_if_untitled(db, task_id, title)
    return title
