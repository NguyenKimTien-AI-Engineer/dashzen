# 09 — Google OAuth Checklist

> **Master plan:** [`../../../google-oauth-login.md`](../../../google-oauth-login.md)
>
> **Chi tiết:** [08-google-oauth.md](./08-google-oauth.md) | UI: [11-google-oauth.md](../../UI/Auth/11-google-oauth.md)

---

## Phase A — Infra & Google Console

- [ ] Tạo project Google Cloud (hoặc dùng project hiện có)
- [ ] OAuth consent screen: External, app name DashZen, support email
- [ ] Scopes: `openid`, `email`, `profile`
- [ ] OAuth Client ID (Web application)
- [ ] Redirect URI: `http://localhost:8000/v1/auth/google/callback`
- [ ] Redirect URI: `https://dashzen-api.onrender.com/v1/auth/google/callback`
- [ ] Authorized JS origins: `http://localhost:3000`, production Studio URL
- [ ] Lưu Client ID + Secret vào Render env (không commit)
- [ ] Cập nhật `.env.example`

---

## Phase B — Database

- [ ] Alembic migration: `password_hash` nullable
- [ ] Alembic migration: `oauth_accounts` table
- [ ] Model `OAuthAccount` + repository
- [ ] `create_user()` chấp nhận `password_hash=None`
- [ ] Test migration up/down

---

## Phase C — Backend core

- [ ] `GOOGLE_*` settings trong `config.py`
- [ ] `authlib` dependency
- [ ] `core/auth/google_oauth.py` — ID token verify
- [ ] `GoogleOAuthService` — state, PKCE, exchange, authenticate
- [ ] Redis state store (+ cookie fallback)
- [ ] Exceptions + error handler
- [ ] Routes `GET /google`, `GET /google/callback`
- [ ] Rate limits
- [ ] `UserResponse.has_password`, `auth_providers`
- [ ] `DELETE /auth/me` OAuth-only path
- [ ] `change-password` reject no password

---

## Phase D — Backend tests

- [ ] Unit: user create via Google
- [ ] Unit: auto-link existing email
- [ ] Unit: reject `email_verified=false`
- [ ] API: `/google` returns 302 + Location Google
- [ ] API: callback mock → cookies + redirect
- [ ] API: invalid state → redirect error
- [ ] Integration: me/refresh/logout after Google login
- [ ] `GOOGLE_OAUTH_ENABLED=false` → 503

---

## Phase E — Frontend

- [ ] `NEXT_PUBLIC_GOOGLE_OAUTH_ENABLED`
- [ ] `startGoogleLogin()` in `auth.ts`
- [ ] `GoogleSignInButton` component
- [ ] Login + Register forms
- [ ] OAuth error toasts on `/login`
- [ ] Settings: conditional change password
- [ ] Delete account: optional password field
- [ ] Types `has_password`, `auth_providers`

---

## Phase F — Deploy & QA

- [ ] Render: env vars set
- [ ] Vercel: `NEXT_PUBLIC_GOOGLE_OAUTH_ENABLED=true`
- [ ] Manual: local full flow
- [ ] Manual: production full flow (mobile Safari cookie)
- [ ] Cập nhật [07-implementation-status.md](./07-implementation-status.md)
- [ ] Cập nhật [UI 09-implementation-status.md](../../UI/Auth/09-implementation-status.md)

---

## Phase G — Phase 2 (backlog)

- [ ] `POST /auth/set-password` cho OAuth-only user
- [ ] Link/unlink Google trong Settings
- [ ] `POST /auth/google/link` (authenticated)
- [ ] GitHub OAuth provider
- [ ] Audit log `oauth_link` events

---

## Definition of Done (release v1)

| Tiêu chí | Pass |
|----------|------|
| Google login end-to-end local | ☐ |
| Google login end-to-end production | ☐ |
| No OTP for new Google users | ☐ |
| Session refresh/logout works | ☐ |
| CI green (backend + studio) | ☐ |
| Secrets not in repo | ☐ |
| Plan docs status → Done | ☐ |
