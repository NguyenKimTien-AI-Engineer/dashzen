# DashZen UI — Phased Implementation

> Chia từ [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) và [`01-project-structure-and-techstack.md`](../../01-project-structure-and-techstack.md) §2.4 Frontend.
>
> **Nguồn sự thật gốc** vẫn là file planner — các phase/slice file này là bản triển khai có thứ tự, checklist, và phụ thuộc.

---

## Tổng quan

| Slice / Phase | Tên | Mục tiêu | Ưu tiên |
|---------------|-----|----------|---------|
| [**Auth**](./Auth/) | **Auth Slice** | Login, register, email verification, route guard, session | P0 |
| [UX Phase 1](./UX/phase-1-mvp-foundation.md) | MVP Foundation | App shell, chat, SSE, canvas preview | P0–P1 |
| [UX Phase 2](./UX/phase-2-core-ux.md) | Core UX | Streaming mượt, HITL đầy đủ, resilience | P1–P2 |
| [UX Phase 3](./UX/phase-3-polish-scale.md) | Polish & Scale | Export, prefs, i18n, discovery | P2–P3 |

> **Auth Slice** là prerequisite cho toàn bộ `/app/*`. Implement **trước** hoặc **song song đầu** Phase 1 UX.

---

## Phụ thuộc

```
Auth Slice (UI)
    │
    ├── Backend Auth API (done) — plan/phases/Backend/auth/
    ├── apps/studio scaffold
    ├── middleware + AuthGuard
    └── verify-email flow
            │
            ▼
UX Phase 1 — App shell, TaskContext, SSE
            │
            ▼
UX Phase 2 → Phase 3
```

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) | §2 Auth, §3 module, §15 errors |
| [`plan/phases/Backend/auth/`](../Backend/auth/) | API contracts, JWT, email verification BE |
| [`plan/phases/UI/UX/`](./UX/) | Chat, sidebar, canvas phases |
