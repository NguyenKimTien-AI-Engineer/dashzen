from __future__ import annotations

import uuid

import pytest
from agents.gates.gate_service import _mem_ask, _mem_gates, init_ask_gate, init_gate
from core.email.testing import InMemoryEmailBackend
from httpx import AsyncClient

from tests.auth_helpers import create_test_user_and_login


@pytest.mark.asyncio
async def test_resolve_tool_gate_approve(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="gates")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]
    call_id = str(uuid.uuid4())

    _mem_gates.clear()
    await init_gate(task_id, call_id)

    resp = await client.post(
        f"/v1/tasks/{task_id}/gates/tool",
        json={"call_id": call_id, "approved": True, "feedback": "looks good"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["resolved"] is True


@pytest.mark.asyncio
async def test_resolve_tool_gate_not_found(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="gates404")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    task_id = resp.json()["id"]

    resp = await client.post(
        f"/v1/tasks/{task_id}/gates/tool",
        json={"call_id": str(uuid.uuid4()), "approved": True},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resolve_ask_gate(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="ask")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    task_id = resp.json()["id"]
    call_id = str(uuid.uuid4())

    _mem_ask.clear()
    await init_ask_gate(task_id, call_id)

    resp = await client.post(
        f"/v1/tasks/{task_id}/gates/ask",
        json={"call_id": call_id, "answer": "Use bar chart"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["resolved"] is True
