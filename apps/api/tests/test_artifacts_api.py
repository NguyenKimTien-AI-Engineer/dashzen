from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from core.email.testing import InMemoryEmailBackend
from db.services.file_service import upsert_workspace_file
from db.session import get_db
from tests.auth_helpers import create_test_user_and_login

_DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><script src="https://cdn.tailwindcss.com"></script></head>
<body><h1>Revenue</h1><!-- builder --></body></html>"""


@pytest.mark.asyncio
async def test_list_user_artifacts(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="art")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    task_id = uuid.UUID(resp.json()["id"])
    await client.patch(
        f"/v1/tasks/{task_id}",
        json={"title": "Revenue Dashboard"},
        headers=headers,
    )

    async for db in get_db():
        await upsert_workspace_file(
            db,
            task_id=task_id,
            name="dashboard.html",
            content=_DASHBOARD_HTML,
            kind="text",
            content_type="text/html",
        )
        await db.commit()
        break

    resp = await client.get("/v1/artifacts", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["name"] == "dashboard.html"
    assert items[0]["task_title"] == "Revenue Dashboard"

    artifact_id = items[0]["id"]
    resp = await client.get(f"/v1/artifacts/{artifact_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert "<!DOCTYPE html>" in (detail["content"] or "")


@pytest.mark.asyncio
async def test_artifact_ownership(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    headers_a = await create_test_user_and_login(client, mail_backend, suffix="aa")
    headers_b = await create_test_user_and_login(client, mail_backend, suffix="ab")

    resp = await client.post("/v1/tasks", json={}, headers=headers_a)
    task_id = uuid.UUID(resp.json()["id"])

    async for db in get_db():
        file_row = await upsert_workspace_file(
            db,
            task_id=task_id,
            name="dashboard.html",
            content=_DASHBOARD_HTML,
        )
        await db.commit()
        artifact_id = file_row.id
        break

    resp = await client.get(f"/v1/artifacts/{artifact_id}", headers=headers_b)
    assert resp.status_code == 404
