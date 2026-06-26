# 01 — Foundation & Routes

> Thiết lập routes, layout task workspace, và scaffold module `modules/task/`.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §2.2, §3.2 | **Phụ thuộc:** [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md)

**Location:** `apps/studio/app/`, `apps/studio/modules/task/`  
**Phụ thuộc:** Auth UI done

---

## 1. Mục tiêu

- [ ] 1. Route `/app/task/[taskId]` — trang conversation chính
- [ ] 2. Cập nhật `/app` — ChatHome thay placeholder
- [ ] 3. Scaffold folder `modules/task/` (contexts, hooks, components, types)
- [ ] 4. Wrap task page trong `TaskProvider`
- [ ] 5. Deprecate hoặc redirect `/app/chats` → `/app`

---

## 2. Routes

### 2.1 Bảng routes Phase 1

| Route | Auth | Mô tả |
|-------|------|-------|
| `/app` | Protected | Home — empty chat + onboarding prompts |
| `/app/task/[taskId]` | Protected | Task conversation + preview panel |
| `/app/settings` | Protected | Giữ nguyên |
| `/app/profile` | Protected | Giữ nguyên |
| `/app/chats` | Protected | Redirect → `/app` (legacy placeholder) |

**Không tạo Phase 1:** `/app/dashboard/[pageId]` — defer đến khi có widget renderer.

### 2.2 `/app/task/[taskId]/page.tsx`

Trách nhiệm trang:

1. Đọc `taskId` từ `params`
2. Mount `TaskProvider` với `taskId`
3. Layout split: `ChatWorkspace` (trái) + `SpecPreviewPanel` (phải, collapsible)
4. Fetch task detail — 404 nếu không tồn tại → toast + redirect `/app`

### 2.3 `/app/page.tsx`

Thay nội dung placeholder bằng `ChatHome`:

- Headline chào user (dùng `useMe`)
- 2–3 onboarding prompt chips (prefill, không auto-send)
- Input tương tự task view — **Send tạo task mới** rồi navigate

Flow **Home send:**

```
1. User gõ prompt trên /app
2. POST /v1/tasks
3. navigate(`/app/task/${id}?initialMessage=...`) hoặc lưu prompt trong TaskContext
4. Task page auto-send message đầu tiên
```

---

## 3. Layout integration

### 3.1 App layout hiện tại

`app/app/layout.tsx` đã có `AuthGuard` + `AppShell`. **Không thay đổi** cấu trúc top-level.

### 3.2 Task page layout

```
<AppShell>  {/* sidebar đã có */}
  <div className="flex h-full flex-1 overflow-hidden">
    <div className="flex min-w-0 flex-1 flex-col">
      <TaskHeader />        {/* title, optional status */}
      <ChatMessageList />
      <ChatInput />
    </div>
    <SpecPreviewPanel />    {/* optional collapse */}
  </div>
</AppShell>
```

### 3.3 TaskHeader

- Hiển thị `task.title` hoặc "Untitled dashboard"
- Cập nhật realtime khi nhận `task_meta` SSE
- Không cần breadcrumb phức tạp Phase 1

---

## 4. Module scaffold

Tạo các file stub (export empty hoặc placeholder) để các step sau fill dần:

| File | Vai trò |
|------|---------|
| `modules/task/contexts/task-context.tsx` | Provider + `sendMessage`, `stop` |
| `modules/task/contexts/task-reducer.ts` | Pure reducer |
| `modules/task/contexts/task-connection.tsx` | SSE client component |
| `modules/task/hooks/useTask.ts` | Context consumer |
| `modules/task/hooks/useTaskMessages.ts` | TanStack Query |
| `modules/task/hooks/useStreamScroll.ts` | Auto-scroll |
| `modules/task/types/stream-events.ts` | TS types mirror BE |
| `modules/task/types/task-state.ts` | Reducer state shape |

---

## 5. Dependencies npm

Thêm nếu chưa có (kiểm tra `package.json`):

| Package | Mục đích |
|---------|----------|
| `react-markdown` | Render assistant markdown |
| `remark-gfm` | Tables, strikethrough |
| `@tanstack/react-query` | Đã có — tasks/messages queries |

**Defer Phase 2:** `shiki` syntax highlight — dùng fenced code basic trước.

---

## 6. Middleware

`middleware.ts` hiện tại protect `/app/*`. **Không cần sửa** — `/app/task/[taskId]` đã nằm dưới `/app`.

---

## 7. Checklist step 01

- [ ] Route `/app/task/[taskId]` render không lỗi
- [ ] `/app` hiển thị ChatHome thay placeholder
- [ ] `/app/chats` redirect hoặc remove khỏi sidebar nav
- [ ] Folder `modules/task/` tồn tại với exports
- [ ] `TaskProvider` wrap task page
- [ ] Navigate New Dashboard → task page works (sau step 05)

---

## 8. Cross-references

| File | Liên quan |
|------|-----------|
| [02-api-client-and-types.md](./02-api-client-and-types.md) | API calls từ pages |
| [05-sidebar-and-navigation.md](./05-sidebar-and-navigation.md) | Sidebar New Dashboard |
| [`Backend/auth/03-frontend.md`](../../Backend/auth/03-frontend.md) | AuthGuard pattern |
