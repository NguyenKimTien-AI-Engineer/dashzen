from __future__ import annotations

from agents.orchestration.agent_status import (
    format_agent_tool_result,
    parse_agent_status_block,
)
from agents.orchestration.spawn import _resolve_spawn_result


def test_parse_agent_status_block() -> None:
    text = "**Status:** DONE\n**Summary:** Wrote spec.md with 4 widgets."
    parsed = parse_agent_status_block(text)
    assert parsed == ("DONE", "Wrote spec.md with 4 widgets.")


def test_parse_agent_status_block_case_insensitive() -> None:
    text = "**Status:** wait\n**Summary:** Need CSV upload."
    parsed = parse_agent_status_block(text)
    assert parsed == ("WAIT", "Need CSV upload.")


def test_parse_agent_status_block_missing() -> None:
    assert parse_agent_status_block("All done.") is None


def test_format_agent_tool_result() -> None:
    assert format_agent_tool_result("done", "ok") == "**Status:** DONE\n**Summary:** ok"


def test_resolve_spawn_result_prefers_status_block() -> None:
    output = "**Status:** WAIT\n**Summary:** Missing spec.md."
    event_status, agent_status, summary = _resolve_spawn_result(
        output,
        timed_out=False,
        activities=[],
    )
    assert event_status == "done"
    assert agent_status == "WAIT"
    assert summary == "Missing spec.md."


def test_resolve_spawn_result_timeout() -> None:
    event_status, agent_status, summary = _resolve_spawn_result(
        "",
        timed_out=True,
        activities=[],
    )
    assert event_status == "timeout"
    assert agent_status == "FAIL"
    assert "timed out" in summary.lower()


def test_resolve_spawn_result_fails_without_block() -> None:
    event_status, agent_status, summary = _resolve_spawn_result(
        "",
        timed_out=False,
        activities=[],
    )
    assert event_status == "error"
    assert agent_status == "FAIL"
    assert "No status block" in summary
