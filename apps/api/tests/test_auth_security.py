"""Security-focused auth tests: tokens, sessions, authorization headers."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.config import get_settings
from core.email.testing import InMemoryEmailBackend
from db.models.email_verification import EmailVerificationCode
from db.models.user import User
from tests.auth_helpers import (
    access_token_from_client,
    login_user,
    register_user,
    register_verify_login,
    refresh_token_from_client,
    verify_user,
)


@pytest.mark.asyncio
async def test_me_accepts_bearer_token_without_cookie(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"bearer-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    access_token = access_token_from_client(client, settings)
    client.cookies.clear()

    me_res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email.lower()


@pytest.mark.asyncio
async def test_me_rejects_malformed_bearer_token(client: AsyncClient) -> None:
    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "token_invalid"


@pytest.mark.asyncio
async def test_me_rejects_expired_access_token(client: AsyncClient) -> None:
    settings = get_settings()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": "expired@example.com",
        "type": "access",
        "iat": now,
        "exp": now - timedelta(minutes=5),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "token_expired"


@pytest.mark.asyncio
async def test_me_rejects_tampered_access_token(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"tamper-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    token = access_token_from_client(client, settings)
    parts = token.split(".")
    assert len(parts) == 3
    tampered = f"{parts[0]}.{parts[1]}.tamperedsignature"
    client.cookies.clear()

    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "token_invalid"


@pytest.mark.asyncio
async def test_me_rejects_refresh_token_used_as_bearer(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"wrongtype-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    refresh_token = refresh_token_from_client(client, settings)
    client.cookies.clear()

    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "token_invalid"


@pytest.mark.asyncio
async def test_me_returns_401_when_user_deleted_from_db(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"deleted-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    access_token = access_token_from_client(client, settings)

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(delete(User).where(User.email == email.lower()))
        await session.commit()

    client.cookies.clear()
    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "token_invalid"


@pytest.mark.asyncio
async def test_me_returns_403_when_user_deactivated_mid_session(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"deactivated-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    access_token = access_token_from_client(client, settings)

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            update(User).where(User.email == email.lower()).values(is_active=False)
        )
        await session.commit()

    client.cookies.clear()
    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "user_inactive"


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(client: AsyncClient) -> None:
    client.cookies.clear()
    res = await client.post("/v1/auth/refresh")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "token_invalid"


@pytest.mark.asyncio
async def test_refresh_fails_after_user_deactivated(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"refresh-inactive-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    refresh_cookie = refresh_token_from_client(client, settings)

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            update(User).where(User.email == email.lower()).values(is_active=False)
        )
        await session.commit()

    client.cookies.clear()
    client.cookies.set(settings.refresh_cookie_name, refresh_cookie)
    res = await client.post("/v1/auth/refresh")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_auth_cookies(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"logout-cookies-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    assert client.cookies.get(settings.access_cookie_name) is not None

    logout_res = await client.post("/v1/auth/logout")
    assert logout_res.status_code == 200

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_auth_error_envelope_shape(client: AsyncClient) -> None:
    res = await client.get("/v1/auth/me")
    assert res.status_code == 401
    body = res.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message"}
    assert isinstance(body["error"]["code"], str)
    assert isinstance(body["error"]["message"], str)
