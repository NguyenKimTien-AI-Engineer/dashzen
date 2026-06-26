from __future__ import annotations

import json

from core.llm.types import ToolDefinition

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="list_file",
    description="List all files in the task workspace.",
    parameters={"type": "object", "properties": {}, "required": []},
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    from db.services.file_service import get_artifacts

    db_files = await get_artifacts(ctx.db, ctx.task_id)
    result = []

    for f in db_files:
        if f.name not in ctx.artifact_buffer.keys():
            result.append(
                {
                    "name": f.name,
                    "size": f.size,
                    "kind": f.kind,
                }
            )

    for name in ctx.artifact_buffer.keys():
        content = ctx.artifact_buffer.get(name) or ""
        result.append(
            {
                "name": name,
                "size": len(content.encode()),
                "kind": "text",
                "staged": True,
            }
        )

    return json.dumps(result, ensure_ascii=False)
