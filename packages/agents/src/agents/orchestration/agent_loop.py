from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import structlog
from core.llm.factory import get_llm_client
from core.llm.types import LLMMessage, ToolDefinition
from tools.context import ToolContext

from agents.orchestration.constants import SUBAGENT_MAX_TURNS, SUBAGENT_TIMEOUT_SEC
from agents.streaming.events import (
    AgentResultEvent,
    AgentTextEvent,
    AgentThinkEvent,
    AgentToolEvent,
)
from agents.tools.loop_detection import LoopDetector
from agents.tools.partition import ToolCall

log = structlog.get_logger()


@dataclass
class AgentRunResult:
    output: str
    tools_used: list[str] = field(default_factory=list)
    iterations: int = 0
    timed_out: bool = False


def _build_tool_definitions(allowed_tools: frozenset[str]) -> list[ToolDefinition]:
    from agents.tools.pipeline import get_tool_definition

    defs: list[ToolDefinition] = []
    for name in sorted(allowed_tools):
        definition = get_tool_definition(name)
        if definition is not None:
            defs.append(definition)
    return defs


async def _execute_tool(
    call: ToolCall,
    ctx: ToolContext,
    detector: LoopDetector,
    on_tool_done: Callable[[str, dict, str], None] | None,
) -> str:
    from agents.tools.pipeline import execute_tool_pipeline

    try:
        result = await execute_tool_pipeline(call, ctx, detector, mode=ctx.mode)
        if on_tool_done:
            on_tool_done(call.name, call.args, result)
        return result
    except Exception as exc:
        return f"[Error] {exc}"


async def run_agent_loop(
    task_description: str,
    agent_name: str,
    allowed_tools: frozenset[str],
    ctx: ToolContext,
    parent_call_id: str,
    emit: Callable[[Any], None],
    on_tool_done: Callable[[str, dict, str], None] | None = None,
    max_turns: int = SUBAGENT_MAX_TURNS,
) -> AgentRunResult:
    from agents.registry.loader import get_agent, load_system_prompt

    defn = get_agent(agent_name)
    system_prompt = load_system_prompt("agent")
    agent_prompt = defn.prompt if defn else ""

    messages: list[LLMMessage] = [
        LLMMessage(role="user", content=task_description),
    ]
    tool_defs = _build_tool_definitions(allowed_tools)
    detector = LoopDetector()
    client = get_llm_client()
    tools_used: list[str] = []
    output_text = ""
    iterations = 0
    timed_out = False

    full_system = f"{system_prompt}\n\n{agent_prompt}".strip()
    ctx.agent_name = agent_name

    async def _run() -> None:
        nonlocal output_text, iterations, timed_out

        for iteration in range(max_turns):
            iterations = iteration + 1
            all_messages = [LLMMessage(role="system", content=full_system), *messages]
            text_acc = ""
            tool_calls_raw: list[dict] = []  # type: ignore[type-arg]

            async for delta in client.stream(
                all_messages,
                tool_defs,
                max_tokens=defn.max_tokens or 8192 if defn else 8192,
                temperature=defn.temperature if defn else 0.7,
                thinking_enabled=ctx.thinking_enabled,
            ):
                if delta.kind == "text_delta" and delta.text:
                    text_acc += delta.text
                    emit(AgentTextEvent(call_id=parent_call_id, delta=delta.text))
                elif delta.kind == "thinking_delta" and delta.thinking:
                    emit(AgentThinkEvent(call_id=parent_call_id, delta=delta.thinking))
                elif delta.kind == "tool_call":
                    try:
                        args = json.loads(delta.tool_args_json or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    tc_entry = {
                        "id": delta.tool_call_id or str(uuid.uuid4()),
                        "name": delta.tool_name or "",
                        "input": args,
                    }
                    tool_calls_raw.append(tc_entry)
                    emit(AgentToolEvent(
                        call_id=parent_call_id,
                        tool_call_id=tc_entry["id"],
                        name=tc_entry["name"],
                        args=args,
                    ))
                elif delta.kind == "done":
                    break

            if text_acc:
                output_text = text_acc

            messages.append(LLMMessage(
                role="assistant",
                content=text_acc,
                tool_calls=[
                    {"id": tc["id"], "name": tc["name"], "input": tc["input"]}
                    for tc in tool_calls_raw
                ] or None,
            ))

            if not tool_calls_raw:
                break

            tool_result_messages: list[LLMMessage] = []
            for tc in tool_calls_raw:
                call = ToolCall(call_id=tc["id"], name=tc["name"], args=tc["input"])
                tools_used.append(tc["name"])
                result = await _execute_tool(call, ctx, detector, on_tool_done)
                emit(AgentResultEvent(
                    call_id=parent_call_id,
                    tool_call_id=tc["id"],
                    status="success",
                    result=result[:500],
                ))
                tool_result_messages.append(LLMMessage(
                    role="tool",
                    content=result,
                    tool_call_id=tc["id"],
                ))
            messages.extend(tool_result_messages)

    try:
        await asyncio.wait_for(_run(), timeout=SUBAGENT_TIMEOUT_SEC)
    except TimeoutError:
        timed_out = True

    return AgentRunResult(
        output=output_text,
        tools_used=tools_used,
        iterations=iterations,
        timed_out=timed_out,
    )
