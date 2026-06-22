from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.jwt import decode_token
from core.config import get_settings
from core.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeMismatchError,
    UserInactiveError,
)
from db.models.user import User
from db.repositories.user import get_user_by_id
from db.session import get_db


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip()


def _extract_access_token(request: Request) -> str | None:
    cookie_token = request.cookies.get(get_settings().access_cookie_name)
    if cookie_token:
        return cookie_token
    return _extract_bearer_token(request)


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
