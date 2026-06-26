from __future__ import annotations

import pytest

from agents.registry.loader import get_agent, load_agent_registry
from agents.tools.pipeline import get_tool_definition
from agents.tools.registry import resolve_agent_tools


def test_load_all_agents_from_registry() -> None:
    agents = load_agent_registry()
    names = {a.name for a in agents}
    assert names == {
        "dashboard-planner",
        "data-binder",
        "layout-designer",
        "dashboard-builder",
        "dashboard-critic",
    }


def test_agent_tools_are_lists_not_strings() -> None:
    for agent in load_agent_registry():
        assert isinstance(agent.tools, list), f"{agent.name}.tools must be a list"
        assert all(isinstance(t, str) for t in agent.tools)


def test_agents_declare_output_file() -> None:
    for agent in load_agent_registry():
        assert agent.output_file.strip(), f"{agent.name} must declare outputFile in frontmatter"


@pytest.mark.parametrize(
    "name,output_file",
    [
        ("dashboard-planner", "spec.md"),
        ("data-binder", "bindings.md"),
        ("layout-designer", "layout.md"),
        ("dashboard-builder", "dashboard.html"),
        ("dashboard-critic", "review.md"),
    ],
)
def test_agent_output_file(name: str, output_file: str) -> None:
    agent = get_agent(name)
    assert agent is not None
    assert agent.output_file == output_file


def test_load_system_tools_from_frontmatter() -> None:
    from agents.registry.loader import load_system_tools

    tools = load_system_tools("main")
    assert "spawn_agent" in tools
    assert "set_memory" in tools
    assert "read_file" in tools


def test_build_orchestrator_tool_definitions() -> None:
    from agents.registry.loader import build_orchestrator_tool_definitions

    defs = build_orchestrator_tool_definitions("main")
    names = {d.name for d in defs}
    assert names == {
        "read_file",
        "write_file",
        "list_file",
        "set_memory",
        "ask_user",
        "spawn_agent",
    }


@pytest.mark.parametrize(
    "name,expected_tools",
    [
        (
            "dashboard-planner",
            {
                "read_file",
                "write_file",
                "list_file",
                "search_components",
                "schema_inspector",
                "csv_preview",
            },
        ),
        (
            "dashboard-builder",
            {"read_file", "write_file", "edit_file", "list_file", "search_components"},
        ),
    ],
)
def test_resolve_agent_tools(name: str, expected_tools: set[str]) -> None:
    agent = get_agent(name)
    assert agent is not None
    resolved = resolve_agent_tools(agent.tools, agent.disallowed_tools)
    assert resolved == expected_tools


def test_coerce_csv_tools_in_frontmatter(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from agents.registry.loader import _load_agent_file

    md = tmp_path / "test-agent.md"
    md.write_text(
        "---\n"
        "name: test-agent\n"
        "displayName: Test\n"
        "tools: read_file, write_file, list_file\n"
        "maxTurns: 5\n"
        "---\n\n"
        "Prompt body.\n",
        encoding="utf-8",
    )
    agent = _load_agent_file(str(md))
    assert agent.tools == ["read_file", "write_file", "list_file"]


def test_agent_tool_definitions_exist_in_pipeline() -> None:
    for agent in load_agent_registry():
        allowed = resolve_agent_tools(agent.tools, agent.disallowed_tools)
        for tool_name in allowed:
            assert get_tool_definition(tool_name) is not None, (
                f"{agent.name} references missing tool: {tool_name}"
            )


def test_load_widget_catalog() -> None:
    from agents.registry.loader import load_widget_catalog

    catalog = load_widget_catalog()
    ids = {item["id"] for item in catalog}
    assert "kpi" in ids
    assert "barChart" in ids
    assert len(catalog) >= 7
