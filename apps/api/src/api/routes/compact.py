from __future__ import annotations

import uuid

from agents.context.compaction import manual_compact
from db.models.user import User
from db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_task
from api.schemas.gates import CompactResponse

router = APIRouter(prefix="/v1/tasks", tags=["compact"])


@router.post("/{task_id}/compact", response_model=CompactResponse)
async def compact_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompactResponse:
    await require_task(task_id, user, db)
    summary, removed = await manual_compact(db, task_id)
    return CompactResponse(summary=summary, messages_removed=removed)
