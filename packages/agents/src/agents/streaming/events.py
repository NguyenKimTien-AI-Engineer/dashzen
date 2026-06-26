from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class MainTextEvent(BaseModel):
    type: Literal["main_text"] = "main_text"
    delta: str


class MainThinkEvent(BaseModel):
    type: Literal["main_think"] = "main_think"
    delta: str


class MainToolEvent(BaseModel):
    type: Literal["main_tool"] = "main_tool"
    call_id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class MainResultEvent(BaseModel):
    type: Literal["main_result"] = "main_result"
    call_id: str
    status: Literal["success", "rejected", "error"]
    result: str


class MainAskEvent(BaseModel):
    type: Literal["main_ask"] = "main_ask"
    call_id: str
    question: str


class AgentStartEvent(BaseModel):
    type: Literal["agent_start"] = "agent_start"
    call_id: str
    name: str
    display_name: str


class AgentTextEvent(BaseModel):
    type: Literal["agent_text"] = "agent_text"
    call_id: str
    delta: str


class AgentThinkEvent(BaseModel):
    type: Literal["agent_think"] = "agent_think"
    call_id: str
    delta: str


class AgentToolEvent(BaseModel):
    type: Literal["agent_tool"] = "agent_tool"
    call_id: str
    tool_call_id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class AgentResultEvent(BaseModel):
    type: Literal["agent_result"] = "agent_result"
    call_id: str
    tool_call_id: str
    status: Literal["success", "rejected", "error"]
    result: str


class AgentDoneEvent(BaseModel):
    type: Literal["agent_done"] = "agent_done"
    call_id: str
    status: str
    summary: str


class FileArtifactEvent(BaseModel):
    type: Literal["file_artifact"] = "file_artifact"
    id: str
    name: str
    content: str
    kind: str = "text"
    version: int = 1


class TaskMetaEvent(BaseModel):
    type: Literal["task_meta"] = "task_meta"
    title: str | None = None
    task_type: str | None = None


class HeartbeatEvent(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"


class StreamDoneEvent(BaseModel):
    type: Literal["stream_done"] = "stream_done"
    partial_message_id: str | None = None


class StreamErrorEvent(BaseModel):
    type: Literal["stream_error"] = "stream_error"
    message: str


StreamEvent = Annotated[
    MainTextEvent
    | MainThinkEvent
    | MainToolEvent
    | MainResultEvent
    | MainAskEvent
    | AgentStartEvent
    | AgentTextEvent
    | AgentThinkEvent
    | AgentToolEvent
    | AgentResultEvent
    | AgentDoneEvent
    | FileArtifactEvent
    | TaskMetaEvent
    | HeartbeatEvent
    | StreamDoneEvent
    | StreamErrorEvent,
    Field(discriminator="type"),
]


def serialize_sse(event: BaseModel) -> str:
    return f"data: {event.model_dump_json()}\n\n"
