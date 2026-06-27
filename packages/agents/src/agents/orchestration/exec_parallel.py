from __future__ import annotations

import asyncio

import structlog
from tools.context import ToolContext

from agents.orchestration.constants import MAX_CONCURRENT_TOOLS
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
) -> dict[str, str]:
    """Execute non-spawn tool calls, respecting concurrency limits. Returns results by call_id."""
    results: dict[str, str] = {}
    batches = partition_batches(calls)

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

    return results
