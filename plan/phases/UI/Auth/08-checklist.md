# 08 — Auth UI Checklist & Definition of Done

> Slice Auth UI — deliverables, test cases, definition of done.
>
> Backend checklist: [Backend 05-checklist.md](../../Backend/auth/05-checklist.md)

---

## Prerequisites checklist

- [x] Backend API running (`localhost:8000`)
- [x] Docker postgres + mailpit up
- [x] `apps/studio` — shadcn init + dependencies — [00](./00-prerequisites.md)
- [x] `.env.local` — `NEXT_PUBLIC_API_URL`

---

## API layer checklist

- [x] `lib/api/client.ts` — `fetchWithAuth`, `fetchPublic`, refresh dedup
- [x] `lib/api/auth.ts` — all 7 auth functions
- [x] `lib/api/errors.ts` — `ApiError`, `mapFieldErrors`
- [x] `SessionExpiredError` → redirect login
- [x] `429` → `RateLimitError` + `Retry-After` parse

---

## Module & components checklist

- [x] `modules/auth/schemas/*` — zod login, register, verify
- [x] `AuthLayout.tsx`
- [x] `LoginForm.tsx` — react-hook-form
- [x] `RegisterForm.tsx`
- [x] `VerifyEmailForm.tsx` + `OtpInput.tsx`
- [x] `AuthGuard.tsx`
- [x] `useAuth`, `useMe`, `useVerifyEmail` hooks

---

## Pages checklist

- [x] `(auth)/layout.tsx` — centered, no sidebar
- [x] `/login` — guest only, `return_to`, `verified` banner
- [x] `/register` — redirect verify on success
- [x] `/verify-email` — OTP + resend cooldown
- [x] `(app)/layout.tsx` — AuthGuard wrap
- [x] `/app` — placeholder welcome (session proof)
- [x] `/app/settings` — logout button
- [x] `/app/profile` — read-only user info

---

## Guards checklist

- [x] `middleware.ts` — protected + guest redirects
- [x] Cookie name matches backend
- [x] `safeReturnTo` — no open redirect
- [x] AuthGuard loading skeleton
- [x] Logout clears query cache + authStore

---

## UX checklist

- [x] Inline validation errors (400)
- [x] Toast for global errors / success
- [x] `email_not_verified` → link verify
- [x] Dev Mailpit banner on verify page
- [x] Dark mode auth pages
- [x] Mobile responsive 375px

---

## Manual test scenarios

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Register new user | 201 → `/verify-email`, no cookie |
| 2 | Verify correct OTP (Mailpit) | → `/login?verified=1` |
| 3 | Login after verify | Cookies set → `/app` |
| 4 | Wrong password | 401, stay on login, error shown |
| 5 | Login unverified user | 403 `email_not_verified` alert |
| 6 | Access `/app` without login | Redirect `/login?return_to=/app` |
| 7 | Access `/login` when logged in | Redirect `/app` |
| 8 | Refresh `/app` page | Still authenticated |
| 9 | Wait access expire + navigate | Silent refresh via `useMe` / API |
| 10 | Logout | Cookies cleared → `/login` |
| 11 | `return_to=/app/settings` after login | Land on settings |
| 12 | Invalid `return_to=https://evil.com` | Fallback `/app` |
| 13 | Resend OTP | Cooldown works, new code in Mailpit |
| 14 | Wrong OTP 5x | `too_many_attempts` |
| 15 | Register duplicate email | 409 inline error |
| 16 | 6th login in 1 min | 429 toast |

---

## Automated tests (Phase 2 — không block MVP)

| Layer | Tool | Scope |
|-------|------|-------|
| Unit | Vitest | zod schemas, `safeReturnTo`, error mappers |
| Component | RTL | LoginForm validation |
| E2E | Playwright | Scenarios 1–4, 6–8 |

Auth UI MVP ship với **manual tests 1–16 pass**.

---

## Definition of done

**Auth UI Slice hoàn thành khi:**

1. User register → verify email → login qua Studio UI end-to-end
2. `/app/*` không truy cập khi chưa login
3. Không JWT trong localStorage/sessionStorage
4. Silent refresh hoạt động khi access hết hạn (manual test 9)
5. Logout revoke session phía client + server
6. `email_not_verified` và verify/resend flows hoạt động
7. Manual tests **1–16** pass
8. Code trên branch `feature/auth-ui` — PR vào `develop`

---

## Estimate & branch

| Item | Gợi ý |
|------|-------|
| Branch | `feature/auth-ui` từ `develop` |
| Scaffold + API client | 0.5 ngày |
| Login + Register | 0.5 ngày |
| Verify email + resend | 0.5 ngày |
| Guards + polish + manual QA | 0.5–1 ngày |
| **Total** | **~2–2.5 ngày** |

---

## Phase 2 — Account management checklist

> Chi tiết + vị trí button: [10-account-management.md](./10-account-management.md)

### Backend (blocker)

- [ ] `PATCH /v1/auth/me` — update `display_name`
- [ ] `POST /v1/auth/change-password`
- [ ] `DELETE /v1/auth/me` — password + confirmation
- [ ] Unit/integration tests

### API layer

- [ ] `updateProfile`, `changePassword`, `deleteAccount` in `auth.ts`
- [ ] Error codes: `invalid_credentials` on wrong password

### Components

- [ ] `ProfileEditForm` + Edit/Save/Cancel on `/app/profile`
- [ ] `ChangePasswordDialog` — triggered from Settings Security card
- [ ] `DeleteAccountDialog` — triggered from Settings Danger zone
- [ ] Settings: Profile link card, Security card, Danger zone card
- [ ] Hooks: `useUpdateProfile`, `useChangePassword`, `useDeleteAccount`
- [ ] Schemas: profile, change-password, delete-account

### Manual tests (17–26)

- [ ] Scenarios in [10](./10-account-management.md) §12

---

## Sau Auth UI → tiếp theo

1. **Account management Phase 2** — [10-account-management.md](./10-account-management.md)
2. **UX Phase 1** — [phase-1-mvp-foundation.md](../UX/phase-1-mvp-foundation.md): Sidebar, TaskContext, SSE
3. **App shell** — thay placeholder `/app` bằng chat home
4. **SSE auth** — `TaskConnection` credentials + 401 handling — [05](./05-route-guards.md) §6
