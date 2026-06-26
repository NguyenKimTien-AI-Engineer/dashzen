import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.file import File
from db.models.task import Task

# Deliverables surfaced in the global Artifacts gallery
PUBLISHED_ARTIFACT_NAMES: frozenset[str] = frozenset({"dashboard.html"})


async def _get_file_by_id(db: AsyncSession, file_id: uuid.UUID) -> File | None:
    result = await db.execute(select(File).where(File.id == file_id).limit(1))
    return result.scalar_one_or_none()


async def get_current_file(db: AsyncSession, task_id: uuid.UUID, name: str) -> File | None:
    result = await db.execute(
        select(File)
        .where(File.task_id == task_id, File.name == name, File.is_current.is_(True))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_file_versions(db: AsyncSession, task_id: uuid.UUID, name: str) -> Sequence[File]:
    result = await db.execute(
        select(File).where(File.task_id == task_id, File.name == name).order_by(File.version.asc())
    )
    return result.scalars().all()


async def upsert_workspace_file(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    name: str,
    content: str | None = None,
    kind: str = "text",
    content_type: str | None = None,
    url: str | None = None,
    message_id: uuid.UUID | None = None,
    file_id: uuid.UUID | None = None,
    bump_version: bool = False,
) -> File:
    size = len(content.encode()) if content else 0

    if file_id is not None:
        by_id = await _get_file_by_id(db, file_id)
        if by_id is not None:
            await db.execute(
                update(File)
                .where(File.id == file_id)
                .values(
                    name=name,
                    content=content,
                    kind=kind,
                    content_type=content_type,
                    url=url,
                    size=size,
                    message_id=message_id if message_id else by_id.message_id,
                )
            )
            await db.flush()
            await db.refresh(by_id)
            return by_id

    current = await get_current_file(db, task_id, name)
    if current is not None and bump_version:
        await db.execute(update(File).where(File.id == current.id).values(is_current=False))
        new_version = current.version + 1
        file = File(
            id=file_id or uuid.uuid4(),
            task_id=task_id,
            name=name,
            source="workspace",
            kind=kind,
            content=content,
            content_type=content_type,
            url=url,
            size=size,
            message_id=message_id,
            version=new_version,
            is_current=True,
        )
        db.add(file)
        await db.flush()
        await db.refresh(file)
        return file

    if current is not None:
        await db.execute(
            update(File)
            .where(File.id == current.id)
            .values(
                content=content,
                kind=kind,
                content_type=content_type,
                url=url,
                size=size,
                message_id=message_id if message_id else current.message_id,
            )
        )
        await db.flush()
        await db.refresh(current)
        return current

    file = File(
        id=file_id or uuid.uuid4(),
        task_id=task_id,
        name=name,
        source="workspace",
        kind=kind,
        content=content,
        content_type=content_type,
        url=url,
        size=size,
        message_id=message_id,
        version=1,
        is_current=True,
    )
    db.add(file)
    await db.flush()
    await db.refresh(file)
    return file


async def restore_file_version(
    db: AsyncSession,
    task_id: uuid.UUID,
    file_id: uuid.UUID,
    *,
    message_id: uuid.UUID | None = None,
) -> File | None:
    target = await _get_file_by_id(db, file_id)
    if target is None or target.task_id != task_id:
        return None

    current = await get_current_file(db, task_id, target.name)
    if current is not None and current.id != target.id:
        await db.execute(update(File).where(File.id == current.id).values(is_current=False))

    next_version = (
        max((v.version for v in await get_file_versions(db, task_id, target.name)), default=0) + 1
    )
    restored = File(
        task_id=task_id,
        name=target.name,
        source=target.source,
        kind=target.kind,
        content=target.content,
        content_type=target.content_type,
        url=target.url,
        size=target.size,
        message_id=message_id or target.message_id,
        version=next_version,
        is_current=True,
    )
    db.add(restored)
    await db.flush()
    await db.refresh(restored)
    return restored


async def get_artifacts(db: AsyncSession, task_id: uuid.UUID) -> Sequence[File]:
    result = await db.execute(
        select(File).where(File.task_id == task_id).order_by(File.created_at.asc())
    )
    return result.scalars().all()


async def list_user_artifacts(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    names: frozenset[str] | None = None,
) -> list[tuple[File, Task]]:
    allowed = names or PUBLISHED_ARTIFACT_NAMES
    result = await db.execute(
        select(File, Task)
        .join(Task, File.task_id == Task.id)
        .where(
            Task.user_id == user_id,
            Task.status == "active",
            File.name.in_(allowed),
            File.is_current.is_(True),
            File.content.isnot(None),
            File.content != "",
        )
        .order_by(Task.updated_at.desc())
    )
    return list(result.all())


async def get_user_artifact(
    db: AsyncSession,
    file_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[File, Task] | None:
    result = await db.execute(
        select(File, Task)
        .join(Task, File.task_id == Task.id)
        .where(File.id == file_id, Task.user_id == user_id)
        .limit(1)
    )
    row = result.first()
    return (row[0], row[1]) if row else None


async def get_file(db: AsyncSession, task_id: uuid.UUID, name: str) -> File | None:
    return await get_current_file(db, task_id, name)


async def remap_files_message_id(
    db: AsyncSession,
    file_ids: list[uuid.UUID],
    message_id: uuid.UUID,
) -> None:
    if not file_ids:
        return
    await db.execute(update(File).where(File.id.in_(file_ids)).values(message_id=message_id))
    await db.flush()


def _kind_from_content_type(content_type: str | None) -> str:
    if content_type and content_type.startswith("image/"):
        return "image"
    if content_type == "application/pdf":
        return "binary"
    return "text"


async def save_upload(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    name: str,
    content: bytes | str | None,
    content_type: str | None,
    size: int,
) -> File:
    text_content: str | None
    if isinstance(content, bytes):
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None
    else:
        text_content = content

    kind = _kind_from_content_type(content_type)
    file = File(
        task_id=task_id,
        name=name,
        source="upload",
        kind=kind,
        content=text_content if kind == "text" else None,
        content_type=content_type,
        size=size,
        version=1,
        is_current=True,
    )
    db.add(file)
    await db.flush()
    await db.refresh(file)
    return file
