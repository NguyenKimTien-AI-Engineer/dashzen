from core.auth.google_oauth import GoogleClaims
from core.exceptions import GoogleEmailUnverifiedError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.repositories.oauth_account import create_oauth_account, get_oauth_account
from db.repositories.user import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    mark_email_verified,
    update_last_login,
)


class GoogleOAuthService:
    PROVIDER = "google"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def authenticate(self, claims: GoogleClaims) -> User:
        if not claims.sub:
            raise GoogleEmailUnverifiedError()
        if not claims.email_verified:
            raise GoogleEmailUnverifiedError()

        linked = await get_oauth_account(self.session, self.PROVIDER, claims.sub)
        if linked is not None:
            user = await get_user_by_id(self.session, linked.user_id)
            if user is None or not user.is_active:
                raise GoogleEmailUnverifiedError()
            await update_last_login(self.session, user.id)
            await self.session.commit()
            await self.session.refresh(user)
            return user

        user = await get_user_by_email(self.session, claims.email)
        if user is None:
            user = await create_user(
                self.session,
                email=claims.email,
                password_hash=None,
                display_name=claims.name,
            )
            await mark_email_verified(self.session, user.id)
            await create_oauth_account(
                self.session,
                user_id=user.id,
                provider=self.PROVIDER,
                provider_subject=claims.sub,
                email_at_link=claims.email,
            )
        else:
            if not user.is_active:
                raise GoogleEmailUnverifiedError()
            existing = await get_oauth_account(self.session, self.PROVIDER, claims.sub)
            if existing is None:
                await create_oauth_account(
                    self.session,
                    user_id=user.id,
                    provider=self.PROVIDER,
                    provider_subject=claims.sub,
                    email_at_link=claims.email,
                )
            if not user.email_verified:
                await mark_email_verified(self.session, user.id)

        await update_last_login(self.session, user.id)
        await self.session.commit()
        await self.session.refresh(user)
        return user


async def build_auth_providers(session: AsyncSession, user: User) -> list[str]:
    from db.repositories.oauth_account import list_oauth_providers

    providers: list[str] = []
    if user.password_hash is not None:
        providers.append("password")
    providers.extend(await list_oauth_providers(session, user.id))
    return providers
