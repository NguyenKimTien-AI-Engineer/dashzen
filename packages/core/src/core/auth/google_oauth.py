from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
import structlog
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt
from authlib.jose.errors import JoseError
from core.config import get_settings

log = structlog.get_logger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})
GOOGLE_SCOPES = "openid email profile"

_jwks_cache: JsonWebKey | None = None
_jwks_cached_at: datetime | None = None
_JWKS_TTL = timedelta(hours=1)


@dataclass(frozen=True)
class GoogleClaims:
    sub: str
    email: str
    email_verified: bool
    name: str | None


@dataclass(frozen=True)
class OAuthStatePayload:
    verifier: str
    return_to: str


def generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def create_oauth_state_token(verifier: str, return_to: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "type": "oauth_state",
        "verifier": verifier,
        "return_to": return_to,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.oauth_state_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def parse_oauth_state_token(state: str) -> OAuthStatePayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "verifier", "return_to", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise ValueError("invalid oauth state") from exc
    if payload.get("type") != "oauth_state":
        raise ValueError("invalid oauth state type")
    return OAuthStatePayload(
        verifier=str(payload["verifier"]),
        return_to=str(payload["return_to"]),
    )


def build_google_authorize_url(*, state: str, code_challenge: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "select_account",
    }
    if settings.google_hd:
        params["hd"] = settings.google_hd
    query = httpx.QueryParams(params)
    return f"{GOOGLE_AUTH_URL}?{query}"


async def _load_google_jwks() -> JsonWebKey:
    global _jwks_cache, _jwks_cached_at
    now = datetime.now(UTC)
    if _jwks_cache is not None and _jwks_cached_at is not None:
        if now - _jwks_cached_at < _JWKS_TTL:
            return _jwks_cache
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(GOOGLE_JWKS_URL)
        response.raise_for_status()
        _jwks_cache = JsonWebKey.import_key_set(response.json())
        _jwks_cached_at = now
        return _jwks_cache


async def exchange_google_code(code: str, verifier: str) -> dict[str, Any]:
    settings = get_settings()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.google_redirect_uri,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code_verifier": verifier,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        if response.status_code >= 400:
            log.warning(
                "google_token_exchange_error",
                status=response.status_code,
                error=response.text[:500],
            )
            raise ValueError(f"google token exchange failed: {response.status_code}")
        return response.json()


async def verify_google_id_token(id_token: str) -> GoogleClaims:
    settings = get_settings()
    jwks = await _load_google_jwks()
    try:
        claims = jose_jwt.decode(id_token, jwks)
        claims.validate()
    except JoseError as exc:
        raise ValueError("invalid google id token") from exc

    issuer = claims.get("iss")
    if issuer not in GOOGLE_ISSUERS:
        raise ValueError("invalid google issuer")
    audience = claims.get("aud")
    client_id = settings.google_client_id
    if isinstance(audience, list):
        if client_id not in audience:
            raise ValueError("invalid google audience")
    elif audience != client_id:
        raise ValueError("invalid google audience")

    email = str(claims.get("email") or "").lower()
    if not email:
        raise ValueError("google email missing")

    return GoogleClaims(
        sub=str(claims.get("sub") or ""),
        email=email,
        email_verified=bool(claims.get("email_verified")),
        name=claims.get("name"),
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
