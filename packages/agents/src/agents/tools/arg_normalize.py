from __future__ import annotations

from typing import Any

from agents.registry.loader import get_agent


def _default_output_path(agent_name: str | None) -> str | None:
    if not agent_name:
        return None
    defn = get_agent(agent_name)
    if defn is None or not defn.output_file.strip():
        return None
    return defn.output_file.strip()

_PATH_ALIASES = ("path", "file", "filename", "file_name", "name", "file_path", "filepath")
_CONTENT_ALIASES = (
    "content",
    "text",
    "body",
    "data",
    "contents",
    "file_content",
    "html",
    "markdown",
    "document",
    "code",
)


def _pick_str(args: dict[str, Any], keys: tuple[str, ...], *, strip: bool = True) -> str | None:
    for key in keys:
        value = args.get(key)
        if not isinstance(value, str):
            continue
        if strip:
            if value.strip():
                return value.strip()
        elif value:
            return value
    return None


def _coerce_args(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        return {}
    return dict(args)


def normalize_tool_args(
    tool_name: str,
    args: dict[str, Any],
    *,
    agent_name: str | None = None,
) -> dict[str, Any]:
    """Map common LLM parameter aliases to tool schema field names."""
    normalized = _coerce_args(args)

    if tool_name in {"read_file", "write_file", "edit_file", "csv_preview", "schema_inspector"}:
        path = _pick_str(normalized, _PATH_ALIASES)
        if path and "path" not in normalized:
            normalized["path"] = path

    if tool_name == "write_file":
        content = _pick_str(normalized, _CONTENT_ALIASES, strip=False)
        if content and "content" not in normalized:
            normalized["content"] = content

        has_path = _pick_str(normalized, ("path",), strip=True)
        if not has_path and agent_name and content:
            default_path = _default_output_path(agent_name)
            if default_path:
                normalized["path"] = default_path

    if tool_name == "edit_file":
        for canonical, aliases in (
            ("old_string", ("old_string", "old", "search", "find")),
            ("new_string", ("new_string", "new", "replace", "replacement")),
        ):
            value = _pick_str(normalized, aliases, strip=False)
            if value and canonical not in normalized:
                normalized[canonical] = value

    if tool_name == "spawn_agent":
        agent = _pick_str(normalized, ("agent", "agent_name", "name"))
        if agent and "agent" not in normalized:
            normalized["agent"] = agent
        task = _pick_str(normalized, ("task", "task_description", "description", "brief"))
        if task and "task" not in normalized:
            normalized["task"] = task

    if tool_name == "set_memory":
        type_ = _pick_str(normalized, ("type", "memory_type", "workflow_type"))
        if type_ and "type" not in normalized:
            normalized["type"] = type_
        phase = _pick_str(normalized, ("phase", "workflow_phase"))
        if phase and "phase" not in normalized:
            normalized["phase"] = phase

    return normalized
