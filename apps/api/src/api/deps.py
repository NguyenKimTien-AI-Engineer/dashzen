from uuid import UUID

from core.auth.jwt import decode_token
from core.config import get_settings
from core.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeMismatchError,
    UserInactiveError,
)
from db.models.task import Task
from db.models.user import User
from db.repositories.user import get_user_by_id
from db.services.task_service import get_task
from db.session import get_db
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip()


def _extract_access_token(request: Request) -> str | None:
    bearer = _extract_bearer_token(request)
    if bearer:
        return bearer
    return request.cookies.get(get_settings().access_cookie_name)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    token = _extract_access_token(request)
    if not token:
        raise TokenInvalidError()

    try:
        payload = decode_token(token, expected_type="access")
    except TokenExpiredError:
        raise
    except (TokenInvalidError, TokenTypeMismatchError):
        raise TokenInvalidError() from None

    user = await get_user_by_id(session, payload.sub)
    if user is None:
        raise TokenInvalidError()
    if not user.is_active:
        raise UserInactiveError()
    return user


async def get_current_user_id(user: User = Depends(get_current_user)) -> UUID:
    return user.id


async def require_task(
    task_id: UUID,
    user: User,
    db: AsyncSession,
) -> Task:
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
