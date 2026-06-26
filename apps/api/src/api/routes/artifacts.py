from __future__ import annotations

import uuid

from db.models.user import User
from db.services.file_service import get_user_artifact, list_user_artifacts
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas.artifacts import ArtifactDetailResponse, ArtifactListItem

router = APIRouter(prefix="/v1/artifacts", tags=["artifacts"])


def _to_list_item(file_row, task) -> ArtifactListItem:  # type: ignore[no-untyped-def]
    return ArtifactListItem(
        id=file_row.id,
        name=file_row.name,
        kind=file_row.kind,
        size=file_row.size,
        task_id=task.id,
        task_title=task.title,
        task_type=task.type,
        created_at=file_row.created_at,
        edited_at=task.updated_at,
    )


@router.get("", response_model=list[ArtifactListItem])
async def list_artifacts_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactListItem]:
    rows = await list_user_artifacts(db, user.id)
    return [_to_list_item(f, t) for f, t in rows]


@router.get("/{artifact_id}", response_model=ArtifactDetailResponse)
async def get_artifact_endpoint(
    artifact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactDetailResponse:
    row = await get_user_artifact(db, artifact_id, user.id)
    if row is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    file_row, task = row
    base = _to_list_item(file_row, task)
    return ArtifactDetailResponse(
        **base.model_dump(),
        content=file_row.content,
        source=file_row.source,
    )
