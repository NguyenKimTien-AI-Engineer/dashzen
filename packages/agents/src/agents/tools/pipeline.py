from __future__ import annotations

from typing import Any

import structlog
from tools.context import ToolContext

from agents.gates.gate_service import init_gate, register_gate
from agents.orchestration.constants import (
    MAX_LIST_FILE_PER_ORCHESTRATOR_TURN,
    TOOL_REJECTED_RESULT,
)
from agents.streaming.events import MainToolEvent
from agents.tools.arg_normalize import normalize_tool_args
from agents.tools.loop_detection import LoopDetector
from agents.tools.partition import ToolCall
from agents.tools.registry import is_ask_bypass, is_read_only

log = structlog.get_logger()

TOOL_RESULT_MAX_CHARS = 8000
HISTORY_CAP_CHARS = 12000

_TOOL_REGISTRY: dict[str, Any] = {}


def _get_tool_registry() -> dict[str, Any]:  # type: ignore[type-arg]
    global _TOOL_REGISTRY
    if not _TOOL_REGISTRY:
        from tools.catalog import search_components
        from tools.data import csv_preview, schema_inspector
        from tools.file import edit_file, list_file, read_file, write_file
        from tools.orchestration import ask_user, set_memory, spawn_agent

        _TOOL_REGISTRY = {
            "read_file": read_file,
            "write_file": write_file,
            "list_file": list_file,
            "edit_file": edit_file,
            "spawn_agent": spawn_agent,
            "set_memory": set_memory,
            "ask_user": ask_user,
            "search_components": search_components,
            "schema_inspector": schema_inspector,
            "csv_preview": csv_preview,
        }
    return _TOOL_REGISTRY


def get_tool_definition(name: str) -> Any | None:
    module = _get_tool_registry().get(name)
    if module is None:
        return None
    return getattr(module, "DEFINITION", None)


def _validate_args(tool_name: str, args: dict) -> str | None:  # type: ignore[type-arg]
    definition = get_tool_definition(tool_name)
    if definition is None:
        return f"[Error] Unknown tool: {tool_name}"
    params = definition.parameters
    if not isinstance(params, dict):
        return None
    required = params.get("required", [])
    for field in required:
        if field not in args:
            return f"[Error] Missing required argument: {field}"
        value = args[field]
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"[Error] Missing required argument: {field}"
    return None


def _truncate_result(result: str, history_chars: int = 0) -> str:
    budget = min(TOOL_RESULT_MAX_CHARS, max(0, HISTORY_CAP_CHARS - history_chars))
    if len(result) <= budget:
        return result
    return result[:budget] + f"\n...[truncated, {len(result)} chars total]"


async def execute_tool_pipeline(
    call: ToolCall,
    ctx: ToolContext,
    detector: LoopDetector,
    mode: str | None = None,
    history_chars: int = 0,
) -> str:
    effective_mode = mode if mode is not None else ctx.mode
    call.args = normalize_tool_args(
        call.name,
        call.args,
        agent_name=ctx.agent_name,
    )

    validation_error = _validate_args(call.name, call.args)
    if validation_error:
        return validation_error

    if call.name == "list_file" and ctx.agent_name is None:
        if ctx.orchestrator_list_file_calls >= MAX_LIST_FILE_PER_ORCHESTRATOR_TURN:
            cached = ctx.read_cache.get(call.name, call.args)
            if cached is not None:
                return _truncate_result(
                    f"{cached}\n\n[Note] Reusing workspace listing — "
                    "list_file is limited to once per user message.",
                    history_chars,
                )
            return (
                "[Error] list_file already called this turn. "
                "Use the prior listing from tool history. Do not call list_file again."
            )
        ctx.orchestrator_list_file_calls += 1

    if call.name == "write_file" and ctx.agent_name is not None:
        path = str(call.args.get("path", "")).strip()
        if path and path in ctx.agent_written_paths:
            return (
                f"[Error] '{path}' was already written this agent run. "
                "Use edit_file for changes — do not call write_file again."
            )

    if is_read_only(call.name):
        cached = ctx.read_cache.get(call.name, call.args)
        if cached is not None:
            return _truncate_result(cached, history_chars)

    blocked, warning = detector.check(call.name, call.args)
    if blocked:
        return warning or "[Error] Loop detected."

    gate_feedback = ""
    if effective_mode == "ask" and not is_ask_bypass(call.name):
        task_id = str(ctx.task_id)
        await init_gate(task_id, call.call_id)
        ctx.emit(MainToolEvent(call_id=call.call_id, name=call.name, args=call.args))
        approved, gate_feedback = await register_gate(task_id, call.call_id)
        if not approved:
            if gate_feedback:
                return _truncate_result(gate_feedback, history_chars)
            return TOOL_REJECTED_RESULT

    registry = _get_tool_registry()
    module = registry.get(call.name)
    if module is None:
        return f"[Error] Unknown tool: {call.name}"

    try:
        if call.name == "ask_user":
            ctx.current_call_id = call.call_id
        result = await module.execute(call.args, ctx)
        result = str(result)
    except Exception as exc:
        log.exception("tool_execute_error", tool=call.name, error=str(exc))
        result = f"[Error] Tool execution failed: {exc}"

    if warning:
        result = f"{warning}\n{result}"

    if gate_feedback:
        result = f"{result}\n\n[User feedback] {gate_feedback}"

    if (
        call.name == "write_file"
        and ctx.agent_name is not None
        and not result.startswith("[Error]")
    ):
        path = str(call.args.get("path", "")).strip()
        if path and "written" in result.lower():
            ctx.agent_written_paths.add(path)

    if is_read_only(call.name):
        ctx.read_cache.set(call.name, call.args, result)

    return _truncate_result(result, history_chars)
