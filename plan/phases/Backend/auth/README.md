# DashZen Auth — Implementation Plan

> Plan chi tiết cho **Authentication & Route Guard** — Slice 1 vertical (BE + FE).
>
> **Nguồn planner:** [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §2, §15 | [`01-project-structure-and-techstack.md`](../../../01-project-structure-and-techstack.md) §16, §17 | [`phase-1-foundation.md`](../phase-1-foundation.md) §3.8

---

## Trạng thái implement (cập nhật 2026-06-22)

| Thành phần | Trạng thái |
|------------|------------|
| Backend Auth (JWT, cookies, routes) | **Done** |
| Security hardening (review fixes) | **Done** — xem [07-implementation-status.md](./07-implementation-status.md) |
| Frontend Auth (Studio) | **Planned** — xem [UI/Auth](../../UI/Auth/) |
| Email verification (BE) | **Done** — xem [06-email-verification.md](./06-email-verification.md) |
| Email verification (UI) | **Planned** — xem [UI/Auth/06](../../UI/Auth/06-email-verification.md) |

---

## Tài liệu trong thư mục

| File | Nội dung |
|------|----------|
| [00-docker-postgres.md](./00-docker-postgres.md) | **Docker Compose PostgreSQL** — prerequisite Auth |
| [01-jwt-flow.md](./01-jwt-flow.md) | JWT flow chuẩn (7 bước) ↔ DashZen mapping |
| [02-backend.md](./02-backend.md) | FastAPI: models, routes, middleware, deps |
| [03-frontend.md](./03-frontend.md) | Next.js: middleware, AuthGuard, API client |
| [04-api-contracts.md](./04-api-contracts.md) | Endpoints, payloads, cookies, errors |
| [05-checklist.md](./05-checklist.md) | Deliverables, test cases, definition of done |
| [06-email-verification.md](./06-email-verification.md) | **Đề xuất** Email OTP verification sau register |
| [07-implementation-status.md](./07-implementation-status.md) | **As-built** — những gì đã code & hardening |
| [08-google-oauth.md](./08-google-oauth.md) | **Planned** Google OAuth login — backend |
| [09-google-oauth-checklist.md](./09-google-oauth-checklist.md) | Checklist triển khai Google OAuth |

**Master plan OAuth:** [`../../google-oauth-login.md`](../../google-oauth-login.md)

---

## Scope MVP (Phase 1)

| In scope | Out of scope (Phase 2+) |
|----------|-------------------------|
| Login / Register / Logout | OAuth (Google, GitHub) → **Google planned** [08-google-oauth.md](./08-google-oauth.md) |
| JWT access + refresh (server-side revocation) | better-auth migration |
| **httpOnly cookie** (khuyến nghị) | Multi-tenant admin |
| Bearer header (fallback) | Invite gate |
| Route guard `/app/*` | Password reset email |
| Silent refresh | RBAC phức tạp |
| 401 → refresh → redirect | |
| Task ownership `user_id` | |
| Rate limiting auth endpoints | |
| RS256 support (optional) | |
| **Email verification (OTP 6 số)** | → [06-email-verification.md](./06-email-verification.md) |

**Quyết định đã chốt (plan 01 §17):** Single-user MVP, interface sẵn multi-tenant (`user_id` trên Task).

---

## Phụ thuộc

```
Auth (Slice 1)
    │
    ├── Docker PostgreSQL (infra/compose)  ← 00-docker-postgres.md
    │       └── DATABASE_URL → localhost:5432
    ├── User model + Alembic migration 001, 002
    ├── Redis — không cần cho Auth Slice (refresh tokens trong Postgres)
    │
    ▼
Tasks API (Slice 1b) — cần get_current_user
Studio shell — cần login redirect
Email verification — sau Auth hardening
```

**Bước 0 (bắt buộc):** `docker compose -f infra/compose/docker-compose.yml up -d`

---

## Thứ tự implement đề xuất

0. **Infra:** Docker Postgres up — xem [00-docker-postgres.md](./00-docker-postgres.md)
1. ~~**Backend:** User model + migration → password hash → login/register → JWT cookies → deps `get_current_user`~~ **Done**
2. ~~**Backend:** refresh + logout + token revocation → rate limit~~ **Done**
3. **Email verification:** OTP + SMTP — xem [06-email-verification.md](./06-email-verification.md)
4. **Frontend:** `lib/api/client.ts` + `auth.ts` → login/register forms
5. **Frontend:** `middleware.ts` + `AuthGuard` → route protection
6. **E2E:** login → tạo task → 401 recovery

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`UI/Auth/`](../../UI/Auth/) | **Auth UI plan** — forms, guards, verify email |
| [`UI/UX/phase-1-mvp-foundation.md`](../../UI/UX/phase-1-mvp-foundation.md) | §3.1 Auth & routing |
| [`Backend/phase-1-foundation.md`](../phase-1-foundation.md) | §3.8 API auth |
| [00-docker-postgres.md](./00-docker-postgres.md) | Docker DB setup |
| [07-implementation-status.md](./07-implementation-status.md) | Code đã merge |
| `infra/compose/docker-compose.yml` | Postgres service |
| `.env.example` | `DATABASE_URL`, `JWT_*`, rate limit |
