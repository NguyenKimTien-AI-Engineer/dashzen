from __future__ import annotations

import csv
import io
import json
import re

from core.llm.types import ToolDefinition

from tools.context import ToolContext
from tools.data.csv_inference import infer_columns_from_csv
from tools.data.workspace_io import read_workspace_file

_TRAVERSAL = re.compile(r"\.\./|\.\.\\|^/|^\\")
_MAX_ROWS = 20

DEFINITION = ToolDefinition(
    name="csv_preview",
    description="Preview an uploaded CSV file: columns, inferred types, and sample rows.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "CSV file name in workspace (upload source)",
            },
        },
        "required": ["path"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    path: str = args.get("path", "")
    if _TRAVERSAL.search(path):
        return f"[Error] Invalid path: {path}"

    content = await read_workspace_file(ctx, path)
    if content is None:
        return f"[Error] File '{path}' not found."
    if not content.strip():
        return f"[Error] File '{path}' is empty."

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return f"[Error] No rows in '{path}'."

    headers = rows[0]
    data_rows = rows[1 : _MAX_ROWS + 1]
    columns = infer_columns_from_csv(content, sample_rows=_MAX_ROWS)

    preview = {
        "path": path,
        "columns": columns,
        "row_count": max(0, len(rows) - 1),
        "preview_rows": [dict(zip(headers, row, strict=False)) for row in data_rows],
    }
    return json.dumps(preview, ensure_ascii=False, indent=2)
