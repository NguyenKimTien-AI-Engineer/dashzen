# 00 — Prerequisites & Scope (UI Phase 1)

> Đọc file này **trước** khi implement bất kỳ component UI Phase 1 nào.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §1, §19 | [`Backend/agent/phase-1/`](../../Backend/agent/phase-1/)

---

## 1. Vision UI Phase 1

UI Phase 1 biến Backend Agent Phase 1 thành trải nghiệm người dùng hoàn chỉnh trên trình duyệt:

```
User login (đã có)
  → New Dashboard → POST /v1/tasks
  → Navigate /app/task/{id}
  → Gõ prompt → POST /v1/tasks/{id}/stream (SSE)
  → UI hiển thị: main_text, agent block, tool chips, file_artifact
  → stream_done → refetch messages + artifacts
  → Panel phải preview spec.md (markdown)
```

Đây là **minimum viable chat UI** — chưa cần dashboard render thật (`WidgetRenderer`), chưa cần Ask mode.

---

## 2. Điểm xuất phát hiện tại (Studio)

| Thành phần | Trạng thái | Ghi chú |
|------------|------------|---------|
| `modules/auth/` | Done | Login, Register, AuthGuard, useMe |
| `lib/api/client.ts` | Done | fetchWithAuth, 401 refresh, 429 |
| `modules/layout/` | Partial | AppSidebar, AppShell — chưa task recents thật |
| `app/app/page.tsx` | Placeholder | "Task chat will be available in the next phase" |
| `app/app/chats/page.tsx` | Placeholder | "Coming soon" |
| `modules/task/` | **Chưa có** | Cần tạo mới |
| `lib/api/tasks.ts` | **Chưa có** | Cần tạo mới |
| `/app/task/[taskId]` | **Chưa có** | Route chính Phase 1 |

---

## 3. Backend API sẵn sàng (Phase 1)

UI Phase 1 **chỉ** gọi các endpoint sau — không giả định API Phase 2:

| Method | Path | UI dùng cho |
|--------|------|-------------|
| `POST` | `/v1/tasks` | New Dashboard |
| `GET` | `/v1/tasks` | Sidebar recents |
| `GET` | `/v1/tasks/{id}` | Task detail |
| `PATCH` | `/v1/tasks/{id}` | Rename task |
| `DELETE` | `/v1/tasks/{id}` | Delete task |
| `GET` | `/v1/tasks/{id}/messages` | Load history + post-stream refetch |
| `GET` | `/v1/tasks/{id}/artifacts` | Load files + post-stream refetch |
| `POST` | `/v1/tasks/{id}/stream` | SSE streaming |
| `POST` | `/v1/tasks/{id}/stop` | Stop button |
| `GET` | `/v1/llm/budget` | Chuẩn bị Phase 2 (optional fetch, không hiển thị donut) |

**Không có trong BE Phase 1:** `/gates/*`, `/compact`, `/upload`, branching APIs.

---

## 4. SSE events — subset UI Phase 1

Mirror types từ `packages/agents/src/agents/streaming/events.py`. UI **phải handle**:

| Event | Reducer action | UI effect |
|-------|----------------|-----------|
| `heartbeat` | (ignore) | Không render |
| `main_text` | `STREAM_DELTA` | Assistant text streaming |
| `main_think` | `STREAM_THINKING_DELTA` | Collapsible thinking (optional P1) |
| `main_tool` | `TOOL_START` | Tool chip running |
| `main_result` | `TOOL_RESULT` | Tool chip done |
| `agent_start` | `AGENT_START` | Mở agent block |
| `agent_text` | `AGENT_EVENT` | Text trong block |
| `agent_think` | `AGENT_EVENT` | Thinking trong block |
| `agent_tool` | `AGENT_EVENT` | Timeline entry |
| `agent_result` | `AGENT_EVENT` | Timeline result |
| `agent_done` | `AGENT_DONE` | Summary + collapse |
| `file_artifact` | `STREAM_ARTIFACT` | Cập nhật preview panel |
| `task_meta` | `SET_TASK_META` | Cập nhật title sidebar |
| `stream_done` | `STREAM_END` | Refetch messages/artifacts |
| `stream_error` | `STREAM_ERROR` | Error card + retry |

**Không handle Phase 1:** `main_ask` (chưa emit từ BE).

---

## 5. Nguyên tắc thiết kế UI Phase 1

| # | Nguyên tắc | Áp dụng |
|---|------------|---------|
| 1 | Chat state = `useReducer` | Không Zustand cho streaming |
| 2 | CRUD = TanStack Query | Tasks, messages, artifacts |
| 3 | SSE = component keyed remount | `TaskConnection key={streamKey}` |
| 4 | Không hardcode budget numbers | Dùng `GET /v1/llm/budget` khi cần |
| 5 | Fail locally | TaskErrorBoundary — chat crash không kill app |
| 6 | Optimistic user message | Hiện ngay khi Send, trước first SSE byte |
| 7 | Auto mode only | Hiện badge "Auto" — không toggle Ask |

---

## 6. Module structure mục tiêu

```
apps/studio/
├── app/
│   └── app/
│       ├── page.tsx                    # ChatHome — empty state + quick start
│       └── task/[taskId]/page.tsx      # Task conversation + preview
├── modules/task/
│   ├── contexts/
│   │   ├── task-context.tsx
│   │   ├── task-reducer.ts
│   │   └── task-connection.tsx
│   ├── hooks/
│   │   ├── useTask.ts
│   │   ├── useTaskMessages.ts
│   │   └── useStreamScroll.ts
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatHome.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatMessageList.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── AgentActivityBlock.tsx
│   │   │   ├── ToolActivityChip.tsx
│   │   │   └── StreamErrorCard.tsx
│   │   └── preview/
│   │       └── SpecPreviewPanel.tsx
│   └── types/
│       ├── stream-events.ts
│       └── task-state.ts
└── lib/api/
    └── tasks.ts
```

---

## 7. Wireframe Phase 1

```
┌─ Sidebar ─────────┬─ Chat (65%) ────────────────┬─ Preview (35%) ──┐
│ DashZen           │ User: Tạo dashboard...       │ spec.md          │
│ ⊕ New Dashboard   │                              │ (markdown render)│
│ 🔍 Search         │ ┌─ Dashboard Planner ── ▼ ─┐ │                  │
│                   │ │ ✓ write_file spec.md     │ │                  │
│ RECENTS           │ │ Summary: 4 widgets...    │ │                  │
│ ● Revenue dash    │ └──────────────────────────┘ │                  │
│                   │ Assistant: Đã tạo spec...    │                  │
│ ⚙ Settings        │ ┌─────────────────────────┐  │                  │
│                   │ │ prompt...  Auto  ↑Send  │  │                  │
│                   │ └─────────────────────────┘  │                  │
└───────────────────┴──────────────────────────────┴──────────────────┘
```

Preview panel có thể ẩn trên mobile — chat full width.

---

## 8. Constants & env

| Biến | Mục đích |
|------|----------|
| `NEXT_PUBLIC_API_URL` | Base URL API (`http://localhost:8000`) |
| Cookie JWT | Auto qua `credentials: "include"` |

Không cần env mới cho Phase 1 UI.

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [01-foundation-and-routes.md](./01-foundation-and-routes.md) | Bước implement đầu tiên |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §17 | Full SSE mapping |
| [`Backend/agent/phase-1/10-checklist.md`](../../Backend/agent/phase-1/10-checklist.md) | BE DoD đối chiếu |
