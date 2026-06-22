from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from core.auth.jwt import create_access_token, create_refresh_token, decode_token
from core.config import Settings, get_settings
from core.exceptions import TokenExpiredError, TokenTypeMismatchError


def test_access_token_roundtrip() -> None:
    user_id = uuid4()
    email = "user@example.com"
    token = create_access_token(user_id, email)
    payload = decode_token(token, expected_type="access")
    assert payload.sub == user_id
    assert payload.email == email


def test_refresh_token_roundtrip() -> None:
    user_id = uuid4()
    token, jti = create_refresh_token(user_id)
    payload = decode_token(token, expected_type="refresh")
    assert payload.sub == user_id
    assert payload.jti == jti


def test_expired_token_raises() -> None:
    settings = get_settings()
    user_id = uuid4()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": "user@example.com",
        "type": "access",
        "iat": now,
        "exp": now - timedelta(minutes=1),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenExpiredError):
        decode_token(token, expected_type="access")


def test_wrong_token_type_raises() -> None:
    user_id = uuid4()
    token, _jti = create_refresh_token(user_id)
    with pytest.raises(TokenTypeMismatchError) as exc_info:
        decode_token(token, expected_type="access")
    assert exc_info.value.code == "token_type_mismatch"


def test_rs256_token_roundtrip() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    settings = Settings(
        database_url="postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen",
        jwt_algorithm="RS256",
        jwt_private_key=private_pem,
        jwt_public_key=public_pem,
    )
    user_id = uuid4()
    email = "rs256@example.com"
    access_token = create_access_token(user_id, email, settings=settings)
    refresh_token, jti = create_refresh_token(user_id, settings=settings)

    access_payload = decode_token(access_token, expected_type="access", settings=settings)
    refresh_payload = decode_token(refresh_token, expected_type="refresh", settings=settings)
    assert access_payload.email == email
    assert refresh_payload.jti == jti
