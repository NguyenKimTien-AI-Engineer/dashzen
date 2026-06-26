from __future__ import annotations

import re

from core.llm.types import ToolDefinition

from tools.context import ToolContext

_TRAVERSAL = re.compile(r"\.\./|\.\.\\|^/|^\\")

DEFINITION = ToolDefinition(
    name="read_file",
    description="Read the content of a workspace file by name.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File name in workspace (e.g. spec.md)"},
        },
        "required": ["path"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    path: str = args.get("path", "")
    if _TRAVERSAL.search(path):
        return f"[Error] Invalid path: {path}"

    cached = ctx.read_cache.get("read_file", {"path": path})
    if cached is not None and not cached.startswith("[Error]"):
        return cached

    buffered = ctx.artifact_buffer.get(path)
    if buffered is not None:
        ctx.read_cache.set("read_file", {"path": path}, buffered)
        return buffered

    from db.services.file_service import get_file

    file = await get_file(ctx.db, ctx.task_id, path)
    if file is None:
        return f"[Error] File '{path}' not found in workspace."
    result = file.content or ""
    if result.strip():
        ctx.read_cache.set("read_file", {"path": path}, result)
    return result
