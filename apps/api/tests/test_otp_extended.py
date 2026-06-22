"""OTP generation and verification unit tests."""

from core.auth.otp import (
    generate_verification_code,
    hash_verification_code,
    verify_verification_code,
)


def test_verification_codes_are_zero_padded_to_six_digits() -> None:
    for _ in range(50):
        code = generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()


def test_leading_zeros_preserved_in_verification_code() -> None:
    code = "000042"
    hashed = hash_verification_code(code)
    assert verify_verification_code("000042", hashed)
    assert not verify_verification_code("42", hashed)


def test_different_codes_produce_different_hashes() -> None:
    h1 = hash_verification_code("123456")
    h2 = hash_verification_code("654321")
    assert h1 != h2


def test_generate_produces_varied_codes() -> None:
    codes = {generate_verification_code() for _ in range(100)}
    assert len(codes) > 80
