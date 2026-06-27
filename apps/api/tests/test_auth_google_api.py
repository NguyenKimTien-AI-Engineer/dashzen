"""Google OAuth API tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from core.auth.google_oauth import GoogleClaims, create_oauth_state_token, generate_pkce_pair
from core.config import get_settings

pytestmark = pytest.mark.asyncio


def _google_claims(email: str | None = None) -> GoogleClaims:
    suffix = uuid4().hex[:8]
    return GoogleClaims(
        sub=f"google-sub-{suffix}",
        email=email or f"google-{suffix}@example.com",
        email_verified=True,
        name="Google User",
    )


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


async def test_google_start_redirects_when_enabled(client, google_oauth_settings):
    response = await client.get(
        "/v1/auth/google",
        params={"return_to": "/app"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "accounts.google.com/o/oauth2/v2/auth" in location
    assert "client_id=test-client-id.apps.googleusercontent.com" in location
    assert "code_challenge=" in location


async def test_google_start_disabled_returns_error(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_ENABLED", "false")
    get_settings.cache_clear()
    response = await client.get("/v1/auth/google", follow_redirects=False)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "oauth_provider_disabled"
    get_settings.cache_clear()


async def test_google_callback_sets_cookies(client, google_oauth_settings):
    verifier, _challenge = generate_pkce_pair()
    state = create_oauth_state_token(verifier, "/app")
    claims = _google_claims()

    with (
        patch(
            "api.routes.auth_google.exchange_google_code",
            new=AsyncMock(return_value={"id_token": "fake-id-token"}),
        ),
        patch(
            "api.routes.auth_google.verify_google_id_token",
            new=AsyncMock(return_value=claims),
        ),
    ):
        response = await client.get(
            "/v1/auth/google/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "http://studio.test/app"
    assert client.cookies.get("dashzen_access_token")
    assert client.cookies.get("dashzen_refresh_token")


async def test_google_callback_invalid_state_redirects_login(client, google_oauth_settings):
    response = await client.get(
        "/v1/auth/google/callback",
        params={"code": "auth-code", "state": "not-a-valid-state"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://studio.test/login?error=oauth_state_invalid"


async def test_google_callback_links_existing_password_user(
    client,
    mail_backend,
    google_oauth_settings,
):
    email = f"link-{uuid4().hex[:8]}@example.com"
    password = "securepass123"
    register_res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_res.status_code == 201

    verifier, _challenge = generate_pkce_pair()
    state = create_oauth_state_token(verifier, "/app")
    claims = _google_claims(email=email)

    with (
        patch(
            "api.routes.auth_google.exchange_google_code",
            new=AsyncMock(return_value={"id_token": "fake-id-token"}),
        ),
        patch(
            "api.routes.auth_google.verify_google_id_token",
            new=AsyncMock(return_value=claims),
        ),
    ):
        response = await client.get(
            "/v1/auth/google/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 302
    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200
    body = me_res.json()
    assert body["email"] == email
    assert body["has_password"] is True
    assert "google" in body["auth_providers"]
    assert "password" in body["auth_providers"]


async def test_change_password_rejects_oauth_only_user(
    client,
    mail_backend,
    google_oauth_settings,
):
    verifier, _challenge = generate_pkce_pair()
    state = create_oauth_state_token(verifier, "/app")
    claims = _google_claims()

    with (
        patch(
            "api.routes.auth_google.exchange_google_code",
            new=AsyncMock(return_value={"id_token": "fake-id-token"}),
        ),
        patch(
            "api.routes.auth_google.verify_google_id_token",
            new=AsyncMock(return_value=claims),
        ),
    ):
        await client.get(
            "/v1/auth/google/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )

    response = await client.post(
        "/v1/auth/change-password",
        json={"current_password": "nope", "new_password": "newpass123"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "no_password_auth"
