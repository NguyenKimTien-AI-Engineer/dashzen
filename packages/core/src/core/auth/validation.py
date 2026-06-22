import re

PASSWORD_MIN_LENGTH = 8
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


class PasswordValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def validate_register_password(password: str) -> str:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordValidationError(
            "password_too_short",
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters.",
        )
    if not _HAS_LETTER.search(password):
        raise PasswordValidationError(
            "password_too_weak",
            "Password must include at least one letter.",
        )
    if not _HAS_DIGIT.search(password):
        raise PasswordValidationError(
            "password_too_weak",
            "Password must include at least one number.",
        )
    return password
