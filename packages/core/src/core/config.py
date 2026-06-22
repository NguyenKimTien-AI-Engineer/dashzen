from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "staging", "production"]
CookieSameSite = Literal["lax", "strict", "none"]
JwtAlgorithm = Literal["HS256", "RS256"]
EmailBackendType = Literal["console", "smtp"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: AppEnv = "development"

    database_url: str = Field(description="PostgreSQL async URL (required via DATABASE_URL)")

    jwt_secret_key: str = Field(default="", description="Required for HS256")
    jwt_algorithm: JwtAlgorithm = "HS256"
    jwt_private_key: str = Field(default="", description="PEM private key for RS256 signing")
    jwt_public_key: str = Field(default="", description="PEM public key for RS256 verification")
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    api_cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated allowed CORS origins",
    )

    access_cookie_name: str = "dashzen_access_token"
    refresh_cookie_name: str = "dashzen_refresh_token"
    access_cookie_path: str = "/"
    refresh_cookie_path: str = "/v1/auth"
    cookie_samesite: CookieSameSite = "lax"
    cookie_secure: bool | None = Field(
        default=None,
        description="Override secure cookie flag; defaults to true outside development",
    )

    rate_limit_enabled: bool = True
    auth_login_rate_limit: str = "5/minute"
    auth_register_rate_limit: str = "10/minute"
    auth_refresh_rate_limit: str = "3/minute"
    auth_verify_rate_limit: str = "5/minute"
    auth_resend_rate_limit: str = "3/hour"

    email_backend: EmailBackendType = "console"
    email_from: str = "noreply@dashzen.local"
    email_verification_code_ttl_minutes: int = 15
    email_verification_max_attempts: int = 5

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    smtp_ssl: bool = False

    @model_validator(mode="after")
    def validate_jwt_config(self) -> Self:
        if self.jwt_algorithm == "HS256":
            if len(self.jwt_secret_key) < 16:
                raise ValueError("jwt_secret_key must be at least 16 characters for HS256")
        elif self.jwt_algorithm == "RS256":
            if not self.jwt_private_key.strip() or not self.jwt_public_key.strip():
                raise ValueError("jwt_private_key and jwt_public_key are required for RS256")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def cookie_secure_resolved(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.app_env != "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
