from __future__ import annotations

import uuid

from core.storage.avatar_store import read_avatar_file
from db.services.avatar_service import AvatarService
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("/{user_id}/avatar")
async def get_user_avatar(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = AvatarService(session)
    user = await service.get_public_user(user_id)
    if user is None or not user.avatar_key:
        raise HTTPException(status_code=404, detail="Avatar not found")

    try:
        data, content_type = read_avatar_file(user.avatar_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Avatar not found")

    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )
