from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from core.email.testing import InMemoryEmailBackend
from core.llm.types import LLMDelta
from tests.auth_helpers import create_test_user_and_login


class _MockLLMClient:
    async def stream(
        self,
        messages: list,  # type: ignore[type-arg]
        tools: list,  # type: ignore[type-arg]
        *,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        thinking_enabled: bool = False,
    ) -> AsyncGenerator[LLMDelta, None]:
        yield LLMDelta(kind="text_delta", text="Hello ")
        yield LLMDelta(kind="text_delta", text="world")
        yield LLMDelta(kind="done", prompt_tokens=10, output_tokens=5)

    async def chat(self, *args, **kwargs) -> str:  # type: ignore[no-untyped-def]
        return "title"


def _parse_sse_events(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_stream_returns_sse_events(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="stream")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    with patch("agents.orchestration.main_loop.get_llm_client", return_value=_MockLLMClient()):
        with patch(
            "agents.orchestration.task_title.try_set_title",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.post(
                f"/v1/tasks/{task_id}/stream",
                json={"message": "hello", "mode": "auto"},
                headers=headers,
            )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)
    types = [e["type"] for e in events]
    assert "main_text" in types
    assert "stream_done" in types


@pytest.mark.asyncio
async def test_run_status_idle(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="runstatus")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    status = await client.get(f"/v1/tasks/{task_id}/run-status", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "idle"
    assert body["event_count"] == 0


@pytest.mark.asyncio
async def test_stream_concurrent_returns_409(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    from agents.streaming.lock import StreamLock

    headers = await create_test_user_and_login(client, mail_backend, suffix="concurrent")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    lock = StreamLock(str(task_id))
    await lock.acquire()
    try:
        second = await client.post(
            f"/v1/tasks/{task_id}/stream",
            json={"message": "second", "mode": "auto"},
            headers=headers,
        )
        assert second.status_code == 409
    finally:
        await lock.release()
