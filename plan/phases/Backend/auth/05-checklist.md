# 05 — Auth Checklist & Definition of Done

> Slice 1 — Auth vertical. Cập nhật 2026-06-22 sau backend hardening.

---

## Backend checklist

### Infrastructure (Docker PostgreSQL)
- [x] `infra/compose/docker-compose.yml` — postgres:16-alpine
- [x] `docker compose -f infra/compose/docker-compose.yml up -d`
- [x] Container `dashzen-postgres` status **healthy**
- [x] `.env` — `DATABASE_URL=postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen`
- [x] `User` model + Alembic migration 001 applied
- [x] Migration 002 — `refresh_tokens`, `last_login_at`, `updated_at` trigger
- [x] JWT env vars in `.env` (secret changed from default for prod)

### Core (`packages/core/auth/`)
- [x] `password.py` — hash + verify (bcrypt 12)
- [x] `jwt.py` — access + refresh encode/decode (HS256 + RS256)
- [x] `cookies.py` — set/clear on `Response`
- [x] `validation.py` — password strength
- [x] `schemas/auth.py` — Pydantic request/response + `PydanticCustomError`
- [x] `schemas/validation.py` — structured error formatting
- [x] `exceptions.py` — AuthError hierarchy

### DB (`packages/db/`)
- [x] `AuthService` — register, login, refresh, logout, issue_tokens
- [x] `RefreshToken` model + repository (store/revoke)
- [x] `IntegrityError` handling on register
- [x] `last_login_at` on login

### API (`apps/api/`)
- [x] `routes/auth.py` — 5 endpoints
- [x] `deps.get_current_user` — cookie + Bearer → AuthError
- [x] CORS `allow_credentials=True` (restricted methods/headers)
- [x] Rate limiting (slowapi) on login/register/refresh
- [ ] `POST /v1/tasks` protected với `user_id`
- [ ] Task queries scoped `user_id` (403 cross-user)

### Security hardening (review fixes)
- [x] Refresh token `jti` stored + revoked on refresh/logout
- [x] Access token TTL 15 minutes
- [x] Login inactive → generic 401
- [x] `TokenTypeMismatchError` → `token_type_mismatch`
- [x] CORS least privilege
- [x] `app_env` Literal enum

### Tests (27 pass)
- [x] Unit: password roundtrip
- [x] Unit: JWT encode/decode/expired/type mismatch
- [x] Unit: RS256 roundtrip
- [x] Integration: register → login → me
- [x] Integration: refresh flow + rotation
- [x] Integration: logout revokes refresh
- [x] Integration: 401 without token
- [x] Integration: rate limit 429
- [x] Integration: inactive login generic error
- [x] Integration: display_name empty → null
- [x] Integration: last_login_at updated

### Email verification (planned)
- [ ] `email_verified` on User — xem [06-email-verification.md](./06-email-verification.md)
- [ ] `email_verification_codes` table
- [ ] `POST /verify-email`, `POST /resend-verification`
- [ ] Email backend (SMTP / Mailpit dev)
- [ ] Register flow change (no auto-login)

---

## Frontend checklist

### API layer
- [ ] `lib/api/client.ts` — `credentials: 'include'`, 401 → refresh → retry
- [ ] `lib/api/auth.ts` — login, register, logout, refresh, me

### Pages
- [ ] `(auth)/login/page.tsx` + `LoginForm`
- [ ] `(auth)/register/page.tsx` + `RegisterForm`
- [ ] `(auth)/verify-email/page.tsx` + `VerifyEmailForm` (sau email verification)
- [ ] Form validation zod + react-hook-form

### Guards
- [ ] `middleware.ts` — `/app/*` protected, guest redirect
- [ ] `AuthGuard` in `app/app/layout.tsx`
- [ ] `return_to` query handling

### UX
- [ ] Login error → inline message
- [ ] 401 global → toast + redirect `/login?return_to=`
- [ ] Logout từ sidebar/settings
- [ ] Verify email flow + resend cooldown

---

## Manual test scenarios

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Register new user | 201, redirect `/app`, cookie set |
| 2 | Login wrong password | 401, stay on `/login`, error shown |
| 3 | Access `/app` without login | Redirect `/login?return_to=/app` |
| 4 | Access `/login` when logged in | Redirect `/app` |
| 5 | Refresh page on `/app` | Still authenticated |
| 6 | Wait access expire + API call | Silent refresh, request succeeds |
| 7 | Logout then reuse old refresh | 401 on refresh |
| 8 | Logout | Cookies cleared, refresh revoked |
| 9 | User A cannot GET User B task | 403 |
| 10 | SSE stream without auth | 401, stream not started |
| 11 | Register → verify email → login | 201 no cookie → verify → login OK |
| 12 | 6th login attempt in 1 min | 429 rate limited |

---

## Definition of done

**Auth Slice hoàn thành khi:**

1. User register/login/logout qua Studio UI
2. `/app/*` không truy cập được khi chưa login
3. Cookies httpOnly — không token trong localStorage
4. API tasks gắn `user_id`, isolation giữa users
5. Silent refresh hoạt động khi access hết hạn
6. Backend pytest auth suite pass (**27/27 done**)
7. Email verified trước khi login (khi feature enabled)
8. Manual tests 1–8 pass (+ 11–12 khi có email verification)

**Backend-only milestone (hiện tại):** items 6 done; 1–5, 7–8 cần FE.

---

## Estimate & branch

| Item | Gợi ý |
|------|-------|
| Branch | `feature/auth` từ `develop` |
| Backend (done) | ~3 ngày |
| Email verification | ~2–3 ngày BE + ~1 ngày FE |
| Frontend | ~1–2 ngày |

---

## Sau Auth → tiếp theo

1. **Email verification** — [06-email-verification.md](./06-email-verification.md)
2. **Slice 1b:** Tasks CRUD (`POST/GET /v1/tasks`) — đã có `user_id` từ Auth.
