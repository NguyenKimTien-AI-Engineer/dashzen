import structlog
from core.auth.cookies import set_auth_cookies
from core.auth.github_oauth import (
    build_github_authorize_url,
    exchange_github_code,
    fetch_github_profile,
)
from core.auth.oauth_common import (
    create_oauth_state_token,
    generate_pkce_pair,
    parse_oauth_state_token,
    sanitize_return_to,
    studio_redirect_url,
)
from core.config import get_settings
from core.exceptions import (
    GitHubAccountInactiveError,
    GitHubEmailUnavailableError,
    OAuthProviderDisabledError,
)
from db.services.auth import AuthService
from db.services.github_oauth_service import GitHubOAuthService
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


def _ensure_github_enabled() -> None:
    settings = get_settings()
    if not settings.github_oauth_enabled:
        raise OAuthProviderDisabledError()
    if not settings.github_client_id or not settings.github_client_secret:
        raise OAuthProviderDisabledError()


@router.get("/github")
@rate_limit(_settings.auth_github_rate_limit)
async def github_login_start(
    request: Request,
    return_to: str = "/app",
) -> RedirectResponse:
    _ensure_github_enabled()
    safe_return = sanitize_return_to(return_to)
    verifier, challenge = generate_pkce_pair()
    state = create_oauth_state_token(provider="github", verifier=verifier, return_to=safe_return)
    url = build_github_authorize_url(state=state, code_challenge=challenge)
    log.info("github_oauth_start", return_to=safe_return)
    return RedirectResponse(url, status_code=302)


@router.get("/github/callback")
@rate_limit(_settings.auth_github_callback_rate_limit)
async def github_login_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    _ensure_github_enabled()

    if error:
        log.warning("github_oauth_provider_error", error=error)
        return _oauth_error_redirect("oauth_exchange_failed")

    if not code or not state:
        return _oauth_error_redirect("oauth_state_invalid")

    try:
        oauth_state = parse_oauth_state_token(state, expected_provider="github")
    except ValueError:
        log.warning("github_oauth_state_invalid")
        return _oauth_error_redirect("oauth_state_invalid")

    try:
        access_token = await exchange_github_code(code, oauth_state.verifier)
        profile = await fetch_github_profile(access_token)
    except GitHubEmailUnavailableError:
        log.warning("github_oauth_fail", reason="email_unavailable")
        return _oauth_error_redirect("github_email_unavailable")
    except ValueError as exc:
        log.warning("github_oauth_exchange_failed", reason=str(exc))
        return _oauth_error_redirect("oauth_exchange_failed")
    except Exception:
        log.exception("github_oauth_unexpected_error")
        return _oauth_error_redirect("oauth_exchange_failed")

    try:
        github_service = GitHubOAuthService(session)
        user = await github_service.authenticate(profile)
        auth_service = AuthService(session)
        tokens = await auth_service.issue_tokens(user)
    except GitHubEmailUnavailableError:
        return _oauth_error_redirect("github_email_unavailable")
    except GitHubAccountInactiveError:
        return _oauth_error_redirect("github_account_inactive")
    except Exception:
        log.exception("github_oauth_authenticate_failed")
        return _oauth_error_redirect("oauth_exchange_failed")

    response = RedirectResponse(
        studio_redirect_url(oauth_state.return_to),
        status_code=302,
    )
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    log.info("github_oauth_success", user_id=str(user.id), github_login=profile.login)
    return response
