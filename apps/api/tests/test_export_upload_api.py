from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.email.testing import InMemoryEmailBackend
from db.services.file_service import upsert_workspace_file
from tests.auth_helpers import create_test_user_and_login

_FIXTURES = Path(__file__).resolve().parents[3] / "packages/eval/src/eval/fixtures"


@pytest.mark.asyncio
async def test_upload_csv_appears_in_artifacts(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="upload")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    csv_data = b"region,amount\nnorth,100\nsouth,200\n"
    resp = await client.post(
        f"/v1/tasks/{task_id}/upload",
        headers=headers,
        files={"file": ("sales.csv", csv_data, "text/csv")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "sales.csv"
    assert body["source"] == "upload"

    resp = await client.get(f"/v1/tasks/{task_id}/artifacts", headers=headers)
    assert resp.status_code == 200
    names = {a["name"] for a in resp.json()}
    assert "sales.csv" in names


@pytest.mark.asyncio
async def test_upload_rejects_forbidden_mime(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="mime")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    task_id = resp.json()["id"]

    resp = await client.post(
        f"/v1/tasks/{task_id}/upload",
        headers=headers,
        files={"file": ("evil.exe", b"data", "application/x-msdownload")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_export_zip_with_valid_artifacts(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
    db_engine,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="export")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as db:
        import uuid

        tid = uuid.UUID(task_id)
        await upsert_workspace_file(
            db, task_id=tid, name="spec.md", content=(_FIXTURES / "valid_spec.md").read_text()
        )
        await upsert_workspace_file(
            db, task_id=tid, name="dashboard.html", content=(_FIXTURES / "valid_dashboard.html").read_text()
        )
        await db.commit()

    resp = await client.get(f"/v1/tasks/{task_id}/export/zip", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = set(zf.namelist())
        assert "spec.md" in names
        assert "dashboard.html" in names


@pytest.mark.asyncio
async def test_export_rejects_invalid_spec(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
    db_engine,
) -> None:
    headers = await create_test_user_and_login(client, mail_backend, suffix="export-bad")

    resp = await client.post("/v1/tasks", json={}, headers=headers)
    task_id = resp.json()["id"]

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as db:
        import uuid

        tid = uuid.UUID(task_id)
        await upsert_workspace_file(
            db, task_id=tid, name="spec.md", content=(_FIXTURES / "invalid_spec.md").read_text()
        )
        await upsert_workspace_file(
            db, task_id=tid, name="dashboard.html", content=(_FIXTURES / "valid_dashboard.html").read_text()
        )
        await db.commit()

    resp = await client.get(f"/v1/tasks/{task_id}/export/zip", headers=headers)
    assert resp.status_code == 400
