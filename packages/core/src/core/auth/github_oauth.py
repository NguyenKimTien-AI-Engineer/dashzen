from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import structlog
from core.config import get_settings
from core.exceptions import GitHubEmailUnavailableError

log = structlog.get_logger(__name__)

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
GITHUB_SCOPES = "read:user user:email"


@dataclass(frozen=True)
class GitHubProfile:
    sub: str
    email: str
    name: str | None
    login: str


def pick_primary_verified_email(emails: list[dict[str, Any]]) -> str | None:
    for item in emails:
        if item.get("primary") and item.get("verified"):
            return str(item["email"]).lower()
    for item in emails:
        if item.get("verified"):
            return str(item["email"]).lower()
    return None


def build_github_authorize_url(*, state: str, code_challenge: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": GITHUB_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    query = httpx.QueryParams(params)
    return f"{GITHUB_AUTH_URL}?{query}"


async def exchange_github_code(code: str, verifier: str) -> str:
    settings = get_settings()
    data = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": code,
        "redirect_uri": settings.github_redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(GITHUB_TOKEN_URL, data=data, headers=headers)
        if response.status_code >= 400:
            log.warning(
                "github_token_exchange_error",
                status=response.status_code,
                error=response.text[:500],
            )
            raise ValueError(f"github token exchange failed: {response.status_code}")
        payload = response.json()
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("github access_token missing")
        return access_token


async def fetch_github_profile(access_token: str) -> GitHubProfile:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        user_response = await client.get(GITHUB_USER_URL, headers=headers)
        if user_response.status_code >= 400:
            log.warning(
                "github_user_fetch_error",
                status=user_response.status_code,
                error=user_response.text[:500],
            )
            raise ValueError(f"github user fetch failed: {user_response.status_code}")
        user = user_response.json()

        emails_response = await client.get(GITHUB_EMAILS_URL, headers=headers)
        if emails_response.status_code >= 400:
            log.warning(
                "github_emails_fetch_error",
                status=emails_response.status_code,
                error=emails_response.text[:500],
            )
            raise ValueError(f"github emails fetch failed: {emails_response.status_code}")
        emails = emails_response.json()

    github_id = user.get("id")
    login = str(user.get("login") or "")
    if github_id is None or not login:
        raise ValueError("github user id or login missing")

    if not isinstance(emails, list):
        raise GitHubEmailUnavailableError()

    email = pick_primary_verified_email(emails)
    if not email:
        raise GitHubEmailUnavailableError()

    display_name = user.get("name")
    name = str(display_name) if display_name else login

    return GitHubProfile(
        sub=str(github_id),
        email=email,
        name=name,
        login=login,
    )
