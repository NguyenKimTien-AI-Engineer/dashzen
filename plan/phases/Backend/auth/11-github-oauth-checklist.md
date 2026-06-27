# 11 — GitHub OAuth Checklist

> **Master plan:** [`../../../github-oauth-login.md`](../../../github-oauth-login.md)
>
> **Chi tiết:** [10-github-oauth.md](./10-github-oauth.md) | UI: [12-github-oauth.md](../../UI/Auth/12-github-oauth.md)

---

## Phase A — Refactor shared OAuth

- [ ] Tạo `packages/core/src/core/auth/oauth_common.py`
- [ ] Refactor `google_oauth.py` dùng `oauth_common`
- [ ] State JWT thêm claim `provider`
- [ ] Cập nhật `test_google_oauth.py` + Google callback tests
- [ ] Verify Google login vẫn pass (regression)

---

## Phase B — GitHub OAuth App

- [ ] Tạo GitHub OAuth App (DashZen)
- [ ] Callback local: `http://localhost:8000/v1/auth/github/callback`
- [ ] Callback prod: `https://<studio>/api/v1/auth/github/callback`
- [ ] Copy Client ID + Secret → `.env` / Render (không commit)

---

## Phase C — Backend

- [ ] `github_oauth.py` — authorize, exchange, profile/emails
- [ ] `GitHubOAuthService`
- [ ] `auth_github.py` routes
- [ ] Config `GITHUB_*` + rate limits
- [ ] `GitHubEmailUnavailableError` + handler
- [ ] `AuthProvider` thêm `"github"`
- [ ] `main.py` include router
- [ ] `.env.example` + `render.yaml`

---

## Phase D — Backend tests

- [ ] Unit: email picker (primary verified, fallback, none)
- [ ] Unit: state JWT provider mismatch
- [ ] API: `/github` redirect + scopes
- [ ] API: callback mock → cookies
- [ ] API: no verified email → redirect error
- [ ] API: link Google + GitHub same email
- [ ] API: disabled flag → 400

---

## Phase E — Frontend

- [ ] `NEXT_PUBLIC_GITHUB_OAUTH_ENABLED`
- [ ] `GitHubSignInButton`
- [ ] `startGitHubLogin()` in `auth.ts`
- [ ] Login + Register forms (stack với Google)
- [ ] Error toast `github_email_unavailable`
- [ ] Export từ `modules/auth/index.ts`

---

## Phase F — Deploy & QA

- [ ] Render env vars set
- [ ] Vercel `NEXT_PUBLIC_GITHUB_OAUTH_ENABLED=true`
- [ ] Verify `oauth_accounts` migration đã chạy prod (009)
- [ ] Manual local full flow
- [ ] Manual prod full flow
- [ ] Regression Google login vẫn OK

---

## Phase G — Phase 2 (backlog)

- [ ] Settings: Connected accounts (link/unlink)
- [ ] Generic `OAuthAccountService` refactor
- [ ] `POST /auth/github/link` (authenticated)
- [ ] Microsoft / Apple providers

---

## Definition of Done (release v1)

| Tiêu chí | Pass |
|----------|------|
| GitHub login end-to-end local | ☐ |
| GitHub login end-to-end production | ☐ |
| Same email links Google + GitHub | ☐ |
| No verified email → clear error | ☐ |
| Google login regression pass | ☐ |
| CI green | ☐ |
| Plan docs status → Done | ☐ |
