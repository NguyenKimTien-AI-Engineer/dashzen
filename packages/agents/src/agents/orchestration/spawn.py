from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC
from typing import Any

import structlog
from tools.context import ToolContext

from agents.orchestration.agent_status import format_agent_tool_result, parse_agent_status_block
from agents.orchestration.constants import (
    ACTIVITY_COUNT_MAX,
    ACTIVITY_RESULT_MAX,
    AGENT_OUTPUT_COMPACT_THRESHOLD,
    SPAWN_SUMMARY_MAX,
)
from agents.orchestration.llm_errors import format_llm_error
from agents.streaming.events import AgentDoneEvent, AgentStartEvent

log = structlog.get_logger()


def _activity_write_summary(activities: list[dict]) -> str:  # type: ignore[type-arg]
    for activity in reversed(activities):
        if activity.get("tool") != "write_file":
            continue
        tool_result = str(activity.get("result", ""))
        if tool_result and not tool_result.startswith("[Error]"):
            return tool_result[:SPAWN_SUMMARY_MAX]
    return ""


def _resolve_spawn_result(
    result_output: str,
    *,
    timed_out: bool,
    activities: list[dict],  # type: ignore[type-arg]
) -> tuple[str, str, str]:
    """Return (event_status, agent_status, summary) for UI event and orchestrator tool result."""
    if timed_out:
        return "timeout", "FAIL", "Agent timed out before completing."

    parsed = parse_agent_status_block(result_output)
    if parsed:
        agent_status, summary = parsed
        event_status = "error" if agent_status == "FAIL" else "done"
        return event_status, agent_status, summary[:SPAWN_SUMMARY_MAX]

    fallback = _activity_write_summary(activities)
    if fallback:
        return "done", "DONE", fallback

    if result_output.strip():
        return "done", "DONE", result_output[:SPAWN_SUMMARY_MAX]

    return "error", "FAIL", "No status block in agent output."


async def spawn_agent(
    agent_name: str,
    task_description: str,
    ctx: ToolContext,
    emit: Callable[[Any], None],
) -> str:
    """Execute an agent and return compact result."""
    from agents.orchestration.agent_loop import run_agent_loop
    from agents.registry.loader import get_agent
    from agents.tools.registry import resolve_agent_tools

    defn = get_agent(agent_name)
    if defn is None:
        return f"[Error] Agent '{agent_name}' not found in registry."

    call_id = str(uuid.uuid4())
    display_name = defn.display_name or agent_name
    ctx.agent_written_paths.clear()
    emit(AgentStartEvent(call_id=call_id, name=agent_name, display_name=display_name))

    allowed_tools = resolve_agent_tools(defn.tools, defn.disallowed_tools)

    activities: list[dict] = []  # type: ignore[type-arg]

    def record_activity(tool_name: str, args: dict, result: str) -> None:  # type: ignore[type-arg]
        from datetime import datetime

        if len(activities) >= ACTIVITY_COUNT_MAX:
            return
        activities.append(
            {
                "tool": tool_name,
                "args": args,
                "result": result[:ACTIVITY_RESULT_MAX],
                "ts": datetime.now(tz=UTC).isoformat(),
            }
        )

    try:
        result = await run_agent_loop(
            task_description=task_description,
            agent_name=agent_name,
            allowed_tools=allowed_tools,
            ctx=ctx,
            parent_call_id=call_id,
            emit=emit,
            on_tool_done=record_activity,
            max_turns=defn.max_turns,
        )
    except Exception as exc:
        log.exception("spawn_agent_failed", agent=agent_name, error=str(exc))
        summary = format_llm_error(exc)
        emit(AgentDoneEvent(call_id=call_id, status="error", summary=summary))
        return f"[Error] {summary}"

    event_status, agent_status, summary = _resolve_spawn_result(
        result.output,
        timed_out=result.timed_out,
        activities=activities,
    )
    emit(AgentDoneEvent(call_id=call_id, status=event_status, summary=summary))

    from db.services.agent_run_service import upsert_agent_run

    message_id = ctx.current_message_id
    if message_id is not None:
        await upsert_agent_run(
            ctx.db,
            message_id=message_id,
            call_id=uuid.UUID(call_id),
            name=agent_name,
            activities=activities,
            status=event_status,
            summary=summary,
        )

    status_block = format_agent_tool_result(agent_status, summary)
    if len(result.output) <= AGENT_OUTPUT_COMPACT_THRESHOLD and parse_agent_status_block(
        result.output
    ):
        return result.output.strip()
    return status_block
