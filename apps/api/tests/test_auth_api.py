import uuid

import pytest
from core.config import get_settings
from core.email.testing import InMemoryEmailBackend
from db.models.user import User
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from tests.auth_helpers import register_verify_login


@pytest.mark.asyncio
async def test_register_login_me_flow(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    register_res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert register_res.status_code == 201
    body = register_res.json()
    assert body["requires_verification"] is True
    assert body["user"]["email_verified"] is False
    assert register_res.cookies.get(settings.access_cookie_name) is None

    code = mail_backend.last_code
    assert code is not None
    verify_res = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": code},
    )
    assert verify_res.status_code == 200

    login_res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    assert login_res.cookies.get(settings.access_cookie_name)

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


@pytest.mark.asyncio
async def test_login_before_email_verified_returns_403(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"unverified-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert mail_backend.last_code is not None

    res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "email_not_verified"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass1"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    res = await client.get("/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_flow(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    settings = get_settings()
    email = f"refresh-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    refresh_res = await client.post("/v1/auth/refresh")
    assert refresh_res.status_code == 200
    assert refresh_res.cookies.get(settings.access_cookie_name)

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200


@pytest.mark.asyncio
async def test_refresh_rotates_and_revokes_old_token(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"rotate-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    old_refresh_cookie = client.cookies.get(settings.refresh_cookie_name)
    assert old_refresh_cookie is not None

    client.cookies.set(settings.refresh_cookie_name, old_refresh_cookie)
    first_refresh = await client.post("/v1/auth/refresh")
    assert first_refresh.status_code == 200

    client.cookies.set(settings.refresh_cookie_name, old_refresh_cookie)
    second_refresh = await client.post("/v1/auth/refresh")
    assert second_refresh.status_code == 401
    assert second_refresh.json()["error"]["code"] == "token_invalid"


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"logout-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    refresh_cookie = client.cookies.get(settings.refresh_cookie_name)
    assert refresh_cookie is not None

    logout_res = await client.post("/v1/auth/logout")
    assert logout_res.status_code == 200

    client.cookies.set(settings.refresh_cookie_name, refresh_cookie)
    refresh_res = await client.post("/v1/auth/refresh")
    assert refresh_res.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    first = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert first.status_code == 201

    second = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "email_exists"
    assert second.json()["error"]["message"] == "An account with this email already exists."


@pytest.mark.asyncio
async def test_register_invalid_email_format(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/register",
        json={"email": "not-an-email", "password": "securepass123"},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["fields"][0]["field"] == "email"
    assert body["error"]["fields"][0]["code"] == "invalid_email"


@pytest.mark.asyncio
async def test_register_password_too_short(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "Ab1"},
    )
    assert res.status_code == 400
    fields = res.json()["error"]["fields"]
    password_error = next(item for item in fields if item["field"] == "password")
    assert password_error["code"] == "password_too_short"


@pytest.mark.asyncio
async def test_register_password_too_weak_no_digit(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "abcdefgh"},
    )
    assert res.status_code == 400
    password_error = next(
        item for item in res.json()["error"]["fields"] if item["field"] == "password"
    )
    assert password_error["code"] == "password_too_weak"
    assert "number" in password_error["message"]


@pytest.mark.asyncio
async def test_register_password_too_weak_no_letter(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "12345678"},
    )
    assert res.status_code == 400
    password_error = next(
        item for item in res.json()["error"]["fields"] if item["field"] == "password"
    )
    assert password_error["code"] == "password_too_weak"
    assert "letter" in password_error["message"]


@pytest.mark.asyncio
async def test_login_empty_password(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "password": ""},
    )
    assert res.status_code == 400
    password_error = next(
        item for item in res.json()["error"]["fields"] if item["field"] == "password"
    )
    assert password_error["code"] == "password_required"


@pytest.mark.asyncio
async def test_login_invalid_credentials_message_is_english(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass1"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["message"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_inactive_user_returns_invalid_credentials(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"inactive-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    code = mail_backend.last_code
    assert code is not None
    await client.post("/v1/auth/verify-email", json={"email": email, "code": code})

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            update(User).where(User.email == email.lower()).values(is_active=False)
        )
        await session.commit()

    res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_register_empty_display_name_normalized(client: AsyncClient) -> None:
    email = f"display-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password, "display_name": ""},
    )
    assert res.status_code == 201
    assert res.json()["user"]["display_name"] is None


@pytest.mark.asyncio
async def test_login_updates_last_login_at(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"lastlogin-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    code = mail_backend.last_code
    assert code is not None
    await client.post("/v1/auth/verify-email", json={"email": email, "code": code})

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        user_before = result.scalar_one()
        assert user_before.last_login_at is None
        user_id = user_before.id

    client.cookies.clear()
    login_res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200

    async with session_factory() as session:
        user_after = await session.get(User, user_id)
        assert user_after is not None
        assert user_after.last_login_at is not None
