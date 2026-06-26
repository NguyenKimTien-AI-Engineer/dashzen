import re

from core.config import Settings

_DB = "postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen"
_JWT = "test-secret-key-for-pytest-only-32b!"


def _settings(**kwargs: object) -> Settings:
    return Settings(database_url=_DB, jwt_secret_key=_JWT, **kwargs)


def test_cors_origins_strip_trailing_slashes() -> None:
    settings = _settings(
        api_cors_origins="http://localhost:3000/, https://dashzen-mu.vercel.app/",
    )
    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://dashzen-mu.vercel.app",
    ]


def test_production_allows_vercel_origins_via_regex() -> None:
    settings = _settings(app_env="production")
    pattern = settings.cors_origin_regex
    assert pattern is not None
    assert re.fullmatch(pattern, "https://dashzen-mu.vercel.app")
    assert re.fullmatch(pattern, "https://dashzen-lead.vercel.app")
    assert re.fullmatch(pattern, "https://dashzen-git-main-user.vercel.app")
    assert re.fullmatch(pattern, "https://evil.com") is None


def test_development_has_no_origin_regex_by_default() -> None:
    settings = _settings(app_env="development")
    assert settings.cors_origin_regex is None


def test_explicit_origin_regex_overrides_production_default() -> None:
    settings = _settings(
        app_env="production",
        api_cors_origin_regex=r"https://studio\.example\.com",
    )
    assert settings.cors_origin_regex == r"https://studio\.example\.com"
