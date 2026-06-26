from __future__ import annotations

import uuid

from core.llm.factory import get_llm_client
from core.llm.types import LLMMessage
from db.services.task_service import set_title_if_untitled
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestration.constants import TITLE_FORCE_BY_TURN
from agents.registry.loader import load_prompt_file


async def generate_title(
    db: AsyncSession,
    task_id: uuid.UUID,
    conversation_so_far: str,
    turn_number: int,
) -> str | None:
    """Generate a short task title. Returns None if not yet determinable."""
    force = turn_number >= TITLE_FORCE_BY_TURN
    template = load_prompt_file("system", "task-title.md")
    prompt = (
        f"{template}\n\nforce={str(force).lower()}\n\nConversation:\n{conversation_so_far[:800]}"
    )
    try:
        client = get_llm_client()
        response = await client.chat(
            [LLMMessage(role="user", content=prompt)],
            max_tokens=32,
            temperature=0.3,
        )
        title = response.strip().strip('"').strip("'")
        if not title or title.lower() == "null":
            return None
        return title[:255]
    except Exception:
        return None


async def try_set_title(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_message: str,
    turn_number: int,
) -> str | None:
    title = await generate_title(db, task_id, user_message, turn_number)
    if title:
        await set_title_if_untitled(db, task_id, title)
    return title
