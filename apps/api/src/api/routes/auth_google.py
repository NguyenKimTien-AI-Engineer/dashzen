import structlog
from core.auth.cookies import set_auth_cookies
from core.auth.google_oauth import (
    build_google_authorize_url,
    create_oauth_state_token,
    exchange_google_code,
    generate_pkce_pair,
    parse_oauth_state_token,
    sanitize_return_to,
    studio_redirect_url,
    verify_google_id_token,
)
from core.config import get_settings
from core.exceptions import (
    GoogleEmailUnverifiedError,
    OAuthExchangeFailedError,
    OAuthProviderDisabledError,
)
from db.services.auth import AuthService
from db.services.google_oauth_service import GoogleOAuthService
from db.session import get_db
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.rate_limit import rate_limit

router = APIRouter(prefix="/v1/auth", tags=["auth"])
_settings = get_settings()
log = structlog.get_logger(__name__)


def _oauth_error_redirect(code: str) -> RedirectResponse:
    return RedirectResponse(
        studio_redirect_url(f"/login?error={code}"),
        status_code=302,
    )


def _ensure_google_enabled() -> None:
    settings = get_settings()
    if not settings.google_oauth_enabled:
        raise OAuthProviderDisabledError()
    if not settings.google_client_id or not settings.google_client_secret:
        raise OAuthProviderDisabledError()


@router.get("/google")
@rate_limit(_settings.auth_google_rate_limit)
async def google_login_start(
    request: Request,
    return_to: str = "/app",
) -> RedirectResponse:
    _ensure_google_enabled()
    safe_return = sanitize_return_to(return_to)
    verifier, challenge = generate_pkce_pair()
    state = create_oauth_state_token(verifier, safe_return)
    url = build_google_authorize_url(state=state, code_challenge=challenge)
    log.info("google_oauth_start", return_to=safe_return)
    return RedirectResponse(url, status_code=302)


@router.get("/google/callback")
@rate_limit(_settings.auth_google_callback_rate_limit)
async def google_login_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    _ensure_google_enabled()

    if error:
        log.warning("google_oauth_provider_error", error=error)
        return _oauth_error_redirect("oauth_exchange_failed")

    if not code or not state:
        return _oauth_error_redirect("oauth_state_invalid")

    try:
        oauth_state = parse_oauth_state_token(state)
    except ValueError:
        log.warning("google_oauth_state_invalid")
        return _oauth_error_redirect("oauth_state_invalid")

    try:
        token_payload = await exchange_google_code(code, oauth_state.verifier)
        id_token = token_payload.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise ValueError("missing id_token")
        claims = await verify_google_id_token(id_token)
    except (ValueError, OAuthExchangeFailedError) as exc:
        log.warning("google_oauth_exchange_failed", reason=str(exc))
        return _oauth_error_redirect("oauth_exchange_failed")
    except Exception:
        log.exception("google_oauth_unexpected_error")
        return _oauth_error_redirect("oauth_exchange_failed")

    try:
        google_service = GoogleOAuthService(session)
        user = await google_service.authenticate(claims)
        auth_service = AuthService(session)
        tokens = await auth_service.issue_tokens(user)
    except GoogleEmailUnverifiedError:
        return _oauth_error_redirect("google_email_unverified")
    except Exception:
        log.exception("google_oauth_authenticate_failed")
        return _oauth_error_redirect("oauth_exchange_failed")

    response = RedirectResponse(
        studio_redirect_url(oauth_state.return_to),
        status_code=302,
    )
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    log.info("google_oauth_success", user_id=str(user.id))
    return response
