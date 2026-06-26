from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class _StagedFile:
    id: uuid.UUID
    content: str
    kind: str = "text"
    content_type: str | None = None
    bump_version: bool = False
    version: int = 1


class ArtifactBuffer:
    def __init__(self) -> None:
        self._staged: dict[str, _StagedFile] = {}
        self._staged_ids: list[uuid.UUID] = []

    def stage(
        self,
        name: str,
        content: str,
        *,
        kind: str = "text",
        content_type: str | None = None,
        file_id: uuid.UUID | None = None,
        bump_version: bool = False,
        version: int = 1,
    ) -> uuid.UUID:
        existing = self._staged.get(name)
        if existing is not None and existing.bump_version:
            fid = existing.id
        elif bump_version:
            fid = uuid.uuid4()
        else:
            fid = file_id or (existing.id if existing else uuid.uuid4())
        next_version = version
        next_bump = bump_version or (existing.bump_version if existing else False)
        if existing is not None:
            next_version = max(existing.version, version)
        self._staged[name] = _StagedFile(
            id=fid,
            content=content,
            kind=kind,
            content_type=content_type,
            bump_version=next_bump,
            version=next_version,
        )
        if fid not in self._staged_ids:
            self._staged_ids.append(fid)
        return fid

    def get(self, name: str) -> str | None:
        entry = self._staged.get(name)
        return entry.content if entry else None

    def get_staged(self, name: str) -> _StagedFile | None:
        return self._staged.get(name)

    def has(self, name: str) -> bool:
        return name in self._staged

    def keys(self) -> list[str]:
        return list(self._staged.keys())

    def items(self) -> list[tuple[str, _StagedFile]]:
        return list(self._staged.items())

    def staged_file_ids(self) -> list[uuid.UUID]:
        return list(self._staged_ids)

    def clear(self) -> None:
        self._staged.clear()
        self._staged_ids.clear()

    async def flush(
        self,
        db: object,
        task_id: uuid.UUID,
        message_id: uuid.UUID | None = None,
    ) -> None:
        await self._persist_staged(db, task_id, message_id)
        self._staged.clear()

    async def persist_staged(
        self,
        db: object,
        task_id: uuid.UUID,
        message_id: uuid.UUID | None = None,
    ) -> None:
        """Write staged files to DB without clearing the in-memory buffer."""
        await self._persist_staged(db, task_id, message_id)

    async def _persist_staged(
        self,
        db: object,
        task_id: uuid.UUID,
        message_id: uuid.UUID | None,
    ) -> list[uuid.UUID]:
        from db.services.file_service import upsert_workspace_file

        persisted_ids: list[uuid.UUID] = []
        for name, entry in self._staged.items():
            row = await upsert_workspace_file(
                db,  # type: ignore[arg-type]
                task_id=task_id,
                name=name,
                content=entry.content,
                kind=entry.kind,
                content_type=entry.content_type,
                message_id=message_id,
                file_id=entry.id,
                bump_version=entry.bump_version,
            )
            persisted_ids.append(row.id)
        return persisted_ids

    async def flush_and_remap(
        self,
        db: object,
        task_id: uuid.UUID,
        message_id: uuid.UUID | None,
    ) -> list[uuid.UUID]:
        from db.services.file_service import remap_files_message_id

        persisted_ids = await self._persist_staged(db, task_id, message_id)
        if message_id is not None and persisted_ids:
            await remap_files_message_id(
                db,  # type: ignore[arg-type]
                persisted_ids,
                message_id,
            )
        self._staged.clear()
        self._staged_ids.clear()
        return persisted_ids
