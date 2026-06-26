"""Email verification edge cases and validation."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from core.email.testing import InMemoryEmailBackend
from db.models.email_verification import EmailVerificationCode
from db.models.user import User
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from tests.auth_helpers import register_user, register_verify_login


@pytest.mark.asyncio
async def test_verify_unknown_email_returns_invalid_code(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/verify-email",
        json={"email": "nobody@example.com", "code": "123456"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_code"


@pytest.mark.asyncio
async def test_verify_code_wrong_format_returns_validation_error(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/verify-email",
        json={"email": "user@example.com", "code": "abc"},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_verify_code_too_short_returns_validation_error(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/verify-email",
        json={"email": "user@example.com", "code": "12345"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_expired_verification_code_rejected(
    client: AsyncClient, db_engine, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"expired-code-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    code = await register_user(client, mail_backend, email, password)

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one()
        await session.execute(
            update(EmailVerificationCode)
            .where(
                EmailVerificationCode.user_id == user.id,
                EmailVerificationCode.consumed_at.is_(None),
            )
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await session.commit()

    res = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": code},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_code"


@pytest.mark.asyncio
async def test_resend_on_already_verified_user_returns_ok_silently(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"resend-verified-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)
    messages_before = len(mail_backend.messages)

    res = await client.post(
        "/v1/auth/resend-verification",
        json={"email": email},
    )
    assert res.status_code == 200
    assert len(mail_backend.messages) == messages_before


@pytest.mark.asyncio
async def test_correct_code_after_wrong_attempts_still_works(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"retry-ok-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    code = await register_user(client, mail_backend, email, password)

    for _ in range(3):
        wrong = await client.post(
            "/v1/auth/verify-email",
            json={"email": email, "code": "000000"},
        )
        assert wrong.status_code == 400
        assert wrong.json()["error"]["code"] == "invalid_code"

    ok = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": code},
    )
    assert ok.status_code == 200

    login_res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_register_sends_exactly_one_verification_email(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"one-email-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_user(client, mail_backend, email, password)
    assert len(mail_backend.messages) == 1
    assert mail_backend.messages[0]["to"] == email.lower()
