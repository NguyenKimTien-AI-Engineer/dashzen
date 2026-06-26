from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from tools.data.schema_inspector import execute


@pytest.mark.asyncio
async def test_schema_inspector_reads_staged_csv() -> None:
    ctx = MagicMock()
    ctx.artifact_buffer.get = lambda name: (
        "region,amount\nNorth,10\nSouth,20" if name == "sales.csv" else None
    )
    ctx.artifact_buffer.keys = lambda: ["sales.csv"]
    ctx.db = MagicMock()
    ctx.task_id = "task"

    raw = await execute({"source": "sales.csv"}, ctx)
    payload = json.loads(raw)
    assert payload["source"] == "sales.csv"
    assert payload["tables"][0]["name"] == "sales"
    assert payload["tables"][0]["columns"] == [
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "integer"},
    ]


@pytest.mark.asyncio
async def test_schema_inspector_lists_workspace_csvs(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = MagicMock()
    ctx.artifact_buffer.get = lambda _name: None
    ctx.artifact_buffer.keys = lambda: []
    ctx.db = MagicMock()
    ctx.task_id = "task"

    file_row = MagicMock()
    file_row.name = "orders.csv"
    file_row.content = "id,total\n1,9.5\n"

    monkeypatch.setattr(
        "db.services.file_service.get_artifacts",
        AsyncMock(return_value=[file_row]),
    )
    monkeypatch.setattr(
        "db.services.file_service.get_file",
        AsyncMock(return_value=file_row),
    )

    raw = await execute({}, ctx)
    payload = json.loads(raw)
    assert payload["source"] == "workspace"
    assert len(payload["tables"]) == 1
    assert payload["tables"][0]["path"] == "orders.csv"
