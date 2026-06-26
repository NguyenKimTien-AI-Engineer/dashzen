"""Complex end-to-end auth flows and concurrency scenarios."""

import asyncio
import uuid

import pytest
from api.main import create_app
from core.config import get_settings
from core.email.testing import InMemoryEmailBackend
from db.models.user import User
from db.session import get_db
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from tests.auth_helpers import (
    refresh_token_from_client,
    register_user,
    register_verify_login,
    verify_user,
)


@pytest.mark.asyncio
async def test_full_auth_lifecycle(client: AsyncClient, mail_backend: InMemoryEmailBackend) -> None:
    settings = get_settings()
    email = f"lifecycle-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    # 1. Register — no session yet
    code = await register_user(client, mail_backend, email, password)
    assert client.cookies.get(settings.access_cookie_name) is None

    # 2. Cannot login before verify
    pre_login = await client.post("/v1/auth/login", json={"email": email, "password": password})
    assert pre_login.status_code == 403

    # 3. Verify email
    await verify_user(client, email, code)

    # 4. Login — session established
    login_res = await client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email_verified"] is True

    # 5. Access protected resource
    me_1 = await client.get("/v1/auth/me")
    assert me_1.status_code == 200

    # 6. Silent refresh
    refresh_res = await client.post("/v1/auth/refresh")
    assert refresh_res.status_code == 200
    me_2 = await client.get("/v1/auth/me")
    assert me_2.status_code == 200

    # 7. Logout
    logout_res = await client.post("/v1/auth/logout")
    assert logout_res.status_code == 200

    # 8. Session gone
    me_3 = await client.get("/v1/auth/me")
    assert me_3.status_code == 401


@pytest.mark.asyncio
async def test_sequential_refresh_chain(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"chain-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    for _ in range(3):
        refresh_res = await client.post("/v1/auth/refresh")
        assert refresh_res.status_code == 200
        assert refresh_res.cookies.get(settings.access_cookie_name)

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200


@pytest.mark.asyncio
async def test_register_email_is_case_insensitive(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    base = uuid.uuid4().hex[:8]
    mixed_email = f"User.{base}@Example.COM"
    lower_email = mixed_email.lower()
    password = "securepass123"

    first = await client.post(
        "/v1/auth/register",
        json={"email": mixed_email, "password": password},
    )
    assert first.status_code == 201
    assert first.json()["user"]["email"] == lower_email

    second = await client.post(
        "/v1/auth/register",
        json={"email": lower_email, "password": password},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "email_exists"


@pytest.mark.asyncio
async def test_login_email_lookup_is_case_insensitive(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    base = uuid.uuid4().hex[:8]
    registered_email = f"case-{base}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, registered_email, password)
    client.cookies.clear()

    login_res = await client.post(
        "/v1/auth/login",
        json={"email": registered_email.upper(), "password": password},
    )
    assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_register_same_email_one_succeeds(
    db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    email = f"race-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"
    payload = {"email": email, "password": password}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        results = await asyncio.gather(
            ac.post("/v1/auth/register", json=payload),
            ac.post("/v1/auth/register", json=payload),
        )

    app.dependency_overrides.clear()

    statuses = sorted(res.status_code for res in results)
    assert statuses == [201, 409]
    codes = {res.json().get("error", {}).get("code") for res in results if res.status_code == 409}
    assert codes == {"email_exists"}


@pytest.mark.asyncio
async def test_verify_then_login_twice_issues_new_refresh_tokens(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    settings = get_settings()
    email = f"twologin-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    code = await register_user(client, mail_backend, email, password)
    await verify_user(client, email, code)

    login_1 = await client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_1.status_code == 200
    refresh_1 = refresh_token_from_client(client, settings)

    client.cookies.clear()
    login_2 = await client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login_2.status_code == 200
    refresh_2 = refresh_token_from_client(client, settings)

    assert refresh_1 != refresh_2


@pytest.mark.asyncio
async def test_me_includes_email_verified_flag(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"verified-flag-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200
    body = me_res.json()
    assert body["email_verified"] is True
    assert body["email"] == email.lower()
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_verify_sets_email_verified_at_in_db(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"verified-at-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    code = await register_user(client, mail_backend, email, password)

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        user_before = result.scalar_one()
        assert user_before.email_verified is False
        assert user_before.email_verified_at is None

    await verify_user(client, email, code)

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        user_after = result.scalar_one()
        assert user_after.email_verified is True
        assert user_after.email_verified_at is not None
