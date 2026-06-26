# 05 — Sidebar & Navigation

> Wire sidebar với Task API — New Dashboard, recents, task title updates.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §4 | **Phụ thuộc:** [02-api-client-and-types.md](./02-api-client-and-types.md)

**Location:** `apps/studio/modules/layout/components/`  
**Phụ thuộc:** Auth done, tasks API client

---

## 1. Mục tiêu

- [ ] 1. **New Dashboard** → `createTask()` → navigate `/app/task/{id}`
- [ ] 2. **Recents** — `listTasks()` từ TanStack Query
- [ ] 3. Highlight active task trong sidebar
- [ ] 4. Cập nhật title khi `task_meta` SSE (invalidate query)
- [ ] 5. Empty state + skeleton loading

---

## 2. Sidebar items Phase 1

| Item | Hành vi |
|------|---------|
| **New Dashboard** | POST task → navigate task page |
| **Search** | Filter local recents (debounce 300ms) — **không** server search |
| **Recents list** | GET /v1/tasks, sort `created_at` desc |
| **Settings** | Giữ `/app/settings` |

**Remove / hide Phase 1:**

- `/app/projects` — out of scope hoặc hide nav item
- `/app/chats` placeholder — redirect `/app`
- `/app/artifacts` global — defer (artifacts per-task trong preview)

---

## 3. Recent item UI

### 3.1 Display

| Element | Nguồn |
|---------|-------|
| Title | `task.title` hoặc "Untitled dashboard" |
| Relative time | `formatDistanceToNow(task.updated_at)` |
| Active indicator | `pathname === /app/task/{id}` |

### 3.2 Status icon (derived)

BE Phase 1 không có `streaming` status field — derive từ UI:

| State | Icon | Điều kiện |
|-------|------|-----------|
| `idle` | dot gray | default |
| `streaming` | spinner | TaskContext global hoặc taskId match |
| `ready` | check | có artifact `spec.md` (optional query) |
| `error` | alert | last stream error on this task |

Phase 1 đơn giản: chỉ **active highlight** + title — status icons optional P1.

### 3.3 Context menu (minimal)

| Action | API |
|--------|-----|
| Rename | PATCH title — inline dialog |
| Delete | DELETE task — confirm dialog |

Duplicate → Phase 2.

---

## 4. New Dashboard flow

```
Click "New Dashboard"
  → createTask() mutation
  → onSuccess: router.push(`/app/task/${id}`)
  → Task page: empty messages, focus input
```

Loading state trên button khi mutation pending.

---

## 5. task_meta sync

Khi TaskConnection nhận `task_meta`:

1. Reducer `SET_TASK_META`
2. `queryClient.setQueryData(["tasks", taskId], merge title)`
3. `queryClient.invalidateQueries(["tasks"])` — update recents list

Sidebar subscribe `useQuery(["tasks"])` — auto re-render.

---

## 6. Empty & loading states

| State | UI |
|-------|-----|
| Loading | 3–5 skeleton lines (`SidebarRecentsSkeleton`) |
| Empty | "Chưa có dashboard nào" + CTA New Dashboard |
| Error | "Không tải được danh sách" + Retry button |

---

## 7. Mobile sidebar

Dùng `sidebarStore` hiện có:

- Collapsed → icon only
- Recents: tooltip title on hover
- New Dashboard: icon `+` khi collapsed

---

## 8. Navigation guards

- Delete task đang xem → redirect `/app`
- Task 404 on load → toast + redirect `/app`

---

## 9. Checklist step 05

- [ ] New Dashboard tạo task và navigate
- [ ] Recents hiển thị tasks từ API
- [ ] Click recent → `/app/task/{id}`
- [ ] Active task highlighted
- [ ] Title updates sau stream (task_meta)
- [ ] Delete removes from list
- [ ] Empty state khi chưa có task

---

## 10. Cross-references

| File | Liên quan |
|------|-----------|
| [01-foundation-and-routes.md](./01-foundation-and-routes.md) | Routes |
| [03-task-context-and-reducer.md](./03-task-context-and-reducer.md) | SET_TASK_META |
| `modules/layout/components/AppSidebar.tsx` | File sửa |
