from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import replace

import structlog
from agents.orchestration.llm_errors import format_llm_error
from core.llm.factory import get_llm_client
from core.llm.types import LLMMessage
from db.services.message_service import create_message, find_orphan_user_message, get_messages, update_message_thinking
from db.services.task_service import get_task
from tools.context import ToolContext

from agents.context.accounting import calibrate_tokens_per_char, estimate_chars
from agents.context.compaction import CompactionState, compact_if_over_budget
from agents.context.history import build_history
from agents.memory.context_block import build_context_block
from agents.memory.memory_file import read_memory
from agents.orchestration.constants import (
    MAX_AGENTS_PER_TURN,
    MAX_ITERATIONS,
    TOOL_REJECTED_RESULT,
)
from agents.orchestration.exec_parallel import execute_tool_calls
from agents.orchestration.runtime import RuntimeContext
from agents.orchestration.spawn import spawn_agent
from agents.streaming.events import (
    MainResultEvent,
    MainTextEvent,
    MainThinkEvent,
    MainToolEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    TaskMetaEvent,
)
from agents.tools.loop_detection import LoopDetector
from agents.tools.partition import ToolCall
from agents.tools.read_cache import ReadCache

log = structlog.get_logger()


async def main_loop(
    ctx: RuntimeContext,
    user_message: str,
    parent_id: uuid.UUID | None,
) -> None:
    from agents.orchestration.activity_log import ActivityLogAccumulator, encode_activity_log
    from agents.orchestration.task_title import try_set_title
    from agents.registry.loader import build_orchestrator_tool_definitions, load_system_prompt, load_workflow

    tool_defs = build_orchestrator_tool_definitions("main")
    client = get_llm_client()
    detector = LoopDetector()
    read_cache = ReadCache()
    total_spawn_count = 0
    compaction_state = CompactionState()
    tool_rejected = False
    activity_acc = ActivityLogAccumulator()
    assistant_msg_id: uuid.UUID | None = None

    def emit_logged(event: object) -> None:
        activity_acc.record(event)
        ctx.emit(event)

    try:
        orphan = await find_orphan_user_message(ctx.db, ctx.task_id)
        if orphan and orphan.content == user_message:
            user_msg = orphan
        else:
            user_msg = await create_message(
                ctx.db,
                task_id=ctx.task_id,
                role="user",
                content=user_message,
                parent_id=parent_id,
            )
            await ctx.db.commit()

        history = await get_messages(ctx.db, ctx.task_id)
        messages: list[LLMMessage] = build_history(history)

        system_prompt = load_system_prompt("main")

        turn_number = len([m for m in history if m.role == "user"])
        title_task = asyncio.create_task(
            try_set_title(ctx.db, ctx.task_id, user_message, turn_number)
        )

        tool_ctx = ToolContext(
            task_id=ctx.task_id,
            user_id=ctx.user_id,
            db=ctx.db,
            artifact_buffer=ctx.artifact_buffer,
            read_cache=read_cache,
            emit=emit_logged,
            mode=ctx.mode,
            thinking_enabled=ctx.thinking_enabled,
            abort_signal=ctx.abort_signal,
        )

        current_parent = user_msg.id

        async def _persist_activity_log() -> None:
            if assistant_msg_id is None:
                return
            task_row = await get_task(ctx.db, ctx.task_id, ctx.user_id)
            if task_row and task_row.title:
                activity_acc.set_header_title(task_row.title)
            built = activity_acc.build()
            if not built.header_title and not built.sections:
                return
            await update_message_thinking(
                ctx.db,
                assistant_msg_id,
                encode_activity_log(built),
            )

        for iteration in range(MAX_ITERATIONS):
            if ctx.abort_signal.is_set():
                break

            activity_acc.begin_orchestrator_iteration(iteration)

            messages, _ = await compact_if_over_budget(
                messages,
                ctx.db,
                ctx.task_id,
                compaction_state,
                leaf_id=current_parent,
                parent_id=current_parent,
            )

            memory_state = await read_memory(
                ctx.db, ctx.task_id, ctx.artifact_buffer
            )

            memory_content = ctx.artifact_buffer.get("memory.md") or ""
            if not memory_content:
                from db.services.file_service import get_file

                memory_file = await get_file(ctx.db, ctx.task_id, "memory.md")
                if memory_file and memory_file.content:
                    memory_content = memory_file.content
            workflow_content = (
                load_workflow(memory_state.type, memory_state.phase)
                if memory_state.phase
                else ""
            )
            context_msg = LLMMessage(
                role="user",
                content=build_context_block(
                    memory_content, workflow_content, ctx.user_instructions
                ),
            )
            llm_payload = [LLMMessage(role="system", content=system_prompt), *messages, context_msg]

            text_acc = ""
            tool_calls_raw: list[dict] = []  # type: ignore[type-arg]
            prompt_tokens: int | None = None

            async for delta in client.stream(
                llm_payload,
                tool_defs,
                max_tokens=8192,
                thinking_enabled=ctx.thinking_enabled,
            ):
                if ctx.abort_signal.is_set():
                    break
                if delta.kind == "text_delta" and delta.text:
                    text_acc += delta.text
                    emit_logged(MainTextEvent(delta=delta.text))
                elif delta.kind == "thinking_delta" and delta.thinking:
                    emit_logged(MainThinkEvent(delta=delta.thinking))
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
                    emit_logged(MainToolEvent(
                        call_id=tc_entry["id"], name=tc_entry["name"], args=args
                    ))
                elif delta.kind == "done":
                    prompt_tokens = delta.prompt_tokens
                    break

            if prompt_tokens:
                compaction_state.last_real_prompt_tokens = prompt_tokens
                compaction_state.tokens_per_char = calibrate_tokens_per_char(
                    prompt_tokens, [*messages, context_msg]
                )
                compaction_state.chars_at_last_call = estimate_chars(messages)

            tool_calls_for_db = (
                [
                    {"id": tc["id"], "name": tc["name"], "input": tc["input"]}
                    for tc in tool_calls_raw
                ]
                if tool_calls_raw
                else None
            )
            tool_calls_content = json.dumps(tool_calls_for_db) if tool_calls_for_db else ""

            asst_msg = await create_message(
                ctx.db,
                task_id=ctx.task_id,
                role="assistant",
                content=text_acc + (tool_calls_content or ""),
                parent_id=current_parent,
                prompt_tokens=prompt_tokens,
            )
            await ctx.db.commit()
            assistant_msg_id = asst_msg.id

            if not tool_calls_raw:
                break

            calls = [
                ToolCall(call_id=tc["id"], name=tc["name"], args=tc["input"])
                for tc in tool_calls_raw
            ]

            tool_results: dict[str, str] = {}
            overflow_ids: list[str] = []

            spawn_calls = [c for c in calls if c.name == "spawn_agent"]
            other_calls = [c for c in calls if c.name != "spawn_agent"]

            if other_calls:
                other_results, other_overflow = await execute_tool_calls(
                    other_calls, tool_ctx, detector, total_spawn_count
                )
                tool_results.update(other_results)
                overflow_ids.extend(other_overflow)

            for sc in spawn_calls:
                if total_spawn_count >= MAX_AGENTS_PER_TURN:
                    result_str = f"[Error] Max {MAX_AGENTS_PER_TURN} spawns reached."
                    overflow_ids.append(sc.call_id)
                    tool_results[sc.call_id] = result_str
                else:
                    agent_name = str(sc.args.get("agent", "")).strip()
                    agent_key = agent_name.lower()
                    if agent_key in tool_ctx.orchestrator_spawn_attempted:
                        tool_results[sc.call_id] = (
                            f"[Error] Agent '{agent_name}' was already spawned this user turn. "
                            "Use the prior spawn result in tool history. "
                            "Follow # WORKFLOW for the next step."
                        )
                        continue

                    total_spawn_count += 1
                    tool_ctx.orchestrator_spawn_attempted.add(agent_key)
                    tool_ctx_with_msg = replace(tool_ctx, current_message_id=asst_msg.id)

                    agent_result = await spawn_agent(
                        agent_name=agent_name,
                        task_description=str(sc.args.get("task", "")),
                        ctx=tool_ctx_with_msg,
                        emit=emit_logged,
                    )
                    tool_results[sc.call_id] = agent_result
                    read_cache.invalidate_workspace_listing()
                    await ctx.artifact_buffer.persist_staged(
                        ctx.db, ctx.task_id, asst_msg.id
                    )

            for tc in tool_calls_raw:
                result_str = tool_results.get(tc["id"], "[Error] No result.")
                if result_str == TOOL_REJECTED_RESULT:
                    tool_rejected = True
                emit_logged(MainResultEvent(
                    call_id=tc["id"], status="success", result=result_str[:500]
                ))
                await create_message(
                    ctx.db,
                    task_id=ctx.task_id,
                    role="tool",
                    content=result_str,
                    parent_id=asst_msg.id,
                )
            await ctx.db.commit()

            messages.append(LLMMessage(
                role="assistant", content=text_acc, tool_calls=tool_calls_for_db
            ))
            for tc in tool_calls_raw:
                messages.append(LLMMessage(
                    role="tool",
                    content=tool_results.get(tc["id"], ""),
                    tool_call_id=tc["id"],
                ))
            current_parent = asst_msg.id

            if tool_rejected:
                break

        await _persist_activity_log()

        await ctx.artifact_buffer.flush_and_remap(ctx.db, ctx.task_id, assistant_msg_id)
        await ctx.db.commit()

        try:
            title = await asyncio.wait_for(title_task, timeout=5.0)
        except (TimeoutError, Exception):
            title = None

        if title:
            task = await get_task(ctx.db, ctx.task_id, ctx.user_id)
            if task and task.title == title:
                activity_acc.set_header_title(title)
                await _persist_activity_log()
                await ctx.db.commit()
                emit_logged(TaskMetaEvent(title=title))

        emit_logged(StreamDoneEvent())

    except Exception as exc:
        log.exception("main_loop_error", error=str(exc))
        message = format_llm_error(exc)
        err_event = StreamErrorEvent(message=message)
        emit_logged(err_event)
        try:
            await ctx.artifact_buffer.flush_and_remap(ctx.db, ctx.task_id, assistant_msg_id)
            await ctx.db.commit()
        except Exception:
            await ctx.db.rollback()
