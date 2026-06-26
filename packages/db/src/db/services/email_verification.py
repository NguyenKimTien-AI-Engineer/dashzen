from datetime import UTC, datetime, timedelta

from core.auth.otp import (
    generate_verification_code,
    hash_verification_code,
    verify_verification_code,
)
from core.config import get_settings
from core.email.backend import get_email_backend
from core.exceptions import (
    AlreadyVerifiedError,
    InvalidVerificationCodeError,
    TooManyVerificationAttemptsError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.repositories.email_verification import (
    consume_verification_code,
    create_verification_code,
    get_active_verification_code,
    increment_verification_attempts,
    revoke_active_codes_for_user,
)
from db.repositories.user import get_user_by_email, mark_email_verified


class EmailVerificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def send_verification_code(self, user: User) -> None:
        if user.email_verified:
            return

        settings = get_settings()
        plain_code = generate_verification_code()
        code_hash = hash_verification_code(plain_code)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.email_verification_code_ttl_minutes
        )

        await revoke_active_codes_for_user(self.session, user.id)
        await create_verification_code(
            self.session,
            user_id=user.id,
            code_hash=code_hash,
            expires_at=expires_at,
            max_attempts=settings.email_verification_max_attempts,
        )

        backend = get_email_backend(settings)
        await backend.send_verification_code(
            to=user.email,
            code=plain_code,
            expires_minutes=settings.email_verification_code_ttl_minutes,
        )

    async def verify_email(self, email: str, code: str) -> None:
        user = await get_user_by_email(self.session, email)
        if user is None:
            raise InvalidVerificationCodeError()
        if user.email_verified:
            raise AlreadyVerifiedError()

        record = await get_active_verification_code(self.session, user.id)
        if record is None:
            raise InvalidVerificationCodeError()
        if record.attempts >= record.max_attempts:
            raise TooManyVerificationAttemptsError()

        if not verify_verification_code(code, record.code_hash):
            await increment_verification_attempts(self.session, record.id)
            refreshed = await get_active_verification_code(self.session, user.id)
            if refreshed is not None and refreshed.attempts >= refreshed.max_attempts:
                raise TooManyVerificationAttemptsError()
            raise InvalidVerificationCodeError()

        await consume_verification_code(self.session, record.id)
        await mark_email_verified(self.session, user.id)

    async def resend_verification(self, email: str) -> None:
        user = await get_user_by_email(self.session, email)
        if user is None or user.email_verified:
            return
        await self.send_verification_code(user)
