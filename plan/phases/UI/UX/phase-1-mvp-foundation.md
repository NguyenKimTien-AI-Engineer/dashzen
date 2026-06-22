# Phase 1 — MVP Foundation

> **Mục tiêu:** Ship DashZen Studio — webapp chat-first tạo dashboard end-to-end.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) §1.1, §19 MVP, §2–§9 (subset), §11, §15 (core)
>
> **Ưu tiên:** P0–P1 | **Phụ thuộc:** Backend auth, tasks API, SSE stream, gates API

---

## 1. Vision & scope

DashZen Studio là **webapp chat-first**: user mô tả dashboard bằng ngôn ngữ tự nhiên, main orchestrator điều phối sub-agents, kết quả hiển thị song song trên **canvas preview**.

```
┌──────────────────────────────────────────────────────────────────┐
│ Sidebar          │  Chat Workspace          │  Canvas (optional) │
│ • New Dashboard  │  messages + agent blocks │  dashboard preview │
│ • Recents        │  input + Ask/Auto        │  live widgets      │
│ • Settings       │                          │                    │
└──────────────────────────────────────────────────────────────────┘
```

### Không thuộc Phase 1 (defer)

- Context donut, manual compact
- `streamingActivities` interleaved timeline
- Regenerate / branch navigation / edit message
- `ask_user` form ActionCard (phức tạp hơn Y/N)
- Extended thinking display đầy đủ
- File attach, Quick Action Chips (Connect Data, Template)
- Export / share, debug trace, user prefs, i18n
- ReconnectBanner, virtualization, rate limit UI chi tiết

---

## 2. Tech foundation

| Layer | Công nghệ | Ghi chú |
|-------|-----------|---------|
| Framework | Next.js 15 App Router | SSR + RSC |
| Language | TypeScript 5.x strict | `"strict": true` |
| Styling | Tailwind CSS 4 | CSS variables theme |
| Components | shadcn/ui + Radix | Copy-paste |
| Icons | lucide-react | |
| Forms | react-hook-form + zod | Login, settings |
| Server state | TanStack Query v5 | CRUD tasks/messages |
| Chat streaming | `useReducer` + TaskContext | **Không** Zustand cho chat core |
| UI ephemeral | Zustand | Sidebar, theme, toast |
| Streaming | fetch ReadableStream (SSE) | Native |
| Auth | JWT + httpOnly cookie | |
| Markdown | react-markdown + remark-gfm | |
| Code highlight | shiki | Tree-shakable |

### Module structure (cần scaffold)

```
apps/studio/
├── app/(auth)/login, register
├── app/(app)/layout, page, task/[taskId], dashboard/[pageId], settings, profile
├── modules/task/
│   ├── contexts/     task-context, task-reducer, task-connection
│   ├── hooks/        useTask, useGate, useStreamScroll, useTaskMessages
│   ├── components/   chat/*, canvas/*, layout/*
│   └── types/        stream-events, task-state
├── components/       auth/, ui/, shared/ (Toast, ErrorBoundary, Skeleton)
└── lib/              api/, stores/
```

---

## 3. Deliverables checklist

### 3.1 Authentication & routing (§2)

- [ ] `POST /v1/auth/login` → httpOnly cookie
- [ ] `POST /v1/auth/refresh` — silent refresh
- [ ] `AuthGuard` + Next.js middleware
- [ ] JWT expiry mid-session → auto refresh; fail → redirect `/login?return_to=`
- [ ] 401 trong SSE stream → stop stream → toast → redirect
- [ ] Routes:

| Route | Auth | Mô tả |
|-------|------|-------|
| `/login`, `/register` | Guest only | Redirect `/app` nếu đã login |
| `/app` | Protected | Task home — empty chat + onboarding |
| `/app/task/[taskId]` | Protected | Task conversation + canvas |
| `/app/dashboard/[pageId]` | Protected | Full-screen preview |
| `/app/settings` | Protected | Settings |
| `/app/profile` | Protected | Profile |

### 3.2 App shell & sidebar (§3, §4)

