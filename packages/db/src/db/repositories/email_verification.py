from datetime import UTC, datetime
from uuid import UUID

from db.models.email_verification import EmailVerificationCode
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def revoke_active_codes_for_user(session: AsyncSession, user_id: UUID) -> None:
    now = datetime.now(UTC)
    await session.execute(
        update(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user_id,
            EmailVerificationCode.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    await session.flush()


async def create_verification_code(
    session: AsyncSession,
    user_id: UUID,
    code_hash: str,
    expires_at: datetime,
    max_attempts: int,
) -> EmailVerificationCode:
    record = EmailVerificationCode(
        user_id=user_id,
        code_hash=code_hash,
        expires_at=expires_at,
        max_attempts=max_attempts,
    )
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record


async def get_active_verification_code(
    session: AsyncSession,
    user_id: UUID,
) -> EmailVerificationCode | None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.user_id == user_id,
            EmailVerificationCode.consumed_at.is_(None),
            EmailVerificationCode.expires_at > now,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def increment_verification_attempts(
    session: AsyncSession,
    code_id: UUID,
) -> None:
    record = await session.get(EmailVerificationCode, code_id)
    if record is None:
        return
    record.attempts += 1
    await session.flush()
    # Persist attempt count even when verify_email raises InvalidVerificationCodeError
    # and get_db rolls back the surrounding transaction.
    await session.commit()


async def consume_verification_code(session: AsyncSession, code_id: UUID) -> None:
    await session.execute(
        update(EmailVerificationCode)
        .where(EmailVerificationCode.id == code_id)
        .values(consumed_at=datetime.now(UTC))
    )
    await session.flush()
