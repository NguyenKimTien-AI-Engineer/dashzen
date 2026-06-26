import uuid

from core.config import Settings, get_settings
from core.email.testing import InMemoryEmailBackend
from httpx import AsyncClient


async def register_user(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
    email: str,
    password: str,
    display_name: str | None = None,
) -> str:
    payload: dict[str, str] = {"email": email, "password": password}
    if display_name is not None:
        payload["display_name"] = display_name

    register_res = await client.post("/v1/auth/register", json=payload)
    assert register_res.status_code == 201
    code = mail_backend.last_code
    assert code is not None
    return code


async def verify_user(client: AsyncClient, email: str, code: str) -> None:
    verify_res = await client.post(
        "/v1/auth/verify-email",
        json={"email": email, "code": code},
    )
    assert verify_res.status_code == 200


async def login_user(client: AsyncClient, email: str, password: str) -> None:
    login_res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200


async def register_verify_login(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
    email: str,
    password: str,
    display_name: str | None = None,
) -> None:
    code = await register_user(client, mail_backend, email, password, display_name)
    await verify_user(client, email, code)
    await login_user(client, email, password)


def access_token_from_client(client: AsyncClient, settings: Settings) -> str:
    token = client.cookies.get(settings.access_cookie_name)
    assert token is not None
    return token


def refresh_token_from_client(client: AsyncClient, settings: Settings) -> str:
    token = client.cookies.get(settings.refresh_cookie_name)
    assert token is not None
    return token


async def create_test_user_and_login(
    client: AsyncClient,
    mail_backend: InMemoryEmailBackend,
    suffix: str = "",
) -> dict[str, str]:
    settings = get_settings()
    unique = uuid.uuid4().hex[:8]
    email = f"testuser-{unique}{suffix}@example.com"
    password = "Password123!"

    resp = await client.post("/v1/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201

    code = mail_backend.last_code
    assert code is not None

    resp = await client.post("/v1/auth/verify-email", json={"email": email, "code": code})
    assert resp.status_code == 200

    resp = await client.post("/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200

    token = client.cookies.get(settings.access_cookie_name)
    assert token is not None

    return {"Authorization": f"Bearer {token}"}
