import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from core.config import Settings
from core.email.templates.verification import render_verification_email

logger = logging.getLogger(__name__)


class SMTPEmailBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification_code(
        self,
        to: str,
        code: str,
        expires_minutes: int,
    ) -> None:
        content = render_verification_email(code, expires_minutes)
        message = MIMEMultipart("alternative")
        message["From"] = self._settings.email_from
        message["To"] = to
        message["Subject"] = content.subject
        message.attach(MIMEText(content.text_body, "plain", "utf-8"))
        message.attach(MIMEText(content.html_body, "html", "utf-8"))

        await aiosmtplib.send(
            message,
            hostname=self._settings.smtp_host,
            port=self._settings.smtp_port,
            username=self._settings.smtp_user or None,
            password=self._settings.smtp_password or None,
            start_tls=self._settings.smtp_tls,
            use_tls=self._settings.smtp_ssl,
        )
        logger.info("Verification email sent to=%s", to)
