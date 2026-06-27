from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "staging", "production"]
CookieSameSite = Literal["lax", "strict", "none"]
JwtAlgorithm = Literal["HS256", "RS256"]
EmailBackendType = Literal["console", "smtp"]
LLMProvider = Literal["ollama", "anthropic", "openai", "gemini", "openrouter"]


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
    api_cors_origin_regex: str = Field(
        default="",
        description=(
            "Optional regex for extra CORS origins (e.g. Vercel previews). "
            "Defaults to *.vercel.app in production when unset."
        ),
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
    auth_google_rate_limit: str = "10/minute"
    auth_google_callback_rate_limit: str = "20/minute"
    auth_github_rate_limit: str = "10/minute"
    auth_github_callback_rate_limit: str = "20/minute"

    google_oauth_enabled: bool = False
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/v1/auth/google/callback"
    google_hd: str | None = None

    github_oauth_enabled: bool = False
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/v1/auth/github/callback"
    oauth_state_ttl_seconds: int = 600

    studio_public_url: str = Field(
        default="http://localhost:3000",
        description="Public Studio base URL for OAuth redirects after login",
    )

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

    llm_provider: LLMProvider = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_api_key: str = ""
    ollama_thinking_enabled: bool = True
    ollama_think_level: str = Field(
        default="",
        description=(
            "Ollama think level: empty/true, or low|medium|high|max. "
            "GPT-OSS models only accept low|medium|high."
        ),
    )
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-5-20251101"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-lite"
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_site_url: str = "http://localhost:3000"
    openrouter_app_name: str = "DashZen Studio"

    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "dashzen"

    api_public_url: str = Field(
        default="http://localhost:8000",
        description="Public API base URL for avatar and asset links",
    )
    avatar_storage_dir: str = Field(
        default="data/avatars",
        description="Local directory for user avatar files",
    )
    published_artifact_names: str = Field(
        default="dashboard.html",
        description="Comma-separated artifact file names surfaced in the Artifacts gallery",
    )

    @model_validator(mode="after")
    def validate_jwt_config(self) -> Self:
        if self.jwt_algorithm == "HS256":
            if len(self.jwt_secret_key) < 16:
                raise ValueError("jwt_secret_key must be at least 16 characters for HS256")
        elif self.jwt_algorithm == "RS256":
            if not self.jwt_private_key.strip() or not self.jwt_public_key.strip():
                raise ValueError("jwt_private_key and jwt_public_key are required for RS256")
        return self

    _VERCEL_CORS_ORIGIN_REGEX = r"https://[\w.-]+\.vercel\.app"

    @property
    def cors_origins(self) -> list[str]:
        origins: list[str] = []
        for origin in self.api_cors_origins.split(","):
            normalized = origin.strip().rstrip("/")
            if normalized:
                origins.append(normalized)
        return origins

    @property
    def cors_origin_regex(self) -> str | None:
        explicit = self.api_cors_origin_regex.strip()
        if explicit:
            return explicit
        if self.app_env == "production":
            return self._VERCEL_CORS_ORIGIN_REGEX
        return None

    @property
    def cookie_secure_resolved(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.app_env != "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
