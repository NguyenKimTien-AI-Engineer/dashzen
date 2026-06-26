from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ArtifactListItem(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    size: int
    task_id: uuid.UUID
    task_title: str | None
    task_type: str | None
    created_at: datetime
    edited_at: datetime


class ArtifactDetailResponse(ArtifactListItem):
    content: str | None
    source: str

    model_config = {"from_attributes": True}
