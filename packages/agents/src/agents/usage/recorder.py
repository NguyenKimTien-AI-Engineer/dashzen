from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from db.services.usage_service import UsageSource, record_usage
from sqlalchemy.ext.asyncio import AsyncSession

from agents.streaming.events import UsageUpdateEvent
from agents.usage.accumulator import UsageAccumulator


def get_llm_model_name() -> str | None:
    try:
        from core.config import get_settings

        settings = get_settings()
        provider = settings.llm_provider
        if provider == "anthropic":
            return settings.anthropic_model
        if provider == "openai":
            return settings.openai_model
        if provider == "gemini":
            return settings.gemini_model
        if provider == "openrouter":
            return settings.openrouter_model
        if provider == "vilao":
            return settings.vilao_model
        return settings.ollama_model
    except Exception:
        return None


async def record_turn_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    turn_id: uuid.UUID,
    source: UsageSource,
    input_tokens: int | None,
    output_tokens: int | None,
    turn_usage: UsageAccumulator,
    emit: Callable[[Any], None] | None = None,
    message_id: uuid.UUID | None = None,
    agent_name: str | None = None,
    model: str | None = None,
) -> None:
    in_t = input_tokens or 0
    out_t = output_tokens or 0
    if in_t == 0 and out_t == 0:
        return

    recorded = await record_usage(
        db,
        user_id=user_id,
        task_id=task_id,
        turn_id=turn_id,
        source=source,
        input_tokens=in_t,
        output_tokens=out_t,
        message_id=message_id,
        agent_name=agent_name,
        model=model or get_llm_model_name(),
    )
    if recorded is None:
        return

    turn_usage.add(recorded.input_tokens, recorded.output_tokens)
    if emit:
        emit(
            UsageUpdateEvent(
                turn_input_tokens=turn_usage.input_tokens,
                turn_output_tokens=turn_usage.output_tokens,
                delta_input=recorded.input_tokens,
                delta_output=recorded.output_tokens,
            )
        )
