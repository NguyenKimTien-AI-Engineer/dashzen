from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from core.config import get_settings


@dataclass(frozen=True)
class OAuthStatePayload:
    verifier: str
    return_to: str


def generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def create_oauth_state_token(*, provider: str, verifier: str, return_to: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "type": "oauth_state",
        "provider": provider,
        "verifier": verifier,
        "return_to": return_to,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.oauth_state_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def parse_oauth_state_token(state: str, *, expected_provider: str) -> OAuthStatePayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "verifier", "return_to", "type", "provider"]},
        )
    except jwt.PyJWTError as exc:
        raise ValueError("invalid oauth state") from exc
    if payload.get("type") != "oauth_state":
        raise ValueError("invalid oauth state type")
    if payload.get("provider") != expected_provider:
        raise ValueError("invalid oauth provider")
    return OAuthStatePayload(
        verifier=str(payload["verifier"]),
        return_to=str(payload["return_to"]),
    )


def sanitize_return_to(raw: str | None) -> str:
    if not raw:
        return "/app"
    path = raw.strip()
    if not path.startswith("/app"):
        return "/app"
    if path.startswith("//"):
        return "/app"
    return path


def studio_redirect_url(path: str) -> str:
    settings = get_settings()
    base = settings.studio_public_url.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"
