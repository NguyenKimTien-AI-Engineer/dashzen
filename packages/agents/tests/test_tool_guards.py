from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.tools.loop_detection import LoopDetector
from agents.tools.partition import ToolCall
from agents.tools.pipeline import execute_tool_pipeline
from tools.context import ToolContext


def _tool_ctx(*, agent_name: str | None = None) -> ToolContext:
    return ToolContext(
        task_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        db=MagicMock(),
        artifact_buffer=MagicMock(),
        read_cache=MagicMock(),
        emit=MagicMock(),
        agent_name=agent_name,
    )


@pytest.mark.asyncio
async def test_orchestrator_list_file_limited_to_once(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _tool_ctx()
    ctx.read_cache.get.return_value = None

    async def fake_list_file(_args: dict, _ctx: ToolContext) -> str:
        return '[{"name": "spec.md"}]'

    monkeypatch.setitem(
        __import__("agents.tools.pipeline", fromlist=["_get_tool_registry"])._TOOL_REGISTRY,
        "list_file",
        MagicMock(execute=fake_list_file),
    )

    call = ToolCall(call_id="c1", name="list_file", args={})
    detector = LoopDetector()

    first = await execute_tool_pipeline(call, ctx, detector)
    second = await execute_tool_pipeline(call, ctx, detector)

    assert "spec.md" in first
    assert "[Error] list_file already called" in second
    assert ctx.orchestrator_list_file_calls == 1


@pytest.mark.asyncio
async def test_subagent_write_file_blocked_on_duplicate_path(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _tool_ctx(agent_name="data-binder")
    ctx.agent_written_paths.add("bindings.md")

    call = ToolCall(
        call_id="c1",
        name="write_file",
        args={"path": "bindings.md", "content": "x"},
    )
    detector = LoopDetector()

    result = await execute_tool_pipeline(call, ctx, detector)

    assert "[Error]" in result
    assert "already written" in result


@pytest.mark.asyncio
async def test_subagent_write_file_tracks_successful_path(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _tool_ctx(agent_name="dashboard-builder")

    async def fake_write(_args: dict, _ctx: ToolContext) -> str:
        return "File dashboard.html written."

    monkeypatch.setitem(
        __import__("agents.tools.pipeline", fromlist=["_get_tool_registry"])._TOOL_REGISTRY,
        "write_file",
        MagicMock(execute=fake_write),
    )

    call = ToolCall(
        call_id="c1",
        name="write_file",
        args={"path": "dashboard.html", "content": "<html></html>"},
    )
    detector = LoopDetector()

    first = await execute_tool_pipeline(call, ctx, detector)
    second = await execute_tool_pipeline(call, ctx, detector)

    assert "written" in first.lower()
    assert "already written" in second