- [ ] Layout: Sidebar + AuthGuard + workspace chat/canvas
- [ ] **New Dashboard** → `POST /v1/tasks` → navigate `/app/task/{id}`
- [ ] **Recents** → `GET /v1/tasks` — title, status icon, relative time
- [ ] Recents: skeleton loading (3–5 items), empty state CTA
- [ ] Recents item: click → `/app/task/[taskId]`
- [ ] **Settings** → `/app/settings`
- [ ] Sidebar states: Loading / Empty / Error (retry) / Collapsed (mobile icon-only)
- [ ] Zustand `sidebarStore` — collapse state

### 3.3 State management core (§3.1, §7.2 subset)

- [ ] `TaskContext` — Provider: send, stop
- [ ] `task-reducer` — subset actions cho MVP:

| Action | Trigger | UI Effect |
|--------|---------|-----------|
| `STREAM_START` | sendMessage | Optimistic user msg, disable input |
| `STREAM_DELTA` | `main_text` | Append assistant text |
| `TOOL_PENDING` | gate init | ActionCard Y/N |
| `TOOL_START` | `main_tool` | Tool chip running |
| `TOOL_RESULT` | `main_result` | Tool chip done |
| `TOOL_DECISION` | gate resolved | Resume stream |
| `AGENT_START` | `agent_start` | Open agent block |
| `AGENT_EVENT` | `agent_text/tool/result` | Update timeline |
| `AGENT_DONE` | `agent_done` | Collapse + summary |
| `STREAM_ARTIFACT` | `file_artifact` | Update canvas |
| `SET_TASK_META` | `task_meta` | Sidebar title |
| `STREAM_END` | `stream_done` | Bridge → refetch |
| `STREAM_ERROR` | `stream_error` | Error + retry |
| `SET_MESSAGES` | refetch | Replace streaming → DB |
| `RESET` | navigate away | Clear state |

- [ ] TanStack Query — refetch messages sau `STREAM_END`
- [ ] Custom hooks: `useTask`, `useGate`, `useStreamScroll`, `useTaskMessages`

### 3.4 SSE integration (§7 — core)

- [ ] `TaskConnection` component — keyed remount (`key={streamKey}`)
- [ ] `onEvent` → dispatch reducer; `onEnd` → refetch messages
- [ ] Stop stream: `POST /v1/tasks/{id}/stop`
- [ ] 409 `still_processing` — handling cơ bản (retry đầy đủ → Phase 2)
- [ ] Client disconnect → backend tiếp tục; user quay lại → `GET /messages` + `GET /artifacts` restore

### 3.5 Chat input (§5 — core)

- [ ] Textarea auto-resize (max 6 rows)
- [ ] `Shift+Enter` newline; `Enter` send
- [ ] **Ask / Auto** toggle — Ask = Redis gate; Auto = chạy thẳng
- [ ] Send — disabled khi empty hoặc streaming
- [ ] Stop — visible khi streaming
- [ ] Input states: `idle` → `sending` → `streaming` → `idle` | `error`
- [ ] Focus management: auto-focus mount, sau send, sau `STREAM_END`

### 3.6 Task conversation view (§6 — basic)

**Message types:**

| Loại | Hiển thị | SSE |
|------|----------|-----|
| User | Bubble phải | Optimistic + DB |
| Assistant | Bubble trái, markdown | `main_text` |
| Tool chip | Inline + status + expandable result | `main_tool` / `main_result` |
| Agent block | Collapsible card, timeline | `agent_*` |
| Action card | Y/N approve (Ask mode) | pending gate |
| Dashboard ready | Card + Open Preview | `file_artifact` |
| Error | Red alert + retry | `stream_error` |

- [ ] Markdown: react-markdown + remark-gfm + shiki
- [ ] Links: `target="_blank" rel="noopener noreferrer"`
- [ ] **Agent Activity Block basic** — open / timeline / close / summary
- [ ] Reload từ `AgentRun.activities` JSON khi refresh page
- [ ] **ActionCard Y/N** — tool approval Ask mode → `POST /gates/tool`
- [ ] **DashboardReadyCard** — thumbnail + Open Preview
- [ ] Auto-scroll khi streaming (`useStreamScroll`)
- [ ] Message metadata on hover: timestamp

