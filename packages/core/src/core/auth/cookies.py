from fastapi import Response

from core.config import Settings, get_settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    secure = settings.cookie_secure_resolved
    # Keep access cookie in the browser for the refresh window; JWT inside still
    # expires per jwt_access_token_expire_minutes — API returns 401 → FE refreshes.
    refresh_max_age = settings.jwt_refresh_token_expire_days * 24 * 60 * 60

    response.set_cookie(
        key=settings.access_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=settings.cookie_samesite,
        path=settings.access_cookie_path,
        max_age=refresh_max_age,
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=settings.cookie_samesite,
        path=settings.refresh_cookie_path,
        max_age=refresh_max_age,
    )


def clear_auth_cookies(response: Response, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    secure = settings.cookie_secure_resolved
    response.delete_cookie(
        key=settings.access_cookie_name,
        path=settings.access_cookie_path,
        secure=secure,
        samesite=settings.cookie_samesite,
    )
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        secure=secure,
        samesite=settings.cookie_samesite,
    )
