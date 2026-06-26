from __future__ import annotations

import json
import re
from typing import Any

from core.llm.types import ToolDefinition

from tools.context import ToolContext
from tools.data.csv_inference import infer_columns_from_csv, table_name_from_path
from tools.data.workspace_io import list_workspace_csv_paths, read_workspace_file

_TRAVERSAL = re.compile(r"\.\./|\.\.\\|^/|^\\")

DEFINITION = ToolDefinition(
    name="schema_inspector",
    description="Return the data source schema (tables, columns, types) from workspace CSV files.",
    parameters={
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "CSV file name in workspace (optional — all CSVs when omitted)",
            },
        },
        "required": [],
    },
)


async def _table_from_csv(ctx: ToolContext, path: str) -> dict[str, Any] | None:
    content = await read_workspace_file(ctx, path)
    if content is None or not content.strip():
        return None
    columns = infer_columns_from_csv(content)
    if not columns:
        return None
    return {
        "name": table_name_from_path(path),
        "path": path,
        "columns": columns,
    }


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    source = str(args.get("source", "")).strip()
    if source:
        if _TRAVERSAL.search(source):
            return f"[Error] Invalid path: {source}"
        table = await _table_from_csv(ctx, source)
        if table is None:
            return f"[Error] CSV '{source}' not found or empty."
        payload = {"source": source, "tables": [table]}
        return json.dumps(payload, ensure_ascii=False, indent=2)

    tables: list[dict[str, Any]] = []
    for path in await list_workspace_csv_paths(ctx):
        table = await _table_from_csv(ctx, path)
        if table is not None:
            tables.append(table)

    payload = {"source": "workspace", "tables": tables}
    return json.dumps(payload, ensure_ascii=False, indent=2)
