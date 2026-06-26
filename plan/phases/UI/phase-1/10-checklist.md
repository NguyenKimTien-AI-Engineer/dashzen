# 10 — Checklist & Definition of Done

> Checklist cuối UI Phase 1 — phải PASS trước khi bắt đầu UI Phase 2.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §19 MVP (subset) | [`Backend/agent/phase-1/10-checklist.md`](../../Backend/agent/phase-1/10-checklist.md)

---

## 1. Definition of Done (12 items)

- [ ] **1.** User đăng nhập → `/app` hiển thị ChatHome (không còn placeholder "next phase")
- [ ] **2.** Click **New Dashboard** → tạo task → navigate `/app/task/{id}` trong < 2s
- [ ] **3.** Sidebar **Recents** hiển thị danh sách tasks từ `GET /v1/tasks`
- [ ] **4.** Gửi prompt *"tạo dashboard doanh thu"* → thấy **streaming assistant text** (`main_text`)
- [ ] **5.** Thấy **Agent Activity Block** (`dashboard-planner`) với timeline tool calls
- [ ] **6.** Thấy **tool chips** cho `spawn_agent` / `write_file` trên main loop
- [ ] **7.** Panel preview hiển thị **`spec.md`** sau `file_artifact` (markdown rendered)
- [ ] **8.** Sau `stream_done` → messages persist — refresh page vẫn thấy hội thoại
- [ ] **9.** **Stop** button dừng stream đang chạy — UI về idle
- [ ] **10.** Gửi stream khi đang streaming → toast 409 (không crash)
- [ ] **11.** `task_meta` cập nhật title trên sidebar sau vài turn
- [ ] **12.** Stream error → error card + nút Retry hoạt động

---

## 2. Per-step verification map

| DoD # | Step plan | Component |
|-------|-----------|-----------|
| 1 | [01](./01-foundation-and-routes.md) | ChatHome |
| 2 | [05](./05-sidebar-and-navigation.md) | New Dashboard |
| 3 | [05](./05-sidebar-and-navigation.md) | SidebarRecents |
| 4 | [04](./04-sse-task-connection.md) + [07](./07-conversation-view.md) | SSE + messages |
| 5 | [07](./07-conversation-view.md) | AgentActivityBlock |
| 6 | [07](./07-conversation-view.md) | ToolActivityChip |
| 7 | [08](./08-artifact-preview-panel.md) | SpecPreviewPanel |
| 8 | [03](./03-task-context-and-reducer.md) + [02](./02-api-client-and-types.md) | Refetch bridge |
| 9 | [06](./06-chat-input-and-controls.md) + [04](./04-sse-task-connection.md) | Stop |
| 10 | [04](./04-sse-task-connection.md) + [09](./09-ux-patterns-and-errors.md) | 409 toast |
| 11 | [05](./05-sidebar-and-navigation.md) | task_meta |
| 12 | [07](./07-conversation-view.md) + [09](./09-ux-patterns-and-errors.md) | StreamErrorCard |

---

## 3. E2E test script (manual browser)

### 3.1 Prerequisites

```bash
./scripts/dev-infra.sh          # postgres + migrate
./scripts/dev-restart.sh        # API + Studio
# .env: LLM_PROVIDER với provider hoạt động (gemini/ollama)
```

### 3.2 Happy path

1. Mở `http://localhost:3000` → login
2. `/app` → gõ "Tạo dashboard doanh thu theo khu vực"
3. Send → redirect hoặc đã ở task page
4. Quan sát:
   - User bubble xuất hiện ngay (optimistic)
   - Assistant text stream dần
   - Agent block "Dashboard Planner" mở
   - Tool entries: write_file spec.md
   - Preview panel hiện spec markdown
5. Stream kết thúc → input enabled lại
6. Refresh page → messages + spec vẫn còn
7. Sidebar hiện task với title (có thể "Untitled" turn 1)

### 3.3 Stop test

1. Gửi prompt dài (trigger multi-step agent)
2. Click **Stop** giữa stream
3. UI idle — có thể gửi message mới

### 3.4 409 test

1. Mở 2 tabs cùng task
2. Tab 1: send (streaming)
3. Tab 2: send ngay → toast 409

### 3.5 Delete test

1. Sidebar → delete task
2. Redirect `/app` — task biến khỏi recents

---

## 4. Automated tests (recommended)

| Layer | Tool | Coverage |
|-------|------|----------|
| Reducer | Vitest | map SSE events → state |
| parseStreamEvent | Vitest | all Phase 1 types |
| ChatMessage | RTL | render markdown |
| API client | MSW | CRUD mock |
| E2E | Playwright (optional) | Happy path 3.2 |

Phase 1 minimum: **reducer unit tests** + **manual E2E**.

---

## 5. Out of scope verification

Các mục sau **không** yêu cầu PASS UI Phase 1:

- Ask mode / ActionCard approve-reject
- Context donut / Compact button
- Regenerate / branch navigation
- File attach upload
- Full dashboard widget render
- ReconnectBanner auto-retry
- Virtualized message list
- Rate limit countdown UI

---

## 6. Alignment với Backend Phase 1 DoD

| BE DoD | UI verification |
|--------|-----------------|
| BE #4 main_text SSE | UI #4 streaming text |
| BE #5 spawn planner | UI #5 agent block |
| BE #6 file_artifact | UI #7 preview spec.md |
| BE #7 messages persist | UI #8 refresh |
| BE #9 stop | UI #9 stop button |
| BE #10 409 | UI #10 toast |
| BE #13 auto title | UI #11 sidebar title |

---

## 7. Sign-off criteria

UI Phase 1 coi là **complete** khi:

1. Tất cả 12 DoD items PASS (manual hoặc auto)
2. Không regression auth flows hiện có
3. `npm run build` Studio pass
4. Không lỗi TypeScript strict
5. Environments: Chrome + Firefox latest; mobile layout không broken

---

## 8. Cross-references

| File | Liên quan |
|------|-----------|
| [README.md](./README.md) | Overview |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §19 | Full MVP scope |
| [`Backend/agent/phase-1/10-checklist.md`](../../Backend/agent/phase-1/10-checklist.md) | BE DoD |
| [`UI/phase-2/`](../phase-2/) | Next phase (tạo sau) |
