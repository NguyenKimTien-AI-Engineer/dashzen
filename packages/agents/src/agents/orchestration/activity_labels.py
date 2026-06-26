from __future__ import annotations

from typing import Any

# Studio activity log labels — not assistant chat copy.
_TOOL_LABELS: dict[str, str] = {
    "read_file": "Read file",
    "write_file": "Write file",
    "edit_file": "Edit file",
    "list_file": "List workspace files",
    "set_memory": "Configure workflow memory",
    "csv_preview": "Preview CSV data",
    "schema_inspector": "Inspect data schema",
    "search_components": "Search UI components",
    "spawn_agent": "Run agent",
    "ask_user": "Ask user",
}


def humanize_tool_label(name: str, args: dict[str, Any]) -> str:
    path = args.get("path")
    path_str = path if isinstance(path, str) else ""
    agent = args.get("agent")
    agent_str = agent if isinstance(agent, str) else ""

    if name == "read_file" and path_str:
        return f"Read {path_str}"
    if name == "write_file" and path_str:
        return f"Write {path_str}"
    if name == "edit_file" and path_str:
        return f"Edit {path_str}"
    if name == "spawn_agent" and agent_str:
        return f"Run {agent_str}"
    return _TOOL_LABELS.get(name, name.replace("_", " "))
