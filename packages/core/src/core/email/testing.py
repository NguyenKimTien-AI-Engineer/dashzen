from dataclasses import dataclass, field

from core.email.templates.verification import render_verification_email


@dataclass
class InMemoryEmailBackend:
    messages: list[dict[str, str | int]] = field(default_factory=list)

    async def send_verification_code(
        self,
        to: str,
        code: str,
        expires_minutes: int,
    ) -> None:
        content = render_verification_email(code, expires_minutes)
        self.messages.append(
            {
                "to": to,
                "code": code,
                "expires_minutes": expires_minutes,
                "subject": content.subject,
            }
        )

    @property
    def last_code(self) -> str | None:
        if not self.messages:
            return None
        code = self.messages[-1]["code"]
        return str(code) if code is not None else None
