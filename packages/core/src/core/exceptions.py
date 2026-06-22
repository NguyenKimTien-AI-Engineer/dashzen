class AuthError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__("invalid_credentials", "Invalid email or password.")


class EmailExistsError(AuthError):
    def __init__(self) -> None:
        super().__init__("email_exists", "An account with this email already exists.")


class UserInactiveError(AuthError):
    def __init__(self) -> None:
        super().__init__("user_inactive", "This account has been deactivated.")


class TokenExpiredError(AuthError):
    def __init__(self) -> None:
        super().__init__("token_expired", "Your session has expired. Please sign in again.")


class TokenInvalidError(AuthError):
    def __init__(self) -> None:
        super().__init__("token_invalid", "Invalid or missing authentication token.")


class TokenTypeMismatchError(AuthError):
    def __init__(self) -> None:
        super().__init__("token_type_mismatch", "Invalid authentication token type.")


class EmailNotVerifiedError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            "email_not_verified",
            "Please verify your email address before signing in.",
        )


class InvalidVerificationCodeError(AuthError):
    def __init__(self) -> None:
        super().__init__("invalid_code", "Invalid or expired verification code.")


class TooManyVerificationAttemptsError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            "too_many_attempts",
            "Too many failed attempts. Please request a new verification code.",
        )


class AlreadyVerifiedError(AuthError):
    def __init__(self) -> None:
        super().__init__("already_verified", "This email address is already verified.")
