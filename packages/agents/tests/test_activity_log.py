from agents.orchestration.activity_log import (
    ActivityLogAccumulator,
    encode_activity_log,
    parse_activity_log,
)
from agents.streaming.events import (
    AgentDoneEvent,
    AgentResultEvent,
    AgentStartEvent,
    AgentTextEvent,
    AgentThinkEvent,
    AgentToolEvent,
    MainResultEvent,
    MainThinkEvent,
    MainToolEvent,
)


def test_activity_log_roundtrip() -> None:
    acc = ActivityLogAccumulator()
    acc.record(MainToolEvent(call_id="t1", name="set_memory", args={}))
    acc.record(MainResultEvent(call_id="t1", status="success", result="ok"))
    acc.record(
        AgentStartEvent(
            call_id="a1",
            name="dashboard-planner",
            display_name="Dashboard Planner",
        )
    )
    acc.record(
        AgentToolEvent(
            call_id="a1",
            tool_call_id="at1",
            name="write_file",
            args={"path": "spec.md"},
        )
    )
    acc.record(
        AgentResultEvent(
            call_id="a1",
            tool_call_id="at1",
            status="success",
            result="written",
        )
    )
    acc.record(AgentDoneEvent(call_id="a1", status="done", summary="Spec ready"))
    acc.set_header_title("Revenue dashboard by region")

    encoded = encode_activity_log(acc.build())
    parsed = parse_activity_log(encoded)
    assert parsed is not None
    assert parsed.header_title == "Revenue dashboard by region"
    assert len(parsed.sections) >= 2
    planner = next(s for s in parsed.sections if s.id == "a1")
    assert planner.title == "Dashboard Planner"
    assert planner.status == "done"
    assert any(step.label == "Write spec.md" for step in planner.steps)


def test_activity_log_records_thinking_deltas() -> None:
    acc = ActivityLogAccumulator()
    acc.begin_orchestrator_iteration(0)
    acc.record(MainThinkEvent(delta="Planning dashboard layout. "))
    acc.record(MainThinkEvent(delta="Choosing bar chart by region."))
    acc.record(
        AgentStartEvent(
            call_id="a1",
            name="dashboard-planner",
            display_name="Dashboard Planner",
        )
    )
    acc.record(AgentThinkEvent(call_id="a1", delta="Reviewing spec requirements."))

    encoded = encode_activity_log(acc.build())
    parsed = parse_activity_log(encoded)
    assert parsed is not None

    orchestrator = next(s for s in parsed.sections if s.id == "orchestrator")
    main_think = [s for s in orchestrator.steps if s.kind == "think"]
    assert len(main_think) == 1
    assert "bar chart by region" in main_think[0].detail

    planner = next(s for s in parsed.sections if s.id == "a1")
    agent_think = [s for s in planner.steps if s.kind == "think"]
    assert len(agent_think) == 1
    assert "spec requirements" in agent_think[0].detail


def test_activity_log_splits_orchestrator_think_by_iteration() -> None:
    acc = ActivityLogAccumulator()
    acc.begin_orchestrator_iteration(0)
    acc.record(MainThinkEvent(delta="Plan A. "))
    acc.record(MainToolEvent(call_id="t1", name="list_file", args={}))
    acc.record(MainResultEvent(call_id="t1", status="success", result="[]"))
    acc.begin_orchestrator_iteration(1)
    acc.record(MainThinkEvent(delta="Plan B."))

    encoded = encode_activity_log(acc.build())
    parsed = parse_activity_log(encoded)
    assert parsed is not None

    orchestrator = next(s for s in parsed.sections if s.id == "orchestrator")
    main_think = [s for s in orchestrator.steps if s.kind == "think"]
    assert len(main_think) == 2
    assert "Plan A" in main_think[0].detail
    assert "Plan B" in main_think[1].detail


def test_agent_done_dedupes_streamed_text_summary() -> None:
    acc = ActivityLogAccumulator()
    acc.record(
        AgentStartEvent(
            call_id="a1",
            name="data-binder",
            display_name="Data Binder",
        )
    )
    summary = "**Status:** DONE\n**Summary:** Created bindings.md"
    acc.record(AgentTextEvent(call_id="a1", delta=summary))
    acc.record(AgentDoneEvent(call_id="a1", status="done", summary=summary))

    encoded = encode_activity_log(acc.build())
    parsed = parse_activity_log(encoded)
    assert parsed is not None
    binder = next(s for s in parsed.sections if s.id == "a1")
    think_steps = [step for step in binder.steps if step.kind == "think"]
    assert len(think_steps) == 1
    assert think_steps[0].detail == summary
