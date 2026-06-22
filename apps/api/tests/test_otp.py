from core.auth.otp import (
    generate_verification_code,
    hash_verification_code,
    verify_verification_code,
)


def test_generate_verification_code_is_six_digits() -> None:
    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()


def test_verification_code_hash_roundtrip() -> None:
    code = "123456"
    hashed = hash_verification_code(code)
    assert hashed != code
    assert verify_verification_code(code, hashed)
    assert not verify_verification_code("654321", hashed)
