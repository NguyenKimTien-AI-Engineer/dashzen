from __future__ import annotations

from uuid import UUID

from core.config import get_settings
from core.storage.avatar_store import (
    ALLOWED_AVATAR_MIME,
    delete_avatar_file,
    save_avatar_file,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.repositories.user import get_user_by_id, update_user_avatar_key


def build_avatar_url(user: User) -> str | None:
    if not user.avatar_key:
        return None
    base = get_settings().api_public_url.rstrip("/")
    ts = int(user.updated_at.timestamp()) if user.updated_at else 0
    return f"{base}/v1/users/{user.id}/avatar?v={ts}"


class AvatarService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upload(self, user: User, data: bytes, content_type: str) -> User:
        if content_type not in ALLOWED_AVATAR_MIME:
            raise ValueError(f"Unsupported content type: {content_type}")

        key = save_avatar_file(user.id, data, content_type)
        return await update_user_avatar_key(self.session, user.id, key)

    async def remove(self, user: User) -> User:
        delete_avatar_file(user.id, user.avatar_key)
        return await update_user_avatar_key(self.session, user.id, None)

    async def get_public_user(self, user_id: UUID) -> User | None:
        return await get_user_by_id(self.session, user_id)
