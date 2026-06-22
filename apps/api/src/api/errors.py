from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.exceptions import (
    AlreadyVerifiedError,
    AuthError,
    EmailExistsError,
    EmailNotVerifiedError,
    InvalidVerificationCodeError,
    TooManyVerificationAttemptsError,
    UserInactiveError,
)
from core.schemas.validation import format_validation_errors


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthError)
    async def auth_error_handler(_request: Request, exc: AuthError) -> JSONResponse:
        status_code = 401
        if isinstance(exc, EmailExistsError):
            status_code = 409
        elif isinstance(exc, (UserInactiveError, EmailNotVerifiedError)):
            status_code = 403
        elif isinstance(
            exc, (InvalidVerificationCodeError, TooManyVerificationAttemptsError)
        ):
            status_code = 400
        elif isinstance(exc, AlreadyVerifiedError):
            status_code = 409
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=format_validation_errors(exc.errors()),
        )
