from core.auth.github_oauth import GitHubProfile
from core.exceptions import GitHubAccountInactiveError, GitHubEmailUnavailableError
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


class GitHubOAuthService:
    PROVIDER = "github"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def authenticate(self, profile: GitHubProfile) -> User:
        if not profile.sub:
            raise GitHubEmailUnavailableError()

        linked = await get_oauth_account(self.session, self.PROVIDER, profile.sub)
        if linked is not None:
            user = await get_user_by_id(self.session, linked.user_id)
            if user is None or not user.is_active:
                raise GitHubAccountInactiveError()
            await update_last_login(self.session, user.id)
            await self.session.commit()
            await self.session.refresh(user)
            return user

        user = await get_user_by_email(self.session, profile.email)
        if user is None:
            user = await create_user(
                self.session,
                email=profile.email,
                password_hash=None,
                display_name=profile.name,
            )
            await mark_email_verified(self.session, user.id)
            await create_oauth_account(
                self.session,
                user_id=user.id,
                provider=self.PROVIDER,
                provider_subject=profile.sub,
                email_at_link=profile.email,
            )
        else:
            if not user.is_active:
                raise GitHubAccountInactiveError()
            existing = await get_oauth_account(self.session, self.PROVIDER, profile.sub)
            if existing is None:
                await create_oauth_account(
                    self.session,
                    user_id=user.id,
                    provider=self.PROVIDER,
                    provider_subject=profile.sub,
                    email_at_link=profile.email,
                )
            if not user.email_verified:
                await mark_email_verified(self.session, user.id)

        await update_last_login(self.session, user.id)
        await self.session.commit()
        await self.session.refresh(user)
        return user
