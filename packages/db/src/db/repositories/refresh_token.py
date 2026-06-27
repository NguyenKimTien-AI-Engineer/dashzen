from datetime import datetime
from uuid import UUID

from db.models.refresh_token import RefreshToken
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


async def store_refresh_token(
    session: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
    session.add(token)
    await session.flush()
    await session.refresh(token)
    return token


async def get_refresh_token(session: AsyncSession, jti: str) -> RefreshToken | None:
    return await session.get(RefreshToken, jti)


async def revoke_refresh_token(session: AsyncSession, jti: str) -> None:
    await session.execute(update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True))
    await session.flush()


async def revoke_all_user_refresh_tokens(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    await session.flush()
