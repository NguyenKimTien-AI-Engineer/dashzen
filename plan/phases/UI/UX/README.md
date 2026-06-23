# DashZen UI/UX — Phased Implementation

> Chia từ [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) (§19 authoritative).
>
> **Nguồn sự thật gốc** vẫn là file planner — các phase file này là bản triển khai có thứ tự, checklist, và phụ thuộc.

---

## Tổng quan

| Slice / Phase | Tên | Mục tiêu | Ưu tiên |
|---------------|-----|----------|---------|
| [**Auth**](../Auth/) | **Auth Slice** | Login, register, verify email, route guard | P0 |
| [Phase 1](./phase-1-mvp-foundation.md) | MVP Foundation | Ship webapp chat-first có thể tạo dashboard end-to-end | P0–P1 |
| [Phase 2](./phase-2-core-ux.md) | Core UX | Streaming mượt, HITL đầy đủ, resilience, performance | P1–P2 |
| [Phase 3](./phase-3-polish-scale.md) | Polish & Scale | Export, prefs, i18n, discovery features | P2–P3 |
| [Sidebar shell](./04-sidebar-shell.md) | Sidebar Shell | Claude-inspired collapse, nav, user menu | P0 (shell) |

---

## Phụ thuộc giữa các phase

```
Auth Slice (UI)          ← plan/phases/UI/Auth/
    │
    ▼
Phase 1 (MVP)
    │
    ├── App shell + Sidebar (AuthGuard từ Auth slice)
    ├── TaskContext + SSE cơ bản
    ├── Chat + HITL Y/N + Agent block basic
    └── Canvas preview basic
            │
            ▼
Phase 2 (Core UX)
    │
    ├── streamingActivities + message reload
    ├── Resilience (retry, reconnect, errorKind)
    ├── Context donut + thinking + branch/regenerate
    └── Performance (virtualization, rate limit UI)
            │
            ▼
Phase 3 (Polish)
    │
    ├── Export / share / print
    ├── User prefs + i18n
    └── Discovery (Cmd+K, templates, onboarding tour)
```

---

## Mapping section → phase

| Section planner | Phase |
|-----------------|-------|
| §1 Vision, §1.1 Base features | 1 |
| §2 Auth & Route Guard | 1 |
| §3 Module & State (core) | 1 |
| §4 Sidebar (basic) | 1 |
| §5 Chat Input (core) | 1 → 2 (chips, token estimate) |
| §6 Conversation (basic messages + ActionCard Y/N) | 1 → 2 (donut, reconnect, thinking) |
| §7 SSE (core + basic 409) | 1 → 2 (retry, errorKind, reconnect) |
| §8 Canvas (basic split + fullscreen) | 1 → 2 (resize, responsive toggle) |
| §9 UX Patterns (skeleton, toast, empty, scroll) | 1 → 2 (FAB) |
| §10 UI bổ sung | 2 → 3 (prefs) |
| §11 Tech Stack | 1 (foundation) |
| §12 Accessibility | 1 (basic) → 2 (shortcuts) |
| §13 Performance | 2 |
| §14 Theme & Responsive | 1 (breakpoints) → 2 (canvas viewport) |
| §15 API Error Handling | 1 (core) → 2 (rate limit UI) |
| §16 Testing | 2+ |
| §17–18 SSE mapping & data flow | 1 (subset) → 2 (full) |
| §19 MVP vs Phase | **Authoritative split** |
| §20 Gaps Checklist | Cross-phase tracking |

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`01-project-structure-and-techstack.md`](../../01-project-structure-and-techstack.md) | SSE schema, rate limits, subsystem |
| [`03-agent-runtime-and-memory.md`](../../03-agent-runtime-and-memory.md) | Gates FSM, recovery |
| [`04-dashboard-spec-schema.md`](../../04-dashboard-spec-schema.md) | WidgetRenderer |
| [`06-api-contracts.md`](../../06-api-contracts.md) | OpenAPI, branching, headers |
| [`plan/phases/UI/Auth/`](../Auth/) | Auth UI slice — forms, guards, verify email |
| [`plan/phases/Backend/auth/`](../../Backend/auth/) | Auth API as-built |
