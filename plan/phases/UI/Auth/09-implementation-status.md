# 09 — Implementation Status (Auth UI)

> **As-planned** — cập nhật file này khi implement từng phần.
>
> Last updated: **2026-06-23** — MVP done; Phase 2 plan added.

---

## Tổng quan

| Area | Status | Ghi chú |
|------|--------|---------|
| Plan docs | **Done** | `plan/phases/UI/Auth/` |
| Studio scaffold | **Done** | Next.js 15, auth routes |
| shadcn/ui init | **Done** | input, label, button, alert, skeleton, form, sonner |
| API client | **Done** | client.ts, errors.ts, auth.ts |
| Auth pages | **Done** | Login, Register, settings, profile |
| Route guards | **Done** | middleware.ts, AuthGuard.tsx |
| Email verification UI | **Done** | VerifyEmailForm, OtpInput |
| Tests (automated) | **Not started** | Manual QA MVP |
| Account management (Phase 2) | **Done** | [10-account-management.md](./10-account-management.md) |

---

## Phase 2 — Account management

| Item | Status |
|------|--------|
| Plan doc [10](./10-account-management.md) | ✅ |
| Backend PATCH `/me` | ✅ |
| Backend change-password | ✅ |
| Backend delete account | ✅ |
| Profile edit UI | ✅ |
| ChangePasswordDialog | ✅ |
| DeleteAccountDialog | ✅ |
| Settings sections (Security, Danger zone) | ✅ |

---

## File tracker

| File | Status |
|------|--------|
| `apps/studio/middleware.ts` | ✅ |
| `apps/studio/lib/api/client.ts` | ✅ |
| `apps/studio/lib/api/auth.ts` | ✅ |
| `apps/studio/lib/api/errors.ts` | ✅ |
| `apps/studio/modules/auth/components/LoginForm.tsx` | ✅ |
| `apps/studio/modules/auth/components/RegisterForm.tsx` | ✅ |
| `apps/studio/modules/auth/components/VerifyEmailForm.tsx` | ✅ |
| `apps/studio/modules/auth/components/OtpInput.tsx` | ✅ |
| `apps/studio/modules/auth/components/AuthGuard.tsx` | ✅ |
| `apps/studio/modules/auth/components/AuthLayout.tsx` | ✅ |
| `apps/studio/app/(auth)/login/page.tsx` | ✅ |
| `apps/studio/app/(auth)/register/page.tsx` | ✅ |
| `apps/studio/app/(auth)/verify-email/page.tsx` | ✅ |
| `apps/studio/app/(app)/layout.tsx` | ✅ |
| `apps/studio/app/(app)/page.tsx` | ✅ |
| `apps/studio/app/(app)/settings/page.tsx` | ✅ |
| `apps/studio/app/(app)/profile/page.tsx` | ✅ |

Legend: ⬜ Not started | 🟡 In progress | ✅ Done

---

## Backend dependency (ready)

| Backend item | Status |
|--------------|--------|
| `POST /v1/auth/register` + `requires_verification` | ✅ |
| `POST /v1/auth/verify-email` | ✅ |
| `POST /v1/auth/resend-verification` | ✅ |
| `POST /v1/auth/login` + cookies | ✅ |
| `POST /v1/auth/refresh` | ✅ |
| `POST /v1/auth/logout` | ✅ |
| `GET /v1/auth/me` | ✅ |
| Mailpit dev | ✅ |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-22 | Initial UI Auth plan created — 10 docs |
| 2026-06-23 | Auth MVP implemented; added 10-account-management.md (Phase 2) |
| 2026-06-23 | Phase 2 account management implemented (BE + FE) |

---

## Cập nhật khi implement

Khi hoàn thành mỗi milestone, cập nhật:

1. Bảng **Tổng quan** status
2. **File tracker** ⬜ → ✅
3. **Changelog** với ngày + mô tả ngắn
4. [08-checklist.md](./08-checklist.md) — tick items done
