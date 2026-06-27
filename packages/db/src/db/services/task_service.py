import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.task import Task


async def create_task(db: AsyncSession, user_id: uuid.UUID) -> Task:
    task = Task(user_id=user_id)
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def list_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    project_id: uuid.UUID | None = None,
    starred: bool | None = None,
    unassigned: bool = False,
) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id, Task.status == "active")
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    elif unassigned:
        stmt = stmt.where(Task.project_id.is_(None))
    if starred is not None:
        stmt = stmt.where(Task.starred.is_(starred))
    stmt = stmt.order_by(Task.updated_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id))
    return result.scalar_one_or_none()


async def update_task(db: AsyncSession, task_id: uuid.UUID, **fields: object) -> Task | None:
    allowed = {"title", "status", "type", "project_id", "starred"}
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return None
    filtered["updated_at"] = datetime.now(UTC)  # type: ignore[assignment]
    await db.execute(update(Task).where(Task.id == task_id).values(**filtered))
    await db.flush()
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def delete_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(delete(Task).where(Task.id == task_id, Task.user_id == user_id))
    return result.rowcount > 0


async def set_title_if_untitled(db: AsyncSession, task_id: uuid.UUID, title: str) -> None:
    await db.execute(
        update(Task).where(Task.id == task_id, Task.title.is_(None)).values(title=title)
    )
    await db.flush()


async def sync_task_type_if_upgrade(db: AsyncSession, task_id: uuid.UUID, new_type: str) -> bool:
    from sqlalchemy import or_

    result = await db.execute(
        update(Task)
        .where(
            Task.id == task_id,
            or_(Task.type.is_(None), Task.type == "chat"),
        )
        .values(type=new_type)
    )
    await db.flush()
    return result.rowcount > 0
