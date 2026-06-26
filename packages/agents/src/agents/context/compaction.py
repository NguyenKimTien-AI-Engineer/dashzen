from __future__ import annotations

import uuid
from dataclasses import dataclass

import structlog
from core.llm.budget import (
    INITIAL_TOKENS_PER_CHAR,
    INPUT_BUDGET_TOKENS,
    KEEP_TOKENS,
    MICRO_COMPACT_AT_TOKENS,
    SUMMARY_COMPACT_AT_TOKENS,
)
from core.llm.factory import get_llm_client
from core.llm.types import LLMMessage
from db.services.message_service import create_message, get_tree_path
from sqlalchemy.ext.asyncio import AsyncSession

from agents.context.accounting import estimate_chars
from agents.context.history import (
    build_compact_summary_message,
    build_history,
    microcompact_tool_messages,
)

log = structlog.get_logger()

_TOOL_PLACEHOLDER = "[Tool result truncated]"


@dataclass
class CompactionState:
    last_real_prompt_tokens: int = 0
    tokens_per_char: float = INITIAL_TOKENS_PER_CHAR
    compaction_exhausted: bool = False
    chars_at_last_call: int = 0


def _estimate_tokens(messages: list[LLMMessage], state: CompactionState) -> int:
    if state.last_real_prompt_tokens <= 0:
        return int(estimate_chars(messages) * state.tokens_per_char)
    delta_chars = max(0, estimate_chars(messages) - state.chars_at_last_call)
    return state.last_real_prompt_tokens + int(delta_chars * state.tokens_per_char)


def _split_keep_tail(messages: list[LLMMessage], keep_tokens: int, ratio: float) -> int:
    if not messages:
        return 0
    running = 0
    for i in range(len(messages) - 1, -1, -1):
        running += int(estimate_chars([messages[i]]) * ratio)
        if running >= keep_tokens:
            return i
    return 0


async def _summarize_messages(messages: list[LLMMessage]) -> str:
    lines: list[str] = []
    for msg in messages:
        role = msg.role
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if content == _TOOL_PLACEHOLDER:
            continue
        lines.append(f"{role}: {content[:2000]}")
    transcript = "\n".join(lines)
    prompt = (
        "Summarize the following conversation history concisely. "
        "Preserve key facts, decisions, file names, and user goals.\n\n"
        f"{transcript}"
    )
    client = get_llm_client()
    return await client.chat(
        [LLMMessage(role="user", content=prompt)],
        max_tokens=4096,
        temperature=0.2,
    )


async def compact_if_over_budget(
    messages: list[LLMMessage],
    db: AsyncSession,
    task_id: uuid.UUID,
    state: CompactionState,
    *,
    leaf_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
) -> tuple[list[LLMMessage], bool]:
    if state.compaction_exhausted:
        return messages, False

    estimated = _estimate_tokens(messages, state)
    if estimated <= MICRO_COMPACT_AT_TOKENS:
        return messages, False

    compacted = False
    working = list(messages)

    if estimated > MICRO_COMPACT_AT_TOKENS:
        working = microcompact_tool_messages(working)
        compacted = True
        estimated = _estimate_tokens(working, state)

    if estimated <= SUMMARY_COMPACT_AT_TOKENS:
        return working, compacted

    if leaf_id is None:
        return working, compacted

    path = await get_tree_path(db, task_id, leaf_id)
    full_history = build_history(path)
    split_at = _split_keep_tail(full_history, KEEP_TOKENS, state.tokens_per_char)
    if split_at <= 0:
        state.compaction_exhausted = True
        return working, compacted

    to_summarize = full_history[:split_at]
    tail = full_history[split_at:]
    summary = await _summarize_messages(to_summarize)

    if parent_id is not None:
        await create_message(
            db,
            task_id=task_id,
            role="compact",
            content=summary,
            parent_id=parent_id,
        )
        await db.commit()

    rebuilt = [build_compact_summary_message(summary), *tail]
    post_estimated = _estimate_tokens(rebuilt, state)
    if post_estimated > INPUT_BUDGET_TOKENS:
        state.compaction_exhausted = True

    log.info(
        "summary_compact",
        task_id=str(task_id),
        split_at=split_at,
        summary_chars=len(summary),
    )
    return rebuilt, True


async def manual_compact(db: AsyncSession, task_id: uuid.UUID) -> tuple[str, int]:
    """Manual tier-2 compact for API endpoint."""
    from db.services.message_service import get_messages

    messages = list(await get_messages(db, task_id))
    if len(messages) < 2:
        return "", 0

    to_summarize = messages[:-2]
    if not to_summarize:
        return "", 0

    history = build_history(to_summarize)
    summary = await _summarize_messages(history)

    await create_message(
        db,
        task_id=task_id,
        role="compact",
        content=summary,
        parent_id=None,
    )
    await db.commit()
    return summary, len(to_summarize)
