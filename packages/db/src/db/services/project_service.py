import uuid
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.project import Project
from db.models.task import Task


async def create_project(db: AsyncSession, user_id: uuid.UUID, name: str) -> Project:
    project = Project(user_id=user_id, name=name.strip())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def list_projects(db: AsyncSession, user_id: uuid.UUID) -> list[Project]:
    result = await db.execute(
        select(Project).where(Project.user_id == user_id).order_by(Project.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, name: str
) -> Project | None:
    project = await get_project(db, project_id, user_id)
    if project is None:
        return None
    await db.execute(
        update(Project)
        .where(Project.id == project_id)
        .values(name=name.strip(), updated_at=datetime.now())
    )
    await db.flush()
    return await get_project(db, project_id, user_id)


async def delete_project(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        delete(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    return result.rowcount > 0


async def count_project_tasks(db: AsyncSession, project_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.project_id == project_id, Task.status == "active")
    )
    return int(result.scalar_one())
