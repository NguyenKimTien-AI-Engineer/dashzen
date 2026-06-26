import pytest
from core.auth.validation import PasswordValidationError, validate_register_password


def test_validate_register_password_accepts_strong_password() -> None:
    assert validate_register_password("securepass123") == "securepass123"


def test_validate_register_password_rejects_too_short() -> None:
    with pytest.raises(PasswordValidationError) as exc:
        validate_register_password("Ab1")
    assert exc.value.code == "password_too_short"


def test_validate_register_password_rejects_no_letter() -> None:
    with pytest.raises(PasswordValidationError) as exc:
        validate_register_password("12345678")
    assert exc.value.code == "password_too_weak"
    assert "letter" in exc.value.message


def test_validate_register_password_rejects_no_digit() -> None:
    with pytest.raises(PasswordValidationError) as exc:
        validate_register_password("abcdefgh")
    assert exc.value.code == "password_too_weak"
    assert "number" in exc.value.message
