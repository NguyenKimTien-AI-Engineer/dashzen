from __future__ import annotations

_READ_ONLY_TOOLS: frozenset[str] = frozenset({
    "read_file",
    "list_file",
    "search_components",
    "schema_inspector",
    "csv_preview",
})
_ASK_BYPASS: frozenset[str] = frozenset({
    *_READ_ONLY_TOOLS,
    "spawn_agent",
    "set_memory",
    "ask_user",
})
_VISIBLE_TOOLS: frozenset[str] = frozenset({
    "write_file",
    "edit_file",
    "spawn_agent",
    "ask_user",
    "schema_inspector",
    "csv_preview",
})
_CONCURRENT_SAFE: frozenset[str] = frozenset({*_READ_ONLY_TOOLS})
_AGENT_TOOLS: frozenset[str] = frozenset({
    "read_file",
    "write_file",
    "list_file",
    "edit_file",
    "search_components",
    "schema_inspector",
    "csv_preview",
})


def is_read_only(name: str) -> bool:
    return name in _READ_ONLY_TOOLS


def is_ask_bypass(name: str) -> bool:
    return name in _ASK_BYPASS


def is_visible(name: str) -> bool:
    return name in _VISIBLE_TOOLS


def is_concurrent_safe(name: str) -> bool:
    return name in _CONCURRENT_SAFE


def get_main_tools() -> frozenset[str]:
    from agents.registry.loader import load_system_tools

    return frozenset(load_system_tools("main"))


def get_agent_tools() -> frozenset[str]:
    return _AGENT_TOOLS


def resolve_agent_tools(
    tools: list[str], disallowed: list[str]
) -> frozenset[str]:
    base = _AGENT_TOOLS if not tools else frozenset(tools) & _AGENT_TOOLS
    return base - frozenset(disallowed)
