# DashZen Auth UI — Implementation Plan

> Plan chi tiết cho **Authentication UI & Route Guard** — Slice vertical Studio (FE).
>
> **Nguồn planner:** [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §2, §15 | [`01-project-structure-and-techstack.md`](../../../01-project-structure-and-techstack.md) §2.4 | [`UI/UX/phase-1-mvp-foundation.md`](../UX/phase-1-mvp-foundation.md) §3.1
>
> **Backend counterpart:** [`plan/phases/Backend/auth/`](../../Backend/auth/) — API đã implement.

---

## Trạng thái implement (cập nhật 2026-06-23)

| Thành phần | Trạng thái |
|------------|------------|
| Backend Auth API (MVP) | **Done** — xem [Backend 07](../../Backend/auth/07-implementation-status.md) |
| Auth UI MVP (login, verify, guards) | **Done** — xem [09](./09-implementation-status.md) |
| Account management (Phase 2) | **Chưa làm** — xem [10](./10-account-management.md) |
| Backend PATCH/change-password/delete | **Chưa làm** — blocker Phase 2 |

**Branch MVP:** `feature/auth-ui` · **Branch Phase 2:** `feature/account-management`

---

## Tài liệu trong thư mục

| File | Nội dung |
|------|----------|
| [00-prerequisites.md](./00-prerequisites.md) | Studio scaffold, env, backend chạy local |
| [01-auth-flow.md](./01-auth-flow.md) | User journeys + JWT/cookie flow (góc nhìn UI) |
| [02-module-architecture.md](./02-module-architecture.md) | Cấu trúc module, state, ranh giới với `modules/task` |
| [03-pages-components.md](./03-pages-components.md) | Pages, forms, layouts, component tree |
| [04-api-integration.md](./04-api-integration.md) | `client.ts`, `auth.ts`, types, error mapping |
| [05-route-guards.md](./05-route-guards.md) | Middleware, AuthGuard, `return_to`, SSE auth |
| [06-email-verification.md](./06-email-verification.md) | Màn verify OTP, resend, post-register flow |
| [07-design-ux.md](./07-design-ux.md) | Visual design, a11y, responsive, toast patterns |
| [08-checklist.md](./08-checklist.md) | Deliverables, test cases, definition of done |
| [09-implementation-status.md](./09-implementation-status.md) | Tracking implement (cập nhật khi code) |
| [10-account-management.md](./10-account-management.md) | Phase 2 — Profile CRUD, change password, delete account |
| [11-google-oauth.md](./11-google-oauth.md) | **Done** Google OAuth — Studio UI |
| [12-github-oauth.md](./12-github-oauth.md) | **Planned** GitHub OAuth — Studio UI |

**Master plans:** [`../../google-oauth-login.md`](../../google-oauth-login.md) · [`../../github-oauth-login.md`](../../github-oauth-login.md)

---

## Scope MVP (Phase 1)

| In scope | Out of scope (Phase 2+) |
|----------|-------------------------|
| Login / Register / Logout UI | OAuth GitHub → **Planned** [12-github-oauth.md](./12-github-oauth.md) |
| Google OAuth UI | **Done** — [11-google-oauth.md](./11-google-oauth.md) |
| Email verification (OTP 6 số) | Password reset / forgot password |
| httpOnly cookie session (không localStorage) | better-auth migration |
| Route guard `/app/*` + guest-only auth routes | Multi-tenant admin UI |
| Silent refresh qua `fetchWithAuth` | RBAC / role-based UI |
| `return_to` deep link sau login | Invite-only registration |
| 401 → toast + redirect login | Social login buttons |
| Profile hiển thị email + display name (read-only MVP) | Avatar upload, đổi email |
| Rate limit UX (429 toast) trên auth endpoints | CAPTCHA |

**Quyết định đã chốt:** Register **không** auto-login — redirect `/verify-email` sau `requires_verification: true` (align Backend as-built).

---

## Scope Phase 2 — Account Management

> Chi tiết đầy đủ: [10-account-management.md](./10-account-management.md)

| Tính năng | Trang / vị trí button |
|-----------|------------------------|
| **Profile Update** (display name) | `/app/profile` — `Edit profile` / `Save changes` / `Cancel` |
| **Change password** | `/app/settings` → card Security — `Change password` → dialog |
| **Delete account** | `/app/settings` → card Danger zone — `Delete account` → dialog |
| **Sign out** | `/app/settings` → card Session — `Sign out` (đã có MVP) |
| **Go to profile** | `/app/settings` → card Profile — link `Go to profile` |

**Out of scope Phase 2.1:** đổi email, avatar upload, forgot password — xem [10](./10-account-management.md) §1.

---

## Phụ thuộc

```
Auth UI (Slice)
    │
    ├── Backend Auth API running (localhost:8000)
    │       └── plan/phases/Backend/auth/
    ├── Docker: postgres + mailpit (dev email)
    ├── apps/studio — Next.js 15 scaffold
    ├── shadcn/ui + Tailwind (cần init trong studio)
    │
    ▼
UX Phase 1 — Sidebar, TaskContext, SSE (cần AuthGuard trước)
```

**Bước 0:** Backend + infra up — xem [00-prerequisites.md](./00-prerequisites.md)

---

## Thứ tự implement đề xuất

1. **Prerequisites:** shadcn init, env, API client skeleton — [00](./00-prerequisites.md)
2. **API layer:** `lib/api/client.ts` + `auth.ts` — [04](./04-api-integration.md)
3. **Auth module scaffold:** `modules/auth/` — [02](./02-module-architecture.md)
4. **Pages:** Login + Register — [03](./03-pages-components.md)
5. **Email verification:** Verify page + resend — [06](./06-email-verification.md)
6. **Guards:** `middleware.ts` + `AuthGuard` — [05](./05-route-guards.md)
7. **Polish:** Design tokens, a11y, error UX — [07](./07-design-ux.md)
8. **E2E manual:** register → verify → login → `/app` — [08](./08-checklist.md)

**Phase 2 (sau MVP):**

9. **Backend:** PATCH `/me`, change-password, delete account
10. **Account UI:** Profile edit + Settings dialogs — [10](./10-account-management.md)

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`Backend/auth/04-api-contracts.md`](../../Backend/auth/04-api-contracts.md) | Endpoint payloads, cookies, errors |
| [`Backend/auth/06-email-verification.md`](../../Backend/auth/06-email-verification.md) | OTP flow BE |
| [`UI/UX/phase-1-mvp-foundation.md`](../UX/phase-1-mvp-foundation.md) | §3.1 Auth & routing |
| [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) | §2, §15 authoritative |
| `apps/studio/` | Target app |
| `feature/auth-ui` | Git branch |
