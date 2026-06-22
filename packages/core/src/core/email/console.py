import logging

from core.config import Settings
from core.email.templates.verification import render_verification_email

logger = logging.getLogger(__name__)


class ConsoleEmailBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification_code(
        self,
        to: str,
        code: str,
        expires_minutes: int,
    ) -> None:
        content = render_verification_email(code, expires_minutes)
        logger.info(
            "Verification email to=%s subject=%s (code not logged in production path)",
            to,
            content.subject,
        )
        print(
            f"\n--- DashZen verification email ---\n"
            f"To: {to}\n"
            f"Subject: {content.subject}\n"
            f"Code: {code}\n"
            f"Expires in: {expires_minutes} minutes\n"
            f"-----------------------------------\n"
        )
