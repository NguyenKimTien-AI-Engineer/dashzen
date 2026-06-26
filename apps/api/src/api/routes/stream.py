from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from agents.streaming.events import StreamErrorEvent, serialize_sse
from agents.streaming.guards import get_or_create_abort_signal, is_duplicate_request
from agents.streaming.lock import StreamLockError
from agents.streaming.session import StreamSessionManager, iter_session_events
from core.config import get_settings
from core.llm.thinking import resolve_thinking_enabled
from db.models.user import User
from db.services.task_service import get_task
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.rate_limit_deps import enforce_task_stream_limit
from api.schemas.tasks import RunStatusResponse, StopResponse, StreamRequest

router = APIRouter(prefix="/v1/tasks", tags=["stream"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _sse_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
    return StreamingResponse(generator, media_type="text/event-stream", headers=_SSE_HEADERS)


@router.get("/{task_id}/run-status", response_model=RunStatusResponse)
async def run_status_endpoint(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunStatusResponse:
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    snapshot = StreamSessionManager.get_status(str(task_id))
    return RunStatusResponse(
        status=snapshot.status,
        event_count=snapshot.event_count,
        started_at=snapshot.started_at,
    )


@router.get("/{task_id}/stream")
async def subscribe_stream_endpoint(
    task_id: uuid.UUID,
    cursor: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    session = StreamSessionManager.get_active_session(str(task_id))
    if session is None:
        return _sse_response(_idle_stream())

    return _sse_response(StreamSessionManager.subscribe(str(task_id), cursor=cursor))


async def _idle_stream() -> AsyncGenerator[str, None]:
    yield serialize_sse(StreamErrorEvent(message="No active stream to resume."))


@router.post("/{task_id}/stream")
async def stream_endpoint(
    task_id: uuid.UUID,
    body: StreamRequest,
    user: User = Depends(enforce_task_stream_limit),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task_key = str(task_id)

    if body.resume:
        session = StreamSessionManager.get_active_session(task_key)
        if session is None:
            return _sse_response(_idle_stream())
        return _sse_response(
            StreamSessionManager.subscribe(task_key, cursor=body.cursor),
        )

    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    if is_duplicate_request(task_key, body.message):
        return _sse_response(_dedup_stream())

    active = StreamSessionManager.get_active_session(task_key)
    if active is not None:
        raise HTTPException(status_code=409, detail="Task is already being processed")

    try:
        settings = get_settings()
        thinking_enabled = resolve_thinking_enabled(
            body.thinking_enabled,
            provider=settings.llm_provider,
            ollama_thinking_enabled=settings.ollama_thinking_enabled,
        )
        session = await StreamSessionManager.start(
            task_id=task_key,
            user_id=user.id,
            message=body.message,
            parent_id=body.parent_id,
            mode=body.mode,
            thinking_enabled=thinking_enabled,
            user_instructions=body.user_instructions,
        )
    except StreamLockError:
        raise HTTPException(status_code=409, detail="Task is already being processed") from None

    return _sse_response(iter_session_events(session, cursor=body.cursor))


async def _dedup_stream() -> AsyncGenerator[str, None]:
    yield serialize_sse(StreamErrorEvent(message="deduplicated"))


@router.post("/{task_id}/stop", response_model=StopResponse)
async def stop_endpoint(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StopResponse:
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    abort_signal = get_or_create_abort_signal(str(task_id))
    abort_signal.set()
    return StopResponse(partial_message_id=None)
