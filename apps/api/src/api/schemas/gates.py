from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ToolGateRequest(BaseModel):
    call_id: str
    approved: bool
    feedback: str | None = None


class AskGateRequest(BaseModel):
    call_id: str
    answer: str


class GateResolveResponse(BaseModel):
    resolved: bool


class UploadResponse(BaseModel):
    id: uuid.UUID
    name: str
    source: str
    kind: str
    size: int
    content_type: str | None = None


class CompactResponse(BaseModel):
    summary: str
    messages_removed: int
