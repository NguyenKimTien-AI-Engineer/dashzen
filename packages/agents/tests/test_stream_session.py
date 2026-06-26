from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from agents.streaming.events import MainTextEvent, StreamDoneEvent, serialize_sse
from agents.streaming.session import StreamSession, StreamSessionManager


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_subscribe_replays_buffered_events() -> None:
    task_id = "task-replay"
    session = StreamSession(task_id=task_id, user_id=uuid.uuid4(), message="hello")
    session.producer_task = asyncio.create_task(asyncio.sleep(60))
    session.push_event(serialize_sse(MainTextEvent(delta="hello")))
    session.push_event(serialize_sse(StreamDoneEvent()))
    StreamSessionManager._sessions[task_id] = session

    try:
        chunks: list[str] = []
        async for chunk in StreamSessionManager.subscribe(task_id, cursor=0):
            chunks.append(chunk)

        events = _parse_sse("".join(chunks))
        types = [e["type"] for e in events]
        assert types == ["main_text", "stream_done"]
    finally:
        session.producer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await session.producer_task
        StreamSessionManager._sessions.pop(task_id, None)


@pytest.mark.asyncio
async def test_subscribe_from_cursor_skips_replayed_prefix() -> None:
    task_id = "task-cursor"
    session = StreamSession(task_id=task_id, user_id=uuid.uuid4(), message="hello")
    session.producer_task = asyncio.create_task(asyncio.sleep(60))
    session.push_event(serialize_sse(MainTextEvent(delta="first")))
    session.push_event(serialize_sse(MainTextEvent(delta="second")))
    session.push_event(serialize_sse(StreamDoneEvent()))
    StreamSessionManager._sessions[task_id] = session

    try:
        chunks: list[str] = []
        async for chunk in StreamSessionManager.subscribe(task_id, cursor=1):
            chunks.append(chunk)

        events = _parse_sse("".join(chunks))
        assert len(events) == 2
        assert events[0]["type"] == "main_text"
        assert events[0]["delta"] == "second"
        assert events[1]["type"] == "stream_done"
    finally:
        session.producer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await session.producer_task
        StreamSessionManager._sessions.pop(task_id, None)


def test_run_status_idle_when_no_session() -> None:
    assert StreamSessionManager.get_status("missing-task").status == "idle"
