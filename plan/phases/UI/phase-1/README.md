# UI Phase 1 — Chat Agent kết nối Backend Phase 1

> Plan triển khai chi tiết cho **Studio UI Phase 1** — kết nối với Backend Agent Phase 1 đã hoàn thành.
>
> **Mục tiêu:** User đăng nhập → tạo task → gửi prompt → thấy streaming chat + agent activity + preview `spec.md` — end-to-end trên trình duyệt.

---

## Trạng thái

| Thành phần | Trạng thái |
|------------|------------|
| Auth UI (login, guard, session) | **Done** — [`auth/`](../../Backend/auth/) |
| App shell (sidebar, layout) | **Partial** — shell có, chưa wire tasks |
| API client tasks/stream | Planned |
| TaskContext + reducer | Planned |
| SSE TaskConnection | Planned |
| Chat conversation view | Planned |
| Artifact preview panel | Planned |
| E2E UI Phase 1 | Planned |

---

## Tài liệu trong thư mục

| File | Nội dung |
|------|----------|
| [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md) | Scope, phụ thuộc BE Phase 1, in/out |
| [01-foundation-and-routes.md](./01-foundation-and-routes.md) | Routes, layout, module scaffold |
| [02-api-client-and-types.md](./02-api-client-and-types.md) | `tasks.ts`, SSE types mirror BE |
| [03-task-context-and-reducer.md](./03-task-context-and-reducer.md) | TaskContext, reducer subset Phase 1 |
| [04-sse-task-connection.md](./04-sse-task-connection.md) | TaskConnection, keyed remount, stop |
| [05-sidebar-and-navigation.md](./05-sidebar-and-navigation.md) | Recents, New Dashboard, task_meta |
| [06-chat-input-and-controls.md](./06-chat-input-and-controls.md) | Textarea, Send, Stop, Auto mode |
| [07-conversation-view.md](./07-conversation-view.md) | Messages, agent blocks, tool chips |
| [08-artifact-preview-panel.md](./08-artifact-preview-panel.md) | Split view, spec.md markdown preview |
| [09-ux-patterns-and-errors.md](./09-ux-patterns-and-errors.md) | Toast, skeleton, error boundary, scroll |
| [10-checklist.md](./10-checklist.md) | Definition of Done, test cases |

---

## Scope Phase 1 UI

### In scope

| Hạng mục | Chi tiết |
|----------|----------|
| Routes | `/app`, `/app/task/[taskId]` |
| Task CRUD | TanStack Query — list, create, delete, rename |
| SSE stream | Toàn bộ events Backend Phase 1 hỗ trợ |
| Chat core | User bubble, assistant markdown, tool chip, agent block |
| Stop | `POST /v1/tasks/{id}/stop` |
| Preview | Markdown panel cho `spec.md` khi `file_artifact` |
| Mode | **Auto only** — badge tĩnh, chưa Ask/HITL |
| Auth | Dùng JWT flow đã có |

### Out of scope (UI Phase 2+)

| Hạng mục | Lý do defer |
|----------|-------------|
| Ask mode + ActionCard (gates) | Backend Phase 2 — chưa có `/gates/*` |
| Context donut + manual compact | Backend Phase 2 |
| Regenerate / branch navigation | Backend Phase 2 |
| Full `WidgetRenderer` dashboard | Cần spec schema + builder agent |
| File attach / upload | Backend Phase 2 |
| Virtualized message list | Performance — Phase 2 |
| ReconnectBanner retry đầy đủ | Phase 2 |
| Rate limit UI | Backend Phase 2 |

---

## Phụ thuộc

```
Backend Auth (Done) ──► JWT cookie, fetchWithAuth
       │
Backend Agent Phase 1 (Done) ──► REST + SSE API
       │
       ▼
UI Phase 1 (thư mục này)
```

**Điều kiện bắt đầu:**

1. Backend Phase 1 API chạy (`./scripts/dev-restart.sh` + `./scripts/dev-infra.sh`)
2. Đã đọc [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §1–§7, §17–§19
3. Đã đọc [`Backend/agent/phase-1/09-api-layer.md`](../../Backend/agent/phase-1/09-api-layer.md)

---

## Thứ tự implement đề xuất

| Bước | File plan | Ghi chú |
|------|-----------|---------|
| 0 | [00](./00-prerequisites-and-scope.md) | Đọc scope + mapping BE↔FE |
| 1 | [01](./01-foundation-and-routes.md) | Routes + folder `modules/task/` |
| 2 | [02](./02-api-client-and-types.md) | Types trước reducer |
| 3 | [03](./03-task-context-and-reducer.md) | State core |
| 4 | [04](./04-sse-task-connection.md) | Wire SSE vào reducer |
| 5 | [05](./05-sidebar-and-navigation.md) | Recents từ API |
| 6 | [06](./06-chat-input-and-controls.md) | Send / Stop |
| 7 | [07](./07-conversation-view.md) | Render messages |
| 8 | [08](./08-artifact-preview-panel.md) | Preview spec.md |
| 9 | [09](./09-ux-patterns-and-errors.md) | Polish UX |
| 10 | [10](./10-checklist.md) | E2E browser verify |

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) | Nguồn sự thật UI đầy đủ (MVP + Phase 2+) |
| [`Backend/agent/phase-1/`](../../Backend/agent/phase-1/) | API contracts, SSE schema |
| [`Backend/agent/phase-1/04-streaming-system.md`](../../Backend/agent/phase-1/04-streaming-system.md) | Event types authoritative |
| [`research/02-leadzen-agent-research.md`](../../../research/02-leadzen-agent-research.md) | Reference TaskContext pattern |
| [`Backend/auth/03-frontend.md`](../../Backend/auth/03-frontend.md) | Auth UI đã implement |
