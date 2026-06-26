from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.message import Message
from db.models.message_action import MessageAction


async def message_belongs_to_task(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    message_id: uuid.UUID,
) -> bool:
    result = await db.execute(
        select(Message.id).where(
            Message.id == message_id,
            Message.task_id == task_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def create_message_action(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    message_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    value: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> MessageAction:
    row = MessageAction(
        task_id=task_id,
        message_id=message_id,
        user_id=user_id,
        action=action,
        value=value,
        metadata_json=metadata_json,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def get_latest_feedback_by_message(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[uuid.UUID, str]:
    result = await db.execute(
        select(MessageAction)
        .where(
            MessageAction.task_id == task_id,
            MessageAction.user_id == user_id,
            MessageAction.action == "assistant_feedback",
        )
        .order_by(desc(MessageAction.created_at))
    )
    rows = result.scalars().all()
    latest: dict[uuid.UUID, str] = {}
    for row in rows:
        if row.message_id in latest:
            continue
        if row.value:
            latest[row.message_id] = row.value
    return latest
