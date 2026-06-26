from __future__ import annotations

from tools.context import ToolContext


async def read_workspace_file(ctx: ToolContext, path: str) -> str | None:
    content = ctx.artifact_buffer.get(path)
    if content is not None:
        return content
    from db.services.file_service import get_file

    file = await get_file(ctx.db, ctx.task_id, path)
    if file is None:
        return None
    return file.content or ""


async def list_workspace_csv_paths(ctx: ToolContext) -> list[str]:
    paths: set[str] = set()
    for name in ctx.artifact_buffer.keys():
        if name.lower().endswith(".csv"):
            paths.add(name)
    from db.services.file_service import get_artifacts

    for file_row in await get_artifacts(ctx.db, ctx.task_id):
        if file_row.name.lower().endswith(".csv"):
            paths.add(file_row.name)
    return sorted(paths)
