from __future__ import annotations

import uuid

from db.models.user import User
from db.services.project_service import (
    count_project_tasks,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from db.services.task_service import list_tasks
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from api.schemas.tasks import TaskResponse

router = APIRouter(prefix="/v1/projects", tags=["projects"])


async def _require_project(project_id: uuid.UUID, user: User, db: AsyncSession):  # type: ignore[type-arg, return]
    project = await get_project(db, project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _to_response(db: AsyncSession, project) -> ProjectResponse:  # type: ignore[no-untyped-def]
    task_count = await count_project_tasks(db, project.id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        task_count=task_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project_endpoint(
    body: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await create_project(db, user.id, body.name)
    await db.commit()
    await db.refresh(project)
    return await _to_response(db, project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    projects = await list_projects(db, user.id)
    return [await _to_response(db, p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await _require_project(project_id, user, db)
    return await _to_response(db, project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_endpoint(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    await _require_project(project_id, user, db)
    updated = await update_project(db, project_id, user.id, body.name)
    if updated is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.commit()
    return await _to_response(db, updated)


@router.delete("/{project_id}", status_code=204)
async def delete_project_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _require_project(project_id, user, db)
    await delete_project(db, project_id, user.id)
    await db.commit()


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def list_project_tasks_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    await _require_project(project_id, user, db)
    tasks = await list_tasks(db, user.id, project_id=project_id)
    return [TaskResponse.model_validate(t) for t in tasks]
