from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.llm_usage_event import LlmUsageEvent
from db.models.task import Task
from db.models.user import User

UsageSource = Literal["orchestrator", "sub_agent", "compaction", "title"]


@dataclass(frozen=True)
class UsageTotals:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


async def record_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    turn_id: uuid.UUID,
    source: UsageSource,
    input_tokens: int,
    output_tokens: int,
    message_id: uuid.UUID | None = None,
    agent_name: str | None = None,
    model: str | None = None,
) -> UsageTotals | None:
    if input_tokens == 0 and output_tokens == 0:
        return None

    event = LlmUsageEvent(
        user_id=user_id,
        task_id=task_id,
        turn_id=turn_id,
        message_id=message_id,
        source=source,
        agent_name=agent_name,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    db.add(event)

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            total_input_tokens=User.total_input_tokens + input_tokens,
            total_output_tokens=User.total_output_tokens + output_tokens,
        )
    )
    await db.execute(
        update(Task)
        .where(Task.id == task_id, Task.user_id == user_id)
        .values(
            total_input_tokens=Task.total_input_tokens + input_tokens,
            total_output_tokens=Task.total_output_tokens + output_tokens,
        )
    )
    await db.flush()
    return UsageTotals(input_tokens=input_tokens, output_tokens=output_tokens)


async def get_user_usage(db: AsyncSession, user_id: uuid.UUID) -> UsageTotals:
    result = await db.execute(
        select(User.total_input_tokens, User.total_output_tokens).where(User.id == user_id)
    )
    row = result.one_or_none()
    if row is None:
        return UsageTotals(0, 0)
    return UsageTotals(input_tokens=int(row[0]), output_tokens=int(row[1]))


async def get_task_usage(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> UsageTotals:
    result = await db.execute(
        select(Task.total_input_tokens, Task.total_output_tokens).where(
            Task.id == task_id, Task.user_id == user_id
        )
    )
    row = result.one_or_none()
    if row is None:
        return UsageTotals(0, 0)
    return UsageTotals(input_tokens=int(row[0]), output_tokens=int(row[1]))


async def sum_turn_usage(db: AsyncSession, turn_id: uuid.UUID) -> UsageTotals:
    result = await db.execute(
        select(
            func.coalesce(func.sum(LlmUsageEvent.input_tokens), 0),
            func.coalesce(func.sum(LlmUsageEvent.output_tokens), 0),
        ).where(LlmUsageEvent.turn_id == turn_id)
    )
    row = result.one()
    return UsageTotals(input_tokens=int(row[0]), output_tokens=int(row[1]))
