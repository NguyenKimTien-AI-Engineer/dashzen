from uuid import UUID

from db.models.oauth_account import OAuthAccount
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_oauth_account(
    session: AsyncSession,
    provider: str,
    provider_subject: str,
) -> OAuthAccount | None:
    result = await session.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_subject == provider_subject,
        )
    )
    return result.scalar_one_or_none()


async def list_oauth_providers(session: AsyncSession, user_id: UUID) -> list[str]:
    result = await session.execute(
        select(OAuthAccount.provider).where(OAuthAccount.user_id == user_id)
    )
    return sorted({row[0] for row in result.all()})


async def create_oauth_account(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: str,
    provider_subject: str,
    email_at_link: str | None,
) -> OAuthAccount:
    record = OAuthAccount(
        user_id=user_id,
        provider=provider,
        provider_subject=provider_subject,
        email_at_link=email_at_link,
    )
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record
