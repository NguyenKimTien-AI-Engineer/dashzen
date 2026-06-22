from core.auth.password import hash_password, verify_password


def test_hash_and_verify_password_roundtrip() -> None:
    hashed = hash_password("securepass123")
    assert hashed != "securepass123"
    assert verify_password("securepass123", hashed)
    assert not verify_password("wrongpassword", hashed)
