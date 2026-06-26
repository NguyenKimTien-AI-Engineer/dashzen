from __future__ import annotations

import uuid

import pytest
from core.email.testing import InMemoryEmailBackend
from httpx import AsyncClient

from tests.auth_helpers import create_test_user_and_login


@pytest.mark.asyncio
async def test_task_lifecycle(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    headers = await create_test_user_and_login(client, mail_backend)

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task = resp.json()
    task_id = task["id"]
    assert task["status"] == "active"
    assert task["type"] is None
    assert task["title"] is None

    resp = await client.get("/v1/tasks", headers=headers)
    assert resp.status_code == 200
    assert any(t["id"] == task_id for t in resp.json())

    resp = await client.get(f"/v1/tasks/{task_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id

    resp = await client.patch(
        f"/v1/tasks/{task_id}", json={"title": "My Dashboard"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "My Dashboard"

    resp = await client.get(f"/v1/tasks/{task_id}/messages", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    resp = await client.get(f"/v1/tasks/{task_id}/artifacts", headers=headers)
    assert resp.status_code == 200
    artifacts = resp.json()
    assert any(a["name"] == "memory.md" for a in artifacts)

    resp = await client.delete(f"/v1/tasks/{task_id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"/v1/tasks/{task_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_llm_budget(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    resp = await client.get("/v1/llm/budget")
    assert resp.status_code == 200
    data = resp.json()
    assert "contextWindow" in data
    assert "inputBudgetTokens" in data
    assert "microCompactFraction" in data
    assert "summaryCompactFraction" in data


@pytest.mark.asyncio
async def test_task_ownership(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    headers_a = await create_test_user_and_login(client, mail_backend, suffix="a")
    headers_b = await create_test_user_and_login(client, mail_backend, suffix="b")

    resp = await client.post("/v1/tasks", json={}, headers=headers_a)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = await client.get(f"/v1/tasks/{task_id}", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stop_nonexistent_task(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="stop")
    fake_id = str(uuid.uuid4())
    resp = await client.post(f"/v1/tasks/{fake_id}/stop", headers=headers)
    assert resp.status_code == 404
