from __future__ import annotations

import re

from core.llm.types import ToolDefinition

from tools.context import ToolContext

_TRAVERSAL = re.compile(r"\.\./|\.\.\\|^/|^\\")

DEFINITION = ToolDefinition(
    name="edit_file",
    description=(
        "Modify an existing workspace file by replacing one specific text block with another. "
        "Use this instead of write_file when making targeted changes to a file that already exists. "
        "Read the file first to get the exact text — old_string must match character-for-character."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File name (e.g. dashboard.html). No path separators."},
            "old_string": {
                "type": "string",
                "description": "Exact text to find and replace — must match the file content exactly, including whitespace and newlines. Read the file first.",
            },
            "new_string": {
                "type": "string",
                "description": "Text to replace old_string with. Use an empty string to delete old_string.",
            },
        },
        "required": ["path", "old_string", "new_string"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    path: str = args.get("path", "")
    old_string: str = args.get("old_string", "")
    new_string: str = args.get("new_string", "")

    if _TRAVERSAL.search(path):
        return f"[Error] Invalid path: {path}"
    if not old_string:
        return "[Error] old_string must not be empty."

    content = ctx.artifact_buffer.get(path)
    existing = None
    if content is None:
        from db.services.file_service import get_current_file

        existing = await get_current_file(ctx.db, ctx.task_id, path)
        if existing is None:
            return f"[Error] File '{path}' not found in workspace."
        content = existing.content or ""
    else:
        from db.services.file_service import get_current_file

        existing = await get_current_file(ctx.db, ctx.task_id, path)

    if old_string not in content:
        return f"[Error] old_string not found in '{path}'."

    updated = content.replace(old_string, new_string, 1)
    version = (existing.version + 1) if existing else 2
    staged_id = ctx.artifact_buffer.stage(
        path,
        updated,
        bump_version=True,
        version=version,
    )
    ctx.read_cache.invalidate_path(path)
    ctx.read_cache.invalidate_workspace_listing()

    from agents.streaming.events import FileArtifactEvent

    ctx.emit(
        FileArtifactEvent(
            id=str(staged_id),
            name=path,
            content=updated,
            version=version,
        )
    )
    return f"File '{path}' patched ({len(updated)} chars)."
