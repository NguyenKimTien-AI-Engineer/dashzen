from __future__ import annotations

import re
import uuid

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memory.state_machine import MemoryState
from agents.registry.loader import load_workflow

_MEMORY_PATH = "memory.md"
DEFAULT_MEMORY_TYPE = "chat"
DEFAULT_MEMORY_PHASE = "create-chat"
_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def format_memory(type_: str, phase: str) -> str:
    return f"---\ntype: {type_}\nphase: {phase}\n---\n"


def default_memory_content() -> str:
    return format_memory(DEFAULT_MEMORY_TYPE, DEFAULT_MEMORY_PHASE)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, text[match.end() :]


async def read_memory(
    db: AsyncSession,
    task_id: uuid.UUID,
    artifact_buffer: object,
) -> MemoryState:
    content = artifact_buffer.get(_MEMORY_PATH)  # type: ignore[union-attr]
    if content is None:
        from db.services.file_service import get_file

        file = await get_file(db, task_id, _MEMORY_PATH)
        content = file.content if file else ""

    if not content:
        return MemoryState(type="chat", phase="")

    frontmatter, _ = parse_frontmatter(content)
    return MemoryState(
        type=str(frontmatter.get("type") or "chat"),
        phase=str(frontmatter.get("phase") or ""),
    )


async def write_memory(
    db: AsyncSession,
    task_id: uuid.UUID,
    type_: str,
    phase: str,
    artifact_buffer: object,
) -> str:
    content = format_memory(type_, phase)
    artifact_buffer.stage(_MEMORY_PATH, content)  # type: ignore[union-attr]
    return load_workflow(type_, phase)
