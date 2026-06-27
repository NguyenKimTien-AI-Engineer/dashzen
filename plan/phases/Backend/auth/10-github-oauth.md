# 10 — GitHub OAuth (Backend)

> **Trạng thái:** Planned
>
> **Master plan:** [`../../../github-oauth-login.md`](../../../github-oauth-login.md)
>
> **Tiền đề:** Google OAuth Done — [08-google-oauth.md](./08-google-oauth.md), `oauth_accounts` migration `009`

---

## 1. Hiện trạng (as-built)

| Thành phần | Trạng thái |
|------------|------------|
| `oauth_accounts` table | **Done** — `provider` + `provider_subject` |
| `password_hash` nullable | **Done** |
| Google routes `/v1/auth/google*` | **Done** — pattern để copy |
| `oauth_common` shared module | **Chưa có** — refactor trong Phase A |
| GitHub routes | **Planned** |
| `AuthProvider` includes `github` | **Planned** |

---

## 2. GitHub OAuth endpoints (reference)

| Step | URL |
|------|-----|
| Authorize | `GET https://github.com/login/oauth/authorize` |
| Token | `POST https://github.com/login/oauth/access_token` |
| User | `GET https://api.github.com/user` |
| Emails | `GET https://api.github.com/user/emails` |

**Authorize params:**

```
client_id, redirect_uri, scope=read:user user:email,
state, code_challenge, code_challenge_method=S256
```

**Token exchange** (PKCE):

```
client_id, client_secret, code, redirect_uri,
grant_type=authorization_code, code_verifier
```

Header bắt buộc: `Accept: application/json` (tránh form-urlencoded response).

---

## 3. Package layout

```
packages/core/src/core/auth/
  oauth_common.py          # NEW — extract từ google_oauth.py
  google_oauth.py          # REFACTOR — dùng oauth_common
  github_oauth.py          # NEW

packages/db/src/db/services/
  github_oauth_service.py  # NEW — mirror GoogleOAuthService

apps/api/src/api/routes/
  auth_github.py           # NEW

apps/api/src/api/main.py   # include auth_github_router
```

---

## 4. `oauth_common.py` (refactor)

Tách từ `google_oauth.py`:

```python
# PKCE
def generate_pkce_pair() -> tuple[str, str]: ...

# State JWT — thêm provider claim
def create_oauth_state_token(*, provider: str, verifier: str, return_to: str) -> str: ...
def parse_oauth_state_token(state: str, *, expected_provider: str) -> OAuthStatePayload: ...

# Redirect helpers
def sanitize_return_to(raw: str | None) -> str: ...
def studio_redirect_url(path: str) -> str: ...
```

**Breaking change nhỏ:** Google state JWT thêm `"provider": "google"`. Update `test_google_oauth.py`.

---

## 5. `github_oauth.py`

```python
@dataclass(frozen=True)
class GitHubProfile:
    sub: str           # str(github_user_id)
    email: str         # primary verified
    name: str | None   # display name or login fallback
    login: str         # GitHub username (log only)


GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
GITHUB_SCOPES = "read:user user:email"


def build_github_authorize_url(*, state: str, code_challenge: str) -> str: ...

async def exchange_github_code(code: str, verifier: str) -> str:
    """Returns access_token."""

async def fetch_github_profile(access_token: str) -> GitHubProfile:
    """GET /user + GET /user/emails → pick primary verified email."""
```

### 5.1 Email selection logic

```python
def pick_primary_verified_email(emails: list[dict]) -> str | None:
    for item in emails:
        if item.get("primary") and item.get("verified"):
            return str(item["email"]).lower()
    # Fallback: any verified email
    for item in emails:
        if item.get("verified"):
            return str(item["email"]).lower()
    return None
```

Nếu `None` → raise `GitHubEmailUnavailableError`.

Display name: `user.name or user.login`.

---

## 6. Config (`packages/core/src/core/config.py`)

```python
github_oauth_enabled: bool = False
github_client_id: str = ""
github_client_secret: str = ""
github_redirect_uri: str = "http://localhost:8000/v1/auth/github/callback"
auth_github_rate_limit: str = "10/minute"
auth_github_callback_rate_limit: str = "20/minute"
```

Dùng lại: `studio_public_url`, `oauth_state_ttl_seconds`.

---

## 7. Exceptions

```python
class GitHubEmailUnavailableError(AuthError):
    code = "github_email_unavailable"
    message = "No verified email on your GitHub account. Make a primary email public and try again."
```

Reuse: `OAuthProviderDisabledError`, `OAuthStateInvalidError`, `OAuthExchangeFailedError`.

---

## 8. `GitHubOAuthService`

