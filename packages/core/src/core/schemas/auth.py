from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError

from core.auth.validation import PasswordValidationError, validate_register_password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        try:
            return validate_register_password(value)
        except PasswordValidationError as exc:
            raise PydanticCustomError(exc.code, exc.message) from exc


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str | None = None
    email_verified: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuthUserResponse(BaseModel):
    user: UserResponse


class RegisterResponse(BaseModel):
    user: UserResponse
    requires_verification: bool = True


class OkResponse(BaseModel):
    ok: bool = True


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
