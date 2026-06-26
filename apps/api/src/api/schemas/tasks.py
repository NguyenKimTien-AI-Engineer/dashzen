from __future__ import annotations

import uuid
from datetime import datetime

from typing import Literal

from pydantic import BaseModel


class TaskCreate(BaseModel):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    project_id: uuid.UUID | None = None
    starred: bool | None = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    status: str
    type: str | None
    project_id: uuid.UUID | None = None
    starred: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BranchInfo(BaseModel):
    sibling_count: int
    sibling_index: int


class ActivityStepResponse(BaseModel):
    id: str
    kind: str
    label: str
    status: str = "success"
    detail: str = ""


class ActivitySectionResponse(BaseModel):
    id: str
    title: str
    status: str
    steps: list[ActivityStepResponse] = []


class ActivityLogResponse(BaseModel):
    type: Literal["activity_log"] = "activity_log"
    version: int = 1
    header_title: str = ""
    sections: list[ActivitySectionResponse] = []


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    parent_id: uuid.UUID | None
    prompt_tokens: int | None
    created_at: datetime
    branch_info: BranchInfo | None = None
    activity_log: ActivityLogResponse | None = None
    user_feedback: Literal["up", "down"] | None = None

    model_config = {"from_attributes": True}


class FileResponse(BaseModel):
    id: uuid.UUID
    name: str
    source: str
    kind: str
    content: str | None
    size: int
    message_id: uuid.UUID | None = None
    version: int = 1
    is_current: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class StreamRequest(BaseModel):
    message: str = ""
    parent_id: uuid.UUID | None = None
    mode: str = "auto"
    thinking_enabled: bool | None = None
    user_instructions: str = ""
    resume: bool = False
    cursor: int = 0


class RunStatusResponse(BaseModel):
    status: Literal["idle", "running", "done", "error"]
    event_count: int = 0
    started_at: float | None = None


class StopResponse(BaseModel):
    partial_message_id: str | None = None


class MessageActionCreate(BaseModel):
    action: str
    value: str | None = None
    metadata: dict[str, str | int | float | bool | None] | None = None


class MessageActionResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    action: str
    value: str | None = None
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