### 3.7 Dashboard canvas (§8 — basic)

- [ ] Split view `/app/task/[taskId]` — chat ~60% + canvas ~40%
- [ ] `file_artifact` SSE → hot-reload preview
- [ ] Canvas toggle — mở/đóng panel (localStorage persist)
- [ ] Canvas lazy mount — chỉ render khi có artifact
- [ ] Full-screen `/app/dashboard/[pageId]` — Back to task, Continue in chat
- [ ] `WidgetErrorBoundary` per widget → placeholder khi fail

### 3.8 UX patterns (§9 — MVP subset)

**Skeleton loaders:**

| Component | Loading UI |
|-----------|------------|
| SidebarRecents | 3–5 skeleton lines |
| ChatMessageList | 2–3 skeleton bubbles |
| DashboardCanvas | Skeleton grid KPI/chart |
| DashboardReadyCard | Thumbnail skeleton |

**Empty states:**

| Screen | UI |
|--------|-----|
| ChatHome | Illustration + CTA + welcome prompts |
| SidebarRecents | "Chưa có dashboard nào" |
| ChatMessageList (new task) | Welcome + example prompts |
| DashboardCanvas | "Dashboard preview sẽ hiện ở đây" |

**Toast system** (Zustand `useToastStore`):

| Trigger | Toast |
|---------|-------|
| Stream error | Error + retry |
| 401 JWT expired | Warning + "Đăng nhập lại" |
| 500 server error | Error + "Thử lại sau" |
| Network offline | Persistent warning |
| Copy message | Success "Đã sao chép" |

**Optimistic updates:** send message, delete/rename task, gate approve/reject

### 3.9 Error handling (§3.4, §15 — core)

**Error boundary hierarchy:**

```
RootErrorBoundary
  AuthGuard → AppLayout
    SidebarErrorBoundary
    TaskErrorBoundary
      CanvasErrorBoundary
        WidgetErrorBoundary (per widget)
```

**API client interceptor:**

- [ ] 401 → try refresh → retry once → redirect login
- [ ] 400 → inline form error
- [ ] 403 → toast "Không có quyền"
- [ ] 404 → redirect home hoặc inline
- [ ] 409 → toast + disable (SSE retry → Phase 2)
- [ ] 429 → toast warning (full UI → Phase 2)
- [ ] 500/503 → toast + retry

### 3.10 Accessibility & responsive (§12, §14 — basic)

- [ ] `ChatMessageList`: `role="log"` + `aria-live="polite"`
- [ ] `ActionCard`: `role="dialog"` + focus trap
- [ ] Toast: `role="alert"`
- [ ] Skeleton: `aria-busy="true"`
- [ ] Keyboard: Enter send, Shift+Enter newline, Tab ActionCard buttons
- [ ] Focus rings rõ ràng; error = màu + icon + text
- [ ] Theme: dark/light via Zustand + CSS variables + localStorage
- [ ] Breakpoints: mobile sidebar hamburger; tablet collapsible; desktop 3-column

---

## 4. Definition of done

Phase 1 hoàn thành khi user có thể:

1. Đăng nhập / đăng xuất, được bảo vệ route `/app/*`
2. Tạo task mới từ sidebar, thấy trong recents
3. Gửi prompt (Ask/Auto), nhận stream assistant + sub-agent blocks
4. Approve/reject tool trong Ask mode qua ActionCard Y/N
5. Thấy dashboard preview live khi agent tạo spec
6. Mở full-screen preview và quay lại chat
7. Refresh page → messages + agent activities restore
8. Gặp lỗi → toast / error card / boundary không crash app

---

## 5. Out of scope (→ Phase 2/3)

Xem [`phase-2-core-ux.md`](./phase-2-core-ux.md) và [`phase-3-polish-scale.md`](./phase-3-polish-scale.md).
