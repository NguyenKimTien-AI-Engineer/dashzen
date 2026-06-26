# 09 — UX Patterns & Errors

> Toast, skeleton, error boundaries, API errors, scroll polish.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §9, §15, §3.4 | **Phụ thuộc:** các steps 01–08

**Location:** `apps/studio/components/`, `apps/studio/modules/task/`  
**Phụ thuộc:** `sonner` toast, existing `lib/api/errors.ts`

---

## 1. Mục tiêu

- [ ] 1. Toast notifications — success + error centralized
- [ ] 2. Skeleton loaders — sidebar, messages
- [ ] 3. `TaskErrorBoundary` — isolate task page crashes
- [ ] 4. 401 / 409 / 429 user-facing messages
- [ ] 5. Empty states — home, sidebar, preview

---

## 2. Toast system

Dùng `sonner` đã có (`components/ui/sonner.tsx`).

### 2.1 Toast triggers Phase 1

| Event | Toast |
|-------|-------|
| Task created | (silent — navigate đủ) |
| Task deleted | "Đã xóa dashboard" |
| Rename success | "Đã đổi tên" |
| Stream error | "Có lỗi xảy ra — thử lại" |
| 409 conflict | "Agent đang xử lý — vui lòng đợi" |
| 429 rate limit | "Quá nhiều yêu cầu — thử lại sau {n}s" |
| Session expired | "Phiên đăng nhập hết hạn" |
| Spec ready | "Spec đã sẵn sàng" (optional) |
| Copy spec | "Đã copy" |

### 2.2 Wrapper helper

`lib/toast.ts` hoặc hooks:

```typescript
toast.error(message)
toast.success(message)
```

Không toast cho mỗi SSE event — chỉ user-facing milestones.

---

## 3. Skeleton loaders

| Component | Skeleton |
|-----------|----------|
| `SidebarRecents` | 4 lines title + meta |
| `ChatMessageList` | 2 bubbles alternating |
| `SpecPreviewPanel` | 8 lines text |
| `TaskHeader` | 1 title bar |

Dùng `components/ui/skeleton.tsx` — không full-page spinner.

---

## 4. Error boundaries

### 4.1 Hierarchy Phase 1

```
<AuthGuard>
  <AppShell>
    <TaskErrorBoundary>     ← new: wrap task page content
      <ChatMessageList />
      <ChatInput />
      <SpecPreviewPanel />
    </TaskErrorBoundary>
  </AppShell>
</AuthGuard>
```

### 4.2 TaskErrorBoundary fallback

- Friendly message: "Không thể tải cuộc hội thoại"
- Buttons: **Thử lại** (reset boundary + refetch), **Về trang chủ**
- Log error to console dev only

Sidebar **không** nằm trong TaskErrorBoundary — sidebar vẫn dùng được.

---

## 5. API error mapping

Extend `lib/api/errors.ts` usage:

| Error class | UI action |
|-------------|-----------|
| `SessionExpiredError` | Redirect login (đã có) |
| `RateLimitError` | Toast + disable send tạm |
| `ApiError 404` | Toast + redirect |
| `ApiError 409` | Toast (stream conflict) |
| Network offline | Toast "Mất kết nối mạng" |

---

## 6. Empty states

| Location | Copy |
|----------|------|
| ChatHome | "Mô tả dashboard bạn muốn tạo — AI sẽ lập kế hoạch và viết spec" |
| Sidebar recents | "Chưa có dashboard — bắt đầu với New Dashboard" |
| New task messages | "Gửi prompt đầu tiên để bắt đầu" |
| Preview panel | "File spec.md sẽ hiện ở đây" |

Optional illustration — brand icon đơn giản.

---

## 7. JWT mid-session

Đã có `useSessionKeepAlive` + `fetchWithAuth` refresh.

**SSE 401:** TaskConnection catch → stop stream → toast session expired → redirect.

---

## 8. Performance notes Phase 1

- **Không** virtualize message list — chấp nhận < 100 messages
- Debounce sidebar search 300ms
- `React.memo` cho `ChatMessage` nếu re-render nhiều

Defer virtualization → UI Phase 2.

---

## 9. Theme

Dùng theme system hiện có — chat bubbles compatible dark mode:

- User bubble: `bg-primary/10` light, adjust dark
- Assistant: `bg-muted`
- Agent block: `border rounded-lg`

---

## 10. Checklist step 09

- [ ] Toasts fire for errors user cares about
- [ ] Skeletons show during initial fetch
- [ ] TaskErrorBoundary catches render errors
- [ ] 409/401/429 có message tiếng Việt rõ ràng
- [ ] Empty states trên home, sidebar, preview
- [ ] Dark mode readable

---

## 11. Cross-references

| File | Liên quan |
|------|-----------|
| [10-checklist.md](./10-checklist.md) | E2E verify |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §9, §15 | Full UX spec |
| `lib/api/client.ts` | Error interceptor |
