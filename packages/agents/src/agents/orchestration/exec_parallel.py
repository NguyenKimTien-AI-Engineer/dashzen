from __future__ import annotations

import asyncio
from typing import Any

import structlog
from tools.context import ToolContext

from agents.orchestration.constants import MAX_AGENTS_PER_TURN, MAX_CONCURRENT_TOOLS
from agents.tools.loop_detection import LoopDetector
from agents.tools.partition import ToolCall, partition_batches
from agents.tools.pipeline import execute_tool_pipeline
from agents.tools.registry import is_concurrent_safe

log = structlog.get_logger()


async def _execute_single(
    call: ToolCall, ctx: ToolContext, detector: LoopDetector
) -> tuple[str, str]:
    result = await execute_tool_pipeline(call, ctx, detector, mode=ctx.mode)
    return call.call_id, result


async def execute_tool_calls(
    calls: list[ToolCall],
    ctx: ToolContext,
    detector: LoopDetector,
    spawn_count: int = 0,
) -> tuple[dict[str, str], list[str]]:
    """
    Returns (results_by_call_id, overflow_call_ids).
    overflow_call_ids: spawn_agent calls that exceeded MAX_AGENTS_PER_TURN.
    """
    results: dict[str, str] = {}
    overflow_ids: list[str] = []

    non_spawn = []
    local_spawn_count = spawn_count
    for call in calls:
        if call.name == "spawn_agent":
            if local_spawn_count >= MAX_AGENTS_PER_TURN:
                overflow_ids.append(call.call_id)
                results[call.call_id] = (
                    f"[Error] Maximum {MAX_AGENTS_PER_TURN} agent spawns per turn."
                    " Retry in next turn."
                )
            else:
                local_spawn_count += 1
                non_spawn.append(call)
        else:
            non_spawn.append(call)

    batches = partition_batches(non_spawn)

    for batch in batches:
        if len(batch) == 1 or not is_concurrent_safe(batch[0].name):
            for call in batch:
                cid, res = await _execute_single(call, ctx, detector)
                results[cid] = res
        else:
            limited = batch[:MAX_CONCURRENT_TOOLS]
            tasks = [_execute_single(c, ctx, detector) for c in limited]
            for cid, res in await asyncio.gather(*tasks):
                results[cid] = res
            for call in batch[MAX_CONCURRENT_TOOLS:]:
                cid, res = await _execute_single(call, ctx, detector)
                results[cid] = res

    return results, overflow_ids
