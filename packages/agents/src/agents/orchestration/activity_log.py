from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from agents.context.thinking_codec import decode_thinking, encode_thinking
from agents.orchestration.activity_labels import humanize_tool_label
from agents.streaming.events import (
    AgentDoneEvent,
    AgentResultEvent,
    AgentStartEvent,
    AgentTextEvent,
    AgentThinkEvent,
    AgentToolEvent,
    MainResultEvent,
    MainTextEvent,
    MainThinkEvent,
    MainToolEvent,
)

ActivityStepKind = Literal["think", "tool"]
ActivitySectionStatus = Literal["running", "done", "error"]


@dataclass
class ActivityStep:
    id: str
    kind: ActivityStepKind
    label: str
    status: str = "success"
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass
class ActivitySection:
    id: str
    title: str
    status: ActivitySectionStatus = "running"
    steps: list[ActivityStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class ActivityLog:
    header_title: str = ""
    sections: list[ActivitySection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "activity_log",
            "version": 1,
            "header_title": self.header_title,
            "sections": [s.to_dict() for s in self.sections],
        }


def parse_activity_log(thinking_json: str | None) -> ActivityLog | None:
    decoded = decode_thinking(thinking_json)
    if not isinstance(decoded, dict) or decoded.get("type") != "activity_log":
        return None
    sections: list[ActivitySection] = []
    for raw in decoded.get("sections", []):
        if not isinstance(raw, dict):
            continue
        steps = [
            ActivityStep(
                id=str(s.get("id", "")),
                kind=s.get("kind", "tool"),  # type: ignore[arg-type]
                label=str(s.get("label", "")),
                status=str(s.get("status", "success")),
                detail=str(s.get("detail", "")),
            )
            for s in raw.get("steps", [])
            if isinstance(s, dict)
        ]
        sections.append(
            ActivitySection(
                id=str(raw.get("id", "")),
                title=str(raw.get("title", "")),
                status=raw.get("status", "done"),  # type: ignore[arg-type]
                steps=steps,
            )
        )
    return ActivityLog(
        header_title=str(decoded.get("header_title", "")),
        sections=sections,
    )


def encode_activity_log(log: ActivityLog) -> str:
    return encode_thinking(log.to_dict())


class ActivityLogAccumulator:
    """Collects stream events into a Claude-style activity log for persistence."""

    def __init__(self) -> None:
        self._log = ActivityLog()
        self._orchestrator = ActivitySection(id="orchestrator", title="Orchestrator")
        self._log.sections.append(self._orchestrator)
        self._sections_by_call: dict[str, ActivitySection] = {}
        self._think_buffers: dict[str, str] = {}
        self._pending_tools: dict[str, ActivityStep] = {}
        self._main_think_iteration = 0

    def begin_orchestrator_iteration(self, iteration: int) -> None:
        """Start a fresh orchestrator think step so iterations do not merge into one block."""
        self._main_think_iteration = iteration

    def set_header_title(self, title: str) -> None:
        cleaned = title.strip()
        if cleaned:
            self._log.header_title = cleaned

    def _section_for_call(self, call_id: str) -> ActivitySection | None:
        return self._sections_by_call.get(call_id)

    def _append_think_delta(
        self,
        section: ActivitySection,
        buffer_key: str,
        delta: str,
        *,
        step_id: str | None = None,
    ) -> None:
        self._think_buffers[buffer_key] = self._think_buffers.get(buffer_key, "") + delta
        text = self._think_buffers[buffer_key].strip()
        if not text:
            return
        resolved_step_id = step_id or f"{buffer_key}-think"
        for step in section.steps:
            if step.id == resolved_step_id:
                step.detail = text
                return
        section.steps.append(
            ActivityStep(id=resolved_step_id, kind="think", label="", status="success", detail=text)
        )

    def record(self, event: object) -> None:
        if isinstance(event, MainThinkEvent):
            iteration = self._main_think_iteration
            self._append_think_delta(
                self._orchestrator,
                f"main-{iteration}",
                event.delta,
                step_id=f"main-think-{iteration}",
            )
        elif isinstance(event, MainToolEvent):
            label = humanize_tool_label(event.name, event.args)
            self._pending_tools[event.call_id] = ActivityStep(
                id=event.call_id,
                kind="tool",
                label=label,
                status="running",
            )
        elif isinstance(event, MainResultEvent):
            pending = self._pending_tools.pop(event.call_id, None)
            if pending is None:
                pending = ActivityStep(
                    id=event.call_id,
                    kind="tool",
                    label="Tool",
                    status=event.status,
                )
            pending.status = event.status
            pending.detail = event.result[:2000] if event.result else ""
            self._orchestrator.steps.append(pending)
        elif isinstance(event, AgentStartEvent):
            section = ActivitySection(
                id=event.call_id,
                title=event.display_name or event.name,
                status="running",
            )
            self._sections_by_call[event.call_id] = section
            self._log.sections.append(section)
        elif isinstance(event, AgentThinkEvent):
            section = self._section_for_call(event.call_id)
            if section:
                self._append_think_delta(section, event.call_id, event.delta)
        elif isinstance(event, AgentTextEvent):
            section = self._section_for_call(event.call_id)
            if section:
                self._append_think_delta(
                    section,
                    f"{event.call_id}-text",
                    event.delta,
                    step_id=f"{event.call_id}-text",
                )
        elif isinstance(event, AgentToolEvent):
            section = self._section_for_call(event.call_id)
            if section is None:
                return
            label = humanize_tool_label(event.name, event.args)
            self._pending_tools[event.tool_call_id] = ActivityStep(
                id=event.tool_call_id,
                kind="tool",
                label=label,
                status="running",
            )
        elif isinstance(event, AgentResultEvent):
            pending = self._pending_tools.pop(event.tool_call_id, None)
            section = self._section_for_call(event.call_id)
            if section is None:
                return
            if pending is None:
                pending = ActivityStep(
                    id=event.tool_call_id,
                    kind="tool",
                    label="Tool",
                    status=event.status,
                )
            pending.status = event.status
            pending.detail = event.result[:2000] if event.result else ""
            section.steps.append(pending)
        elif isinstance(event, AgentDoneEvent):
            section = self._section_for_call(event.call_id)
            if section is None:
                return
            section.status = "error" if event.status == "error" else "done"
            # agent_text streams the same output as summary — keep one copy only
            text_step_id = f"{event.call_id}-text"
            section.steps = [s for s in section.steps if s.id != text_step_id]
            summary = event.summary.strip()
            if summary:
                section.steps.append(
                    ActivityStep(
                        id=f"{event.call_id}-summary",
                        kind="think",
                        label="",
                        status="success",
                        detail=summary,
                    )
                )
        elif isinstance(event, MainTextEvent):
            pass

    def finalize_orchestrator(self) -> None:
        has_main_think = any(k.startswith("main-") for k in self._think_buffers)
        if self._orchestrator.steps or has_main_think:
            self._orchestrator.status = "done"

    def build(self) -> ActivityLog:
        self.finalize_orchestrator()
        return self._log


def new_step_id() -> str:
    return str(uuid.uuid4())
