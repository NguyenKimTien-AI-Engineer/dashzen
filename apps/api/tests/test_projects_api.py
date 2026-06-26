from __future__ import annotations

import pytest
from core.email.testing import InMemoryEmailBackend
from httpx import AsyncClient

from tests.auth_helpers import create_test_user_and_login


@pytest.mark.asyncio
async def test_project_lifecycle(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="proj")

    resp = await client.post("/v1/projects", json={"name": "Fintech"}, headers=headers)
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]
    assert project["name"] == "Fintech"
    assert project["task_count"] == 0

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = await client.patch(
        f"/v1/tasks/{task_id}",
        json={"project_id": project_id, "starred": True, "title": "Revenue dash"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == project_id
    assert body["starred"] is True
    assert body["title"] == "Revenue dash"

    resp = await client.get(f"/v1/projects/{project_id}/tasks", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/v1/projects", headers=headers)
    assert resp.status_code == 200
    assert resp.json()[0]["task_count"] == 1

    resp = await client.get("/v1/tasks", params={"starred": True}, headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.patch(
        f"/v1/tasks/{task_id}",
        json={"project_id": None},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["project_id"] is None

    resp = await client.delete(f"/v1/projects/{project_id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"/v1/tasks/{task_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["project_id"] is None


@pytest.mark.asyncio
async def test_project_ownership(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    headers_a = await create_test_user_and_login(client, mail_backend, suffix="pa")
    headers_b = await create_test_user_and_login(client, mail_backend, suffix="pb")

    resp = await client.post("/v1/projects", json={"name": "Private"}, headers=headers_a)
    project_id = resp.json()["id"]

    resp = await client.get(f"/v1/projects/{project_id}", headers=headers_b)
    assert resp.status_code == 404
