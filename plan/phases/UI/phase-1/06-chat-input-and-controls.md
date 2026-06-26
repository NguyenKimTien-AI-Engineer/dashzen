# 06 — Chat Input & Controls

> Textarea, Send, Stop, Auto badge — input state machine.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §5 | **Phụ thuộc:** [03](./03-task-context-and-reducer.md), [04](./04-sse-task-connection.md)

**Location:** `apps/studio/modules/task/components/chat/ChatInput.tsx`  
**Phụ thuộc:** TaskProvider

---

## 1. Mục tiêu

- [ ] 1. `ChatInput` component — reusable trên `/app` và `/app/task/[id]`
- [ ] 2. State machine: `idle → sending → streaming → idle | error`
- [ ] 3. Send on Enter (Shift+Enter = newline)
- [ ] 4. Stop button khi streaming
- [ ] 5. Auto mode badge (read-only — không toggle Ask)

---

## 2. Layout

```
┌─────────────────────────────────────────────────────────┐
│  Mô tả dashboard bạn muốn tạo...                        │
│                                                         │
│  ⚡ Auto                              [Stop ◼] [↑ Send] │
└─────────────────────────────────────────────────────────┘
```

**Phase 1 không có:** 📎 attach, token estimate, drag-drop, Ask toggle.

---

## 3. Component props

| Prop | Type | Mô tả |
|------|------|-------|
| `onSend` | `(text: string) => void` | Parent handles create task or sendMessage |
| `onStop` | `() => void` | Optional — chỉ task page |
| `isStreaming` | boolean | Disable input, show Stop |
| `disabled` | boolean | External lock |
| `placeholder` | string | Context-specific |
| `autoFocus` | boolean | Task page default true |

---

## 4. Input state machine

| State | Send button | Stop button | Textarea |
|-------|-------------|-------------|----------|
| `idle` | Enabled if text.trim() | Hidden | Enabled |
| `sending` | Disabled + spinner | Hidden | Disabled |
| `streaming` | Hidden | Visible | Disabled |
| `error` | Enabled (retry) | Hidden | Enabled, giữ text |

Map từ `TaskContext.streamStatus`.

---

## 5. Keyboard behavior

| Key | Action |
|-----|--------|
| `Enter` | Send (preventDefault) |
| `Shift+Enter` | New line |
| `Escape` | Blur textarea (optional) |

---

## 6. Auto mode badge

- Static badge "Auto" với tooltip: "Agent chạy tự động không cần phê duyệt"
- **Không** toggle — Ask mode Phase 2
- Style: subtle badge `variant="secondary"`

---

## 7. Stop behavior

```
Click Stop
  → onStop() → TaskContext.stop()
  → POST /v1/tasks/{id}/stop
  → Abort SSE reader
  → streamStatus → idle
```

Show loading on Stop briefly nếu API chậm.

---

## 8. Home vs Task page

| Page | onSend behavior |
|------|-----------------|
| `/app` (ChatHome) | createTask → navigate với message |
| `/app/task/[id]` | TaskContext.sendMessage |

Cùng `ChatInput` component — khác callback.

---

## 9. Focus management

- Auto-focus on mount task page
- Sau `STREAM_END` → focus lại textarea
- Sau Send → clear input + focus

---

## 10. Quick action chips (ChatHome only)

| Chip | Prefill text |
|------|--------------|
| "Dashboard doanh thu" | "Tạo dashboard doanh thu theo khu vực với biểu đồ cột" |
| "Dashboard marketing" | "Tạo dashboard marketing với KPI và funnel chart" |

Click → set textarea value, **không** auto-send.

---

## 11. Checklist step 06

- [ ] Enter sends, Shift+Enter newline
- [ ] Send disabled when empty or streaming
- [ ] Stop visible only when streaming
- [ ] Stop calls API + aborts stream
- [ ] Auto badge displayed, not interactive
- [ ] Focus restored after stream end
- [ ] Works on Home (create flow) and Task page

---

## 12. Cross-references

| File | Liên quan |
|------|-----------|
| [07-conversation-view.md](./07-conversation-view.md) | Message list above input |
| [04-sse-task-connection.md](./04-sse-task-connection.md) | Stop + stream lifecycle |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §5 | Full input spec (Phase 2+) |
