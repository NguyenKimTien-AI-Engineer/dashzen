from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(
    session: AsyncSession,
    email: str,
    password_hash: str,
    display_name: str | None = None,
) -> User:
    user = User(email=email.lower(), password_hash=password_hash, display_name=display_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_last_login(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(last_login_at=datetime.now(UTC))
    )
    await session.commit()


async def mark_email_verified(session: AsyncSession, user_id: UUID) -> None:
    now = datetime.now(UTC)
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(email_verified=True, email_verified_at=now)
    )
    await session.commit()


async def update_user_display_name(
    session: AsyncSession, user_id: UUID, display_name: str
) -> User:
    await session.execute(
        update(User).where(User.id == user_id).values(display_name=display_name)
    )
    await session.commit()
    user = await get_user_by_id(session, user_id)
    assert user is not None
    return user


async def update_user_password_hash(
    session: AsyncSession, user_id: UUID, password_hash: str
) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(password_hash=password_hash)
    )
    await session.commit()


async def delete_user(session: AsyncSession, user_id: UUID) -> None:
    user = await get_user_by_id(session, user_id)
    if user is None:
        return
    await session.delete(user)
    await session.commit()
