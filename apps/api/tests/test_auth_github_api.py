"""GitHub OAuth API tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from core.auth.github_oauth import GitHubProfile
from core.auth.oauth_common import create_oauth_state_token, generate_pkce_pair
from core.config import get_settings
from core.exceptions import GitHubEmailUnavailableError

pytestmark = pytest.mark.asyncio


def _github_profile(email: str | None = None) -> GitHubProfile:
    suffix = uuid4().hex[:8]
    return GitHubProfile(
        sub=f"{1000 + int(suffix, 16) % 9000}",
        email=email or f"github-{suffix}@example.com",
        name="GitHub User",
        login=f"ghuser-{suffix}",
    )


@pytest.fixture
def github_oauth_settings(monkeypatch):
    monkeypatch.setenv("GITHUB_OAUTH_ENABLED", "true")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "Ov23liTestClientId")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv(
        "GITHUB_REDIRECT_URI",
        "http://test/v1/auth/github/callback",
    )
    monkeypatch.setenv("STUDIO_PUBLIC_URL", "http://studio.test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_github_start_redirects_when_enabled(client, github_oauth_settings):
    response = await client.get(
        "/v1/auth/github",
        params={"return_to": "/app"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "github.com/login/oauth/authorize" in location
    assert "client_id=Ov23liTestClientId" in location
    assert "read%3Auser" in location or "read:user" in location
    assert "code_challenge=" in location


async def test_github_start_disabled_returns_error(client, monkeypatch):
    monkeypatch.setenv("GITHUB_OAUTH_ENABLED", "false")
    get_settings.cache_clear()
    response = await client.get("/v1/auth/github", follow_redirects=False)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "oauth_provider_disabled"
    get_settings.cache_clear()


async def test_github_callback_sets_cookies(client, github_oauth_settings):
    verifier, _challenge = generate_pkce_pair()
    state = create_oauth_state_token(provider="github", verifier=verifier, return_to="/app")
    profile = _github_profile()

    with (
        patch(
            "api.routes.auth_github.exchange_github_code",
            new=AsyncMock(return_value="fake-access-token"),
        ),
        patch(
            "api.routes.auth_github.fetch_github_profile",
            new=AsyncMock(return_value=profile),
        ),
    ):
        response = await client.get(
            "/v1/auth/github/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "http://studio.test/app"
    assert client.cookies.get("dashzen_access_token")
    assert client.cookies.get("dashzen_refresh_token")


async def test_github_callback_invalid_state_redirects_login(client, github_oauth_settings):
    response = await client.get(
        "/v1/auth/github/callback",
        params={"code": "auth-code", "state": "not-a-valid-state"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://studio.test/login?error=oauth_state_invalid"


async def test_github_callback_no_verified_email_redirects(client, github_oauth_settings):
    verifier, _challenge = generate_pkce_pair()
    state = create_oauth_state_token(provider="github", verifier=verifier, return_to="/app")

    with (
        patch(
            "api.routes.auth_github.exchange_github_code",
            new=AsyncMock(return_value="fake-access-token"),
        ),
        patch(
            "api.routes.auth_github.fetch_github_profile",
            new=AsyncMock(side_effect=GitHubEmailUnavailableError()),
        ),
    ):
        response = await client.get(
            "/v1/auth/github/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "http://studio.test/login?error=github_email_unavailable"


async def test_github_links_existing_google_user(
    client,
    mail_backend,
    google_oauth_settings,
    github_oauth_settings,
):
    email = f"dual-{uuid4().hex[:8]}@example.com"

    google_verifier, _ = generate_pkce_pair()
    google_state = create_oauth_state_token(
        provider="google",
        verifier=google_verifier,
        return_to="/app",
    )
    from core.auth.google_oauth import GoogleClaims

    google_claims = GoogleClaims(
        sub=f"google-sub-{uuid4().hex[:8]}",
        email=email,
        email_verified=True,
        name="Google User",
    )

    with (
        patch(
            "api.routes.auth_google.exchange_google_code",
            new=AsyncMock(return_value={"id_token": "fake-id-token"}),
        ),
        patch(
            "api.routes.auth_google.verify_google_id_token",
            new=AsyncMock(return_value=google_claims),
        ),
    ):
        google_res = await client.get(
            "/v1/auth/google/callback",
            params={"code": "auth-code", "state": google_state},
            follow_redirects=False,
        )
    assert google_res.status_code == 302

    github_verifier, _ = generate_pkce_pair()
    github_state = create_oauth_state_token(
        provider="github",
        verifier=github_verifier,
        return_to="/app",
    )
    github_profile = _github_profile(email=email)

    with (
        patch(
            "api.routes.auth_github.exchange_github_code",
            new=AsyncMock(return_value="fake-access-token"),
        ),
        patch(
            "api.routes.auth_github.fetch_github_profile",
            new=AsyncMock(return_value=github_profile),
        ),
    ):
        github_res = await client.get(
            "/v1/auth/github/callback",
            params={"code": "auth-code", "state": github_state},
            follow_redirects=False,
        )

    assert github_res.status_code == 302
    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200
    body = me_res.json()
    assert body["email"] == email
    assert "google" in body["auth_providers"]
    assert "github" in body["auth_providers"]


async def test_github_cross_provider_state_rejected(client, github_oauth_settings):
    verifier, _ = generate_pkce_pair()
    google_state = create_oauth_state_token(provider="google", verifier=verifier, return_to="/app")

    response = await client.get(
        "/v1/auth/github/callback",
        params={"code": "auth-code", "state": google_state},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://studio.test/login?error=oauth_state_invalid"


@pytest.fixture
def google_oauth_settings(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv(
        "GOOGLE_REDIRECT_URI",
        "http://test/v1/auth/google/callback",
    )
    monkeypatch.setenv("STUDIO_PUBLIC_URL", "http://studio.test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
