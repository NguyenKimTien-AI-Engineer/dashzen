import uuid

import pytest
from httpx import AsyncClient

from tests.auth_helpers import register_verify_login

# 1x1 PNG
MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.asyncio
async def test_upload_avatar_success(client: AsyncClient, mail_backend) -> None:
    email = f"avatar-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    upload_res = await client.post(
        "/v1/auth/me/avatar",
        files={"file": ("avatar.png", MINI_PNG, "image/png")},
    )
    assert upload_res.status_code == 200
    body = upload_res.json()
    assert body["avatar_url"] is not None
    assert f"/v1/users/{body['id']}/avatar" in body["avatar_url"]

    avatar_res = await client.get(f"/v1/users/{body['id']}/avatar")
    assert avatar_res.status_code == 200
    assert avatar_res.headers["content-type"] == "image/png"
    assert avatar_res.content == MINI_PNG


@pytest.mark.asyncio
async def test_upload_avatar_requires_auth(client: AsyncClient) -> None:
    res = await client.post(
        "/v1/auth/me/avatar",
        files={"file": ("avatar.png", MINI_PNG, "image/png")},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_upload_avatar_rejects_invalid_type(client: AsyncClient, mail_backend) -> None:
    email = f"bad-avatar-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.post(
        "/v1/auth/me/avatar",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_delete_avatar_success(client: AsyncClient, mail_backend) -> None:
    email = f"del-avatar-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    upload_res = await client.post(
        "/v1/auth/me/avatar",
        files={"file": ("avatar.png", MINI_PNG, "image/png")},
    )
    user_id = upload_res.json()["id"]

    delete_res = await client.delete("/v1/auth/me/avatar")
    assert delete_res.status_code == 200
    assert delete_res.json()["avatar_url"] is None

    avatar_res = await client.get(f"/v1/users/{user_id}/avatar")
    assert avatar_res.status_code == 404


@pytest.mark.asyncio
async def test_update_profile_display_name(client: AsyncClient, mail_backend) -> None:
    email = f"profile-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password, "Old Name")

    patch_res = await client.patch(
        "/v1/auth/me",
        json={"display_name": "New Name"},
    )
    assert patch_res.status_code == 200
    body = patch_res.json()
    assert body["display_name"] == "New Name"

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["display_name"] == "New Name"


@pytest.mark.asyncio
async def test_update_profile_requires_auth(client: AsyncClient) -> None:
    res = await client.patch("/v1/auth/me", json={"display_name": "Test"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_rejects_empty_display_name(client: AsyncClient, mail_backend) -> None:
    email = f"empty-name-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.patch("/v1/auth/me", json={"display_name": "   "})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, mail_backend) -> None:
    email = f"changepw-{uuid.uuid4().hex[:8]}@example.com"
    old_password = "securepass123"
    new_password = "newpass456"

    await register_verify_login(client, mail_backend, email, old_password)

    res = await client.post(
        "/v1/auth/change-password",
        json={"current_password": old_password, "new_password": new_password},
    )
    assert res.status_code == 200

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200

    login_old = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert login_old.status_code == 401

    await client.post("/v1/auth/logout")

    login_new = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert login_new.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, mail_backend) -> None:
    email = f"wrongpw-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.post(
        "/v1/auth/change-password",
        json={"current_password": "wrongpass1", "new_password": "newpass456"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_change_password_same_as_current(client: AsyncClient, mail_backend) -> None:
    email = f"samewp-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.post(
        "/v1/auth/change-password",
        json={"current_password": password, "new_password": password},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_delete_account_success(client: AsyncClient, mail_backend) -> None:
    email = f"delete-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.request(
        "DELETE",
        "/v1/auth/me",
        json={"password": password, "confirmation": "DELETE"},
    )
    assert res.status_code == 200

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 401

    login_res = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_wrong_password(client: AsyncClient, mail_backend) -> None:
    email = f"delwrong-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.request(
        "DELETE",
        "/v1/auth/me",
        json={"password": "wrongpass1", "confirmation": "DELETE"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"

    me_res = await client.get("/v1/auth/me")
    assert me_res.status_code == 200


@pytest.mark.asyncio
async def test_delete_account_invalid_confirmation(client: AsyncClient, mail_backend) -> None:
    email = f"delconf-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    await register_verify_login(client, mail_backend, email, password)

    res = await client.request(
        "DELETE",
        "/v1/auth/me",
        json={"password": password, "confirmation": "NOPE"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "validation_error"
