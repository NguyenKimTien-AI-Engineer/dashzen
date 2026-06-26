from __future__ import annotations

import uuid

from agents.memory.memory_file import default_memory_content
from db.models.user import User
from db.services.file_service import (
    get_artifacts,
    get_file_versions,
    restore_file_version,
    upsert_workspace_file,
)
from db.services.message_service import get_messages_enriched
from db.services.message_action_service import (
    create_message_action,
    get_latest_feedback_by_message,
    message_belongs_to_task,
)
from db.services.project_service import get_project
from db.services.task_service import (
    create_task,
    delete_task,
    list_tasks,
    update_task,
)
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_task
from api.rate_limit_deps import enforce_task_create_limit
from api.schemas.tasks import (
    FileResponse,
    MessageActionCreate,
    MessageActionResponse,
    MessageResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task_endpoint(
    _body: TaskCreate,
    user: User = Depends(enforce_task_create_limit),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task = await create_task(db, user.id)
    await upsert_workspace_file(
        db,
        task_id=task.id,
        name="memory.md",
        content=default_memory_content(),
    )
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks_endpoint(
    project_id: uuid.UUID | None = None,
    starred: bool | None = None,
    unassigned: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    tasks = await list_tasks(
        db,
        user.id,
        project_id=project_id,
        starred=starred,
        unassigned=unassigned,
    )
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task = await require_task(task_id, user, db)
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_endpoint(
    task_id: uuid.UUID,
    body: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    await require_task(task_id, user, db)
    data = body.model_dump(exclude_unset=True)
    if "project_id" in data and data["project_id"] is not None:
        if await get_project(db, data["project_id"], user.id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
    updated = await update_task(db, task_id, **data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.commit()
    return TaskResponse.model_validate(updated)


@router.delete("/{task_id}", status_code=204)
async def delete_task_endpoint(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_task(task_id, user, db)
    await delete_task(db, task_id, user.id)
    await db.commit()


@router.get("/{task_id}/messages", response_model=list[MessageResponse])
async def get_messages_endpoint(
    task_id: uuid.UUID,
    leaf_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    await require_task(task_id, user, db)
    messages = await get_messages_enriched(db, task_id, leaf_id=leaf_id)
    feedback_map: dict[uuid.UUID, str] = {}
    try:
        feedback_map = await get_latest_feedback_by_message(
            db,
            task_id=task_id,
            user_id=user.id,
        )
    except Exception:
        feedback_map = {}
    enriched = []
    for m in messages:
        item = dict(m)
        item["user_feedback"] = feedback_map.get(item["id"])
        enriched.append(item)
    return [MessageResponse.model_validate(m) for m in enriched]


@router.post(
    "/{task_id}/messages/{message_id}/actions",
    response_model=MessageActionResponse,
    status_code=201,
)
async def create_message_action_endpoint(
    task_id: uuid.UUID,
    message_id: uuid.UUID,
    body: MessageActionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageActionResponse:
    await require_task(task_id, user, db)
    if not await message_belongs_to_task(db, task_id=task_id, message_id=message_id):
        raise HTTPException(status_code=404, detail="Message not found")

    created = await create_message_action(
        db,
        task_id=task_id,
        message_id=message_id,
        user_id=user.id,
        action=body.action,
        value=body.value,
        metadata_json=body.metadata,
    )
    await db.commit()
    return MessageActionResponse.model_validate(created)


@router.get("/{task_id}/artifacts", response_model=list[FileResponse])
async def get_artifacts_endpoint(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FileResponse]:
    await require_task(task_id, user, db)
    files = await get_artifacts(db, task_id)
    return [FileResponse.model_validate(f) for f in files]


@router.get("/{task_id}/artifacts/{name}/versions", response_model=list[FileResponse])
async def get_artifact_versions_endpoint(
    task_id: uuid.UUID,
    name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FileResponse]:
    await require_task(task_id, user, db)
    files = await get_file_versions(db, task_id, name)
    return [FileResponse.model_validate(f) for f in files]


@router.post(
    "/{task_id}/artifacts/{artifact_id}/restore",
    response_model=FileResponse,
)
async def restore_artifact_version_endpoint(
    task_id: uuid.UUID,
    artifact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    await require_task(task_id, user, db)
    restored = await restore_file_version(db, task_id, artifact_id)
    if restored is None:
        raise HTTPException(status_code=404, detail="Artifact version not found")
    await db.commit()
    return FileResponse.model_validate(restored)
