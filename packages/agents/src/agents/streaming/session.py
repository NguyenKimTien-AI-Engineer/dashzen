from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from agents.artifacts.buffer import ArtifactBuffer
from agents.orchestration.runtime import RuntimeContext
from agents.streaming.events import StreamErrorEvent, serialize_sse
from agents.streaming.guards import clear_abort_signal, get_or_create_abort_signal
from agents.streaming.lock import StreamLock, StreamLockError

_SENTINEL = object()
_TERMINAL_SSE_MARKERS = ('"type":"stream_done"', '"type":"stream_error"')


def _has_terminal_event(events: list[str]) -> bool:
    return any(marker in sse for sse in events for marker in _TERMINAL_SSE_MARKERS)


_MAX_BUFFERED_EVENTS = 10_000

RunState = Literal["running", "done", "error"]


@dataclass
class RunStatusSnapshot:
    status: Literal["idle", "running", "done", "error"]
    started_at: float | None = None
    event_count: int = 0


@dataclass
class StreamSession:
    task_id: str
    user_id: uuid.UUID
    message: str
    status: RunState = "running"
    started_at: float = field(default_factory=time.time)
    events: list[str] = field(default_factory=list)
    subscriber_queues: list[asyncio.Queue[object]] = field(default_factory=list)
    lock: StreamLock | None = None
    producer_task: asyncio.Task[None] | None = None  # type: ignore[type-arg]

    def push_event(self, sse: str) -> None:
        self.events.append(sse)
        if len(self.events) > _MAX_BUFFERED_EVENTS:
            self.events = self.events[-_MAX_BUFFERED_EVENTS:]
        for queue in list(self.subscriber_queues):
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(sse)

    def close_subscribers(self) -> None:
        for queue in list(self.subscriber_queues):
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(_SENTINEL)


class StreamSessionManager:
    """In-process registry for detached stream runs (survives client disconnect)."""

    _sessions: dict[str, StreamSession] = {}
    _mutex = asyncio.Lock()

    @classmethod
    def get_status(cls, task_id: str) -> RunStatusSnapshot:
        session = cls._sessions.get(task_id)
        if session is None:
            return RunStatusSnapshot(status="idle")
        if session.producer_task is not None and not session.producer_task.done():
            return RunStatusSnapshot(
                status="running",
                started_at=session.started_at,
                event_count=len(session.events),
            )
        return RunStatusSnapshot(
            status=session.status if session.status != "running" else "done",
            started_at=session.started_at,
            event_count=len(session.events),
        )

    @classmethod
    def get_active_session(cls, task_id: str) -> StreamSession | None:
        session = cls._sessions.get(task_id)
        if session is None:
            return None
        if session.producer_task is not None and not session.producer_task.done():
            return session
        return None

    @classmethod
    async def start(
        cls,
        *,
        task_id: str,
        user_id: uuid.UUID,
        message: str,
        parent_id: uuid.UUID | None,
        mode: str,
        thinking_enabled: bool,
        user_instructions: str,
    ) -> StreamSession:
        async with cls._mutex:
            if cls.get_active_session(task_id) is not None:
                raise StreamLockError("Task is already being processed")

            lock = StreamLock(task_id)
            await lock.acquire()

            session = StreamSession(
                task_id=task_id,
                user_id=user_id,
                message=message,
                lock=lock,
            )
            cls._sessions[task_id] = session

            session.producer_task = asyncio.create_task(
                cls._run_producer(
                    session,
                    message=message,
                    parent_id=parent_id,
                    mode=mode,
                    thinking_enabled=thinking_enabled,
                    user_instructions=user_instructions,
                )
            )
            return session

    @classmethod
    async def _run_producer(
        cls,
        session: StreamSession,
        *,
        message: str,
        parent_id: uuid.UUID | None,
        mode: str,
        thinking_enabled: bool,
        user_instructions: str,
    ) -> None:
        from db.session import get_session_factory

        from agents.gates.gate_service import unregister_all_gates
        from agents.orchestration.main_loop import main_loop

        task_id = session.task_id
        abort_signal = get_or_create_abort_signal(task_id)
        abort_signal.clear()
        artifact_buffer = ArtifactBuffer()

        def emit(event: object) -> None:
            if isinstance(event, BaseModel):
                session.push_event(serialize_sse(event))

        session_factory = get_session_factory()
        try:
            async with session_factory() as db:
                ctx = RuntimeContext(
                    task_id=uuid.UUID(task_id),
                    user_id=session.user_id,
                    db=db,
                    artifact_buffer=artifact_buffer,
                    mode=mode,
                    thinking_enabled=thinking_enabled,
                    user_instructions=user_instructions,
                    abort_signal=abort_signal,
                    emit=emit,
                )
                await main_loop(ctx, message, parent_id)
        except Exception:
            session.status = "error"
            emit(StreamErrorEvent(message="Stream processing error."))
        else:
            session.status = "done"
        finally:
            session.close_subscribers()
            await unregister_all_gates(task_id)
            if session.lock is not None:
                await session.lock.release()
            clear_abort_signal(task_id)
            async with cls._mutex:
                if cls._sessions.get(task_id) is session:
                    cls._sessions.pop(task_id, None)

    @classmethod
    async def subscribe(
        cls,
        task_id: str,
        *,
        cursor: int = 0,
    ) -> AsyncGenerator[str, None]:
        session = cls.get_active_session(task_id)
        if session is None:
            yield serialize_sse(StreamErrorEvent(message="No active stream to resume."))
            return

        start = max(0, min(cursor, len(session.events)))
        replayed = session.events[start:]
        for sse in replayed:
            yield sse

        if _has_terminal_event(replayed) or _has_terminal_event(session.events):
            return

        if session.producer_task is not None and session.producer_task.done():
            return

        queue: asyncio.Queue[object] = asyncio.Queue(maxsize=500)
        session.subscriber_queues.append(queue)
        try:
            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    break
                if isinstance(item, str):
                    yield item
        finally:
            with contextlib.suppress(ValueError):
                session.subscriber_queues.remove(queue)


async def iter_session_events(
    session: StreamSession,
    *,
    cursor: int = 0,
) -> AsyncGenerator[str, None]:
    async for chunk in StreamSessionManager.subscribe(session.task_id, cursor=cursor):
        yield chunk
