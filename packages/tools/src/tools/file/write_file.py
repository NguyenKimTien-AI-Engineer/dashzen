from __future__ import annotations

from core.llm.types import ToolDefinition
from core.security.paths import has_path_separator, sanitize_filename

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="write_file",
    description=(
        "Create or fully overwrite a workspace file with the given content. "
        "Use this once to produce a new artifact file "
        "(spec.md, bindings.md, layout.md, dashboard.html). "
        "For targeted changes to an existing file, use edit_file instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File name (e.g. spec.md). No path separators.",
            },
            "content": {"type": "string", "description": "Complete file content as a string."},
        },
        "required": ["path", "content"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    path: str = args.get("path", "")
    content: str = args.get("content", "")
    if has_path_separator(path):
        return f"[Error] Invalid path: {path}"

    path = sanitize_filename(path)

    from db.services.file_service import get_current_file

    existing = await get_current_file(ctx.db, ctx.task_id, path)
    bump_version = existing is not None
    version = (existing.version + 1) if existing else 1

    staged_id = ctx.artifact_buffer.stage(
        path,
        content,
        bump_version=bump_version,
        version=version,
    )
    ctx.read_cache.invalidate_path(path)
    ctx.read_cache.invalidate_workspace_listing()

    from agents.streaming.events import (
        FileArtifactEvent,  # lazy — shared venv, avoids package-level cycle
    )

    ctx.emit(
        FileArtifactEvent(
            id=str(staged_id),
            name=path,
            content=content,
            version=version,
        )
    )
    return f"File '{path}' written ({len(content)} chars)."
