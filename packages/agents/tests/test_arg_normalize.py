from agents.tools.arg_normalize import normalize_tool_args


def test_write_file_maps_filename_and_text() -> None:
    args = normalize_tool_args(
        "write_file",
        {"filename": "spec.md", "text": "# Spec\n"},
    )
    assert args["path"] == "spec.md"
    assert args["content"] == "# Spec\n"


def test_write_file_keeps_canonical_names() -> None:
    args = normalize_tool_args(
        "write_file",
        {"path": "bindings.md", "content": "data"},
    )
    assert args == {"path": "bindings.md", "content": "data"}


def test_read_file_maps_name_alias() -> None:
    args = normalize_tool_args("read_file", {"name": "layout.md"})
    assert args["path"] == "layout.md"


def test_spawn_agent_maps_aliases() -> None:
    args = normalize_tool_args(
        "spawn_agent",
        {"agent_name": "dashboard-planner", "brief": "Build marketing dashboard"},
    )
    assert args["agent"] == "dashboard-planner"
    assert args["task"] == "Build marketing dashboard"


def test_write_file_maps_html_body_and_defaults_path() -> None:
    args = normalize_tool_args(
        "write_file",
        {"html": "<!DOCTYPE html><html></html>"},
        agent_name="dashboard-builder",
    )
    assert args["path"] == "dashboard.html"
    assert args["content"] == "<!DOCTYPE html><html></html>"
    args = normalize_tool_args(
        "write_file",
        {"content": "<!DOCTYPE html><html></html>"},
        agent_name="dashboard-builder",
    )
    assert args["path"] == "dashboard.html"
    assert args["content"] == "<!DOCTYPE html><html></html>"


def test_write_file_does_not_default_path_without_content() -> None:
    args = normalize_tool_args("write_file", {}, agent_name="dashboard-builder")
    assert "path" not in args


def test_write_file_does_not_default_path_for_orchestrator() -> None:
    args = normalize_tool_args(
        "write_file",
        {"content": "hello"},
        agent_name=None,
    )
    assert "path" not in args
