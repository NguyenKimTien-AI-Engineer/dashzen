from typing import Protocol

from core.config import Settings


class EmailBackend(Protocol):
    async def send_verification_code(
        self,
        to: str,
        code: str,
        expires_minutes: int,
    ) -> None: ...


_backend_override: EmailBackend | None = None


def set_email_backend_override(backend: EmailBackend | None) -> None:
    global _backend_override
    _backend_override = backend


def get_email_backend(settings: Settings | None = None) -> EmailBackend:
    if _backend_override is not None:
        return _backend_override

    from core.config import get_settings
    from core.email.console import ConsoleEmailBackend
    from core.email.smtp import SMTPEmailBackend

    settings = settings or get_settings()
    if settings.email_backend == "smtp":
        return SMTPEmailBackend(settings)
    return ConsoleEmailBackend(settings)