Mirror `GoogleOAuthService` — `PROVIDER = "github"`, input `GitHubProfile` thay `GoogleClaims`.

```python
class GitHubOAuthService:
    PROVIDER = "github"

    async def authenticate(self, profile: GitHubProfile) -> User:
        # Same branching as Google:
        # 1. lookup oauth_accounts(github, sub)
        # 2. else lookup user by email → link or create
        # 3. mark_email_verified, update_last_login, commit
```

**Không** gọi `GoogleEmailUnverifiedError` — dùng `GitHubEmailUnavailableError` trước khi vào service.

---

## 9. Routes — `auth_github.py`

Cấu trúc **identical** `auth_google.py`:

```python
@router.get("/github")
async def github_login_start(return_to: str = "/app") -> RedirectResponse:
    verifier, challenge = generate_pkce_pair()
    state = create_oauth_state_token(provider="github", verifier=verifier, return_to=safe_return)
    url = build_github_authorize_url(state=state, code_challenge=challenge)
    return RedirectResponse(url, 302)


@router.get("/github/callback")
async def github_login_callback(code, state, session) -> RedirectResponse:
    oauth_state = parse_oauth_state_token(state, expected_provider="github")
    access_token = await exchange_github_code(code, oauth_state.verifier)
    profile = await fetch_github_profile(access_token)
    user = await GitHubOAuthService(session).authenticate(profile)
    tokens = await AuthService(session).issue_tokens(user)
    response = RedirectResponse(studio_redirect_url(oauth_state.return_to), 302)
    set_auth_cookies(response, ...)
    return response
```

Error redirect codes — xem master plan §6.

---

## 10. Schema updates

```python
AuthProvider = Literal["password", "google", "github"]
```

`build_auth_providers()` — không đổi logic; `list_oauth_providers` trả `"github"` tự động.

---

## 11. Rate limiting

```python
@rate_limit(_settings.auth_github_rate_limit)          # /github
@rate_limit(_settings.auth_github_callback_rate_limit)  # /github/callback
```

---

## 12. Security checklist

- [ ] PKCE S256 bắt buộc
- [ ] State JWT có `provider=github` — reject Google state trên GitHub callback
- [ ] Không log `access_token`, `client_secret`
- [ ] `Accept: application/json` trên token exchange
- [ ] Chỉ chấp nhận **verified** email từ GitHub
- [ ] `return_to` whitelist `/app/*`
- [ ] Feature flag `GITHUB_OAUTH_ENABLED`

---

## 13. Tests — `apps/api/tests/test_auth_github_api.py`

Mirror `test_auth_google_api.py`:

| Test | Mô tả |
|------|-------|
| `test_github_start_redirects` | Location chứa `github.com/login/oauth/authorize` + scopes |
| `test_github_start_disabled` | 400 `oauth_provider_disabled` |
| `test_github_callback_sets_cookies` | Mock exchange + profile |
| `test_github_callback_invalid_state` | Redirect `oauth_state_invalid` |
| `test_github_callback_no_verified_email` | Redirect `github_email_unavailable` |
| `test_github_links_existing_google_user` | Same email → `auth_providers: ["google","github"]` |
| `test_github_cross_provider_state_rejected` | Google state on GitHub callback → invalid |

Mock targets: `exchange_github_code`, `fetch_github_profile`.

Unit tests: `packages/core/tests/test_github_oauth.py` — email picker logic.

---

## 14. File tracker

| File | Action |
|------|--------|
| `packages/core/src/core/auth/oauth_common.py` | Create |
| `packages/core/src/core/auth/google_oauth.py` | Refactor |
| `packages/core/src/core/auth/github_oauth.py` | Create |
| `packages/core/src/core/config.py` | Modify |
| `packages/core/src/core/exceptions.py` | Modify |
| `packages/core/src/core/schemas/auth.py` | Modify |
| `packages/db/src/db/services/github_oauth_service.py` | Create |
| `apps/api/src/api/routes/auth_github.py` | Create |
| `apps/api/src/api/main.py` | Modify |
| `apps/api/tests/test_auth_github_api.py` | Create |
| `packages/core/tests/test_github_oauth.py` | Create |
| `packages/core/tests/test_google_oauth.py` | Update (provider claim) |
| `.env.example` | Modify |
| `render.yaml` | Modify |

**Không cần:** Alembic migration mới.

---

## 15. Observability

```python
log.info("github_oauth_start", return_to=...)
log.info("github_oauth_success", user_id=..., github_login=...)
log.warning("github_oauth_fail", reason="email_unavailable")
log.warning("github_token_exchange_error", status=..., error=...)
```

Metrics (optional, mirror Google):

- `auth_github_start_total`
- `auth_github_success_total`
- `auth_github_error_total{reason}`
