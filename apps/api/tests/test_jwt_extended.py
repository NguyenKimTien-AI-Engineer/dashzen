"""Additional JWT unit tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from core.auth.jwt import create_access_token, create_refresh_token, decode_token
from core.config import get_settings
from core.exceptions import TokenExpiredError, TokenInvalidError, TokenTypeMismatchError


def test_each_refresh_token_gets_unique_jti() -> None:
    user_id = uuid4()
    jtis = set()
    for _ in range(20):
        _token, jti = create_refresh_token(user_id)
        jtis.add(jti)
    assert len(jtis) == 20


def test_decode_token_rejects_tampered_signature() -> None:
    user_id = uuid4()
    token = create_access_token(user_id, "user@example.com")
    header, payload, _signature = token.split(".")
    tampered = f"{header}.{payload}.tampered"
    with pytest.raises(TokenInvalidError):
        decode_token(tampered, expected_type="access")


def test_access_token_missing_type_claim_rejected() -> None:
    settings = get_settings()
    user_id = uuid4()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": "user@example.com",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenInvalidError):
        decode_token(token, expected_type="access")


def test_refresh_token_requires_jti_in_payload() -> None:
    user_id = uuid4()
    token, jti = create_refresh_token(user_id)
    payload = decode_token(token, expected_type="refresh")
    assert payload.jti == jti
    assert jti is not None


def test_token_type_mismatch_has_distinct_error_code() -> None:
    user_id = uuid4()
    refresh_token, _ = create_refresh_token(user_id)
    with pytest.raises(TokenTypeMismatchError) as exc:
        decode_token(refresh_token, expected_type="access")
    assert exc.value.code == "token_type_mismatch"


def test_expired_refresh_token_raises_token_expired() -> None:
    settings = get_settings()
    user_id = uuid4()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now - timedelta(days=1),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenExpiredError):
        decode_token(token, expected_type="refresh")
