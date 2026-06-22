import uuid

import pytest
from httpx import AsyncClient

from core.email.testing import InMemoryEmailBackend
from tests.auth_helpers import register_verify_login


@pytest.mark.asyncio
async def test_verify_email_with_wrong_code(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"wrongcode-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )

    res = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": "000000"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_code"


@pytest.mark.asyncio
async def test_verify_email_already_verified(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"already-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": "123456"},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "already_verified"


@pytest.mark.asyncio
async def test_resend_verification_sends_new_code(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"resend-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    first_code = mail_backend.last_code
    assert first_code is not None

    res = await client.post(
        "/v1/auth/resend-verification",
        json={"email": email},
    )
    assert res.status_code == 200
    second_code = mail_backend.last_code
    assert second_code is not None
    assert second_code != first_code

    verify_res = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": second_code},
    )
    assert verify_res.status_code == 200

    wrong_old = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": first_code},
    )
    assert wrong_old.status_code == 409
    assert wrong_old.json()["error"]["code"] == "already_verified"


@pytest.mark.asyncio
async def test_resend_verification_unknown_email_returns_ok(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/resend-verification",
        json={"email": "nobody@example.com"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True


@pytest.mark.asyncio
async def test_too_many_verification_attempts(
    client: AsyncClient, mail_backend: InMemoryEmailBackend
) -> None:
    email = f"attempts-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )

    for _ in range(4):
        res = await client.post(
            "/v1/auth/verify-email",
            json={"email": email, "code": "000000"},
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "invalid_code"

    blocked = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": "000000"},
    )
    assert blocked.status_code == 400
    assert blocked.json()["error"]["code"] == "too_many_attempts"
