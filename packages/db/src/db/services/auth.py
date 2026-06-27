from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from core.auth.jwt import TokenPayload, create_access_token, create_refresh_token, decode_token
from core.auth.password import hash_password, verify_password
from core.config import get_settings
from core.exceptions import (
    EmailExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.repositories.refresh_token import (
    get_refresh_token,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    store_refresh_token,
)
from db.repositories.user import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    update_user_display_name,
    update_user_password_hash,
)
from db.services.avatar_service import AvatarService


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, email: str, password: str, display_name: str | None = None) -> User:
        existing = await get_user_by_email(self.session, email)
        if existing is not None:
            raise EmailExistsError()
        try:
            user = await create_user(
                self.session,
                email=email,
                password_hash=hash_password(password),
                display_name=display_name,
            )
            # Commit before returning so concurrent duplicate inserts surface as IntegrityError.
            await self.session.commit()
            return user
        except IntegrityError:
            await self.session.rollback()
            raise EmailExistsError() from None

    async def login(self, email: str, password: str) -> User:
        user = await get_user_by_email(self.session, email)
        if user is None or user.password_hash is None:
            raise InvalidCredentialsError()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InvalidCredentialsError()
        if not user.email_verified:
            raise EmailNotVerifiedError()
        await update_last_login(self.session, user.id)
        await self.session.refresh(user)
        return user

    async def refresh(self, refresh_token: str) -> tuple[User, TokenPair]:
        payload: TokenPayload = decode_token(refresh_token, expected_type="refresh")
        if payload.jti is None:
            raise TokenInvalidError()

        stored = await get_refresh_token(self.session, payload.jti)
        if stored is None or stored.revoked:
            raise TokenInvalidError()

        now = datetime.now(UTC)
        if stored.expires_at < now:
            raise TokenExpiredError()

        user = await get_user_by_id(self.session, payload.sub)
        if user is None or not user.is_active or not user.email_verified:
            raise InvalidCredentialsError()

        await revoke_refresh_token(self.session, payload.jti)
        tokens = await self.issue_tokens(user)
        return user, tokens

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except (TokenInvalidError, TokenExpiredError):
            return
        if payload.jti is not None:
            await revoke_refresh_token(self.session, payload.jti)

    async def issue_tokens(self, user: User) -> TokenPair:
        settings = get_settings()
        access_token = create_access_token(user.id, user.email)
        refresh_token, jti = create_refresh_token(user.id)
        expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
        await store_refresh_token(self.session, jti, user.id, expires_at)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def update_profile(self, user: User, display_name: str) -> User:
        return await update_user_display_name(self.session, user.id, display_name)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        from core.exceptions import NoPasswordAuthError

        if user.password_hash is None:
            raise NoPasswordAuthError()
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()
        await update_user_password_hash(self.session, user.id, hash_password(new_password))

    async def delete_account(self, user: User, password: str | None = None) -> None:
        if user.password_hash is not None:
            if password is None or not verify_password(password, user.password_hash):
                raise InvalidCredentialsError()
        await AvatarService(self.session).remove(user)
        await revoke_all_user_refresh_tokens(self.session, user.id)
        await delete_user(self.session, user.id)
