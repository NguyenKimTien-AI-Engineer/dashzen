from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt
from core.config import Settings, get_settings
from core.exceptions import TokenExpiredError, TokenInvalidError, TokenTypeMismatchError

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class TokenPayload:
    sub: UUID
    email: str
    token_type: TokenType
    jti: str | None = None


def _signing_key(settings: Settings) -> str:
    if settings.jwt_algorithm == "RS256":
        return settings.jwt_private_key
    return settings.jwt_secret_key


def _verification_key(settings: Settings) -> str:
    if settings.jwt_algorithm == "RS256":
        return settings.jwt_public_key
    return settings.jwt_secret_key


def create_access_token(
    user_id: UUID,
    email: str,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    return jwt.encode(payload, _signing_key(settings), algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: UUID,
    settings: Settings | None = None,
) -> tuple[str, str]:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    jti = str(uuid4())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
    }
    token = jwt.encode(payload, _signing_key(settings), algorithm=settings.jwt_algorithm)
    return token, jti


def decode_token(
    token: str,
    expected_type: TokenType,
    settings: Settings | None = None,
) -> TokenPayload:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            _verification_key(settings),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "type", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidError() from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise TokenTypeMismatchError()

    return TokenPayload(
        sub=UUID(payload["sub"]),
        email=payload.get("email", ""),
        token_type=token_type,
        jti=payload.get("jti"),
    )
