import json
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.message import Message


def _branch_info_for(
    msg: Message,
    siblings_by_parent: dict[uuid.UUID | None, list[Message]],
) -> dict[str, int] | None:
    siblings = siblings_by_parent.get(msg.parent_id, [])
    if len(siblings) <= 1:
        return None
    ordered = sorted(siblings, key=lambda m: m.created_at)
    index = next(i for i, s in enumerate(ordered) if s.id == msg.id)
    return {"sibling_count": len(ordered), "sibling_index": index}


def _activity_log_from_thinking(thinking: str | None) -> dict[str, Any] | None:
    if not thinking:
        return None
    try:
        parsed = json.loads(thinking)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(parsed, dict) and parsed.get("type") == "activity_log":
        return parsed
    return None


def _enrich_message(
    msg: Message,
    siblings_by_parent: dict[uuid.UUID | None, list[Message]],
) -> dict[str, Any]:
    activity_log = _activity_log_from_thinking(msg.thinking)
    data: dict[str, Any] = {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "parent_id": msg.parent_id,
        "prompt_tokens": msg.prompt_tokens,
        "created_at": msg.created_at,
        "branch_info": _branch_info_for(msg, siblings_by_parent),
    }
    if activity_log is not None:
        data["activity_log"] = activity_log
    return data


async def create_message(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    role: str,
    content: str,
    parent_id: uuid.UUID | None = None,
    prompt_tokens: int | None = None,
    thinking: str | None = None,
) -> Message:
    msg = Message(
        task_id=task_id,
        role=role,
        content=content,
        parent_id=parent_id,
        prompt_tokens=prompt_tokens,
        thinking=thinking,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, task_id: uuid.UUID) -> Sequence[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.task_id == task_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()


async def update_message_thinking(
    db: AsyncSession,
    message_id: uuid.UUID,
    thinking: str,
) -> None:
    from sqlalchemy import update

    from db.models.message import Message

    await db.execute(
        update(Message).where(Message.id == message_id).values(thinking=thinking)
    )
    await db.flush()


async def get_messages_enriched(
    db: AsyncSession,
    task_id: uuid.UUID,
    *,
    leaf_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(Message).where(Message.task_id == task_id)
    )
    all_msgs = list(result.scalars().all())
    if not all_msgs:
        return []

    siblings_by_parent: dict[uuid.UUID | None, list[Message]] = {}
    for m in all_msgs:
        siblings_by_parent.setdefault(m.parent_id, []).append(m)

    if leaf_id is not None:
        path = await get_tree_path(db, task_id, leaf_id)
        return [_enrich_message(m, siblings_by_parent) for m in path]

    ordered = sorted(all_msgs, key=lambda m: m.created_at)
    return [_enrich_message(m, siblings_by_parent) for m in ordered]


async def get_tree_path(
    db: AsyncSession, task_id: uuid.UUID, leaf_id: uuid.UUID
) -> list[Message]:
    result = await db.execute(
        select(Message).where(Message.task_id == task_id)
    )
    all_msgs = {m.id: m for m in result.scalars().all()}
    path: list[Message] = []
    current_id: uuid.UUID | None = leaf_id
    while current_id is not None:
        msg = all_msgs.get(current_id)
        if msg is None:
            break
        path.append(msg)
        current_id = msg.parent_id
    path.reverse()
    return path


async def find_orphan_user_message(
    db: AsyncSession, task_id: uuid.UUID
) -> Message | None:
    result = await db.execute(
        select(Message)
        .where(Message.task_id == task_id, Message.role == "user")
        .order_by(Message.created_at.desc())
    )
    msgs = result.scalars().all()
    if not msgs:
        return None
    latest_user = msgs[0]
    resp = await db.execute(
        select(Message).where(
            Message.parent_id == latest_user.id,
            Message.role == "assistant",
        )
    )
    if resp.scalar_one_or_none() is None:
        return latest_user
    return None
