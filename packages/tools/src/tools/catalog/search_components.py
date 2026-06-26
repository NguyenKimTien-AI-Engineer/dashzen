from __future__ import annotations

import json

from agents.registry.loader import load_widget_catalog
from core.llm.types import ToolDefinition

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="search_components",
    description=(
        "Search the DashZen widget component catalog by keyword or widget type "
        "(kpi, barChart, lineChart, pieChart, table, filterBar)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Search term — widget type id or keyword (e.g. 'kpi', 'chart', 'filter')"
                ),
            },
        },
        "required": ["query"],
    },
)


def _search_catalog(query: str) -> list[dict[str, object]]:
    catalog = load_widget_catalog()
    if not query:
        return catalog

    matches = [
        item
        for item in catalog
        if query in str(item.get("id", "")).lower()
        or query in str(item.get("name", "")).lower()
        or query in str(item.get("category", "")).lower()
        or query in str(item.get("description", "")).lower()
    ]
    return matches or catalog


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    query = str(args.get("query", "")).strip().lower()
    return json.dumps(_search_catalog(query), ensure_ascii=False, indent=2)
