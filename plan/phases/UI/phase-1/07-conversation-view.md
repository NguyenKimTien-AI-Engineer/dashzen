# 07 — Conversation View

> Render message list, agent blocks, tool chips, streaming text, errors.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §6 | **Phụ thuộc:** [03](./03-task-context-and-reducer.md)

**Location:** `apps/studio/modules/task/components/chat/`  
**Phụ thuộc:** TaskProvider, useStreamScroll

---

## 1. Mục tiêu

- [ ] 1. `ChatMessageList` — scrollable container
- [ ] 2. `ChatMessage` — user / assistant bubbles
- [ ] 3. `AgentActivityBlock` — collapsible sub-agent timeline
- [ ] 4. `ToolActivityChip` — main loop tool calls
- [ ] 5. `StreamErrorCard` — error + retry
- [ ] 6. Auto-scroll khi streaming (`useStreamScroll`)

---

## 2. ChatMessageList

### 2.1 Structure

```
<ScrollArea ref={listRef}>
  {messages.map(msg => <ChatMessage key={msg.id} />)}
  {agentBlocks.map(block => <AgentActivityBlock />)}
  {streamingAssistant && <ChatMessage streaming />}
  {streamError && <StreamErrorCard />}
  <div ref={bottomRef} />
</ScrollArea>
```

### 2.2 Ordering

Phase 1 flat chronological:

1. Historical messages từ DB (user, assistant)
2. Inline agent blocks **theo thứ tự SSE** (interleave với assistant stream)
3. Streaming buffer (main_text chưa flush)

**Đơn giản hóa Phase 1:** Agent blocks render **sau** user message hiện tại, trước assistant streaming bubble.

---

## 3. ChatMessage

### 3.1 User bubble

- Align right
- Background `bg-primary/10`
- Plain text — không markdown
- Optimistic: opacity pulse nhẹ cho đến STREAM_END

### 3.2 Assistant bubble

- Align left
- `react-markdown` + `remark-gfm`
- Streaming: cursor blink ở cuối text
- Links: `target="_blank" rel="noopener noreferrer"`

### 3.3 Thinking block (optional P1)

Nếu `thinkingText` không rỗng:

- Collapsible muted section trên assistant bubble
- Icon 🧠 + "Thinking..."
- `main_think` deltas append

---

## 4. ToolActivityChip

Main loop tools (`main_tool` / `main_result`):

```
┌ spawn_agent ───────────── ✓ ┐
│ dashboard-planner           │
└─────────────────────────────┘
```

| State | Icon |
|-------|------|
| running | spinner |
| success | checkmark green |
| error | x red |

Expand click → show `result` text (truncated 500 chars từ BE).

Tools Phase 1 thường gặp: `spawn_agent`, `read_file`, `write_file`, `list_file`.

---

## 5. AgentActivityBlock

Sub-agent UI — học LeadZen:

```
┌─ Dashboard Planner ──────────────────── ▼ ─┐
│  ✓ write_file spec.md                      │
│  Summary: Created spec with 4 widgets...   │
└────────────────────────────────────────────┘
```

### 5.1 Lifecycle

| Event | UI |
|-------|-----|
| `agent_start` | Open block, spinner, displayName |
| `agent_tool` | Timeline entry pending |
| `agent_result` | Entry checkmark + result preview |
| `agent_text` | Optional text area trong block |
| `agent_done` | Collapse default, show summary |

### 5.2 States

`running` | `done` | `error` | `collapsed`

Click header → toggle collapse.

### 5.3 Timeline entry

| Field | Display |
|-------|---------|
| tool name | `write_file`, `read_file` |
| args.path | monospace small |
| result | truncated, expandable |

---

## 6. StreamErrorCard

Khi `stream_error` hoặc connection fail:

- Red alert border
- Message user-friendly (không raw stack)
- **Retry** button → `TaskContext.retry()`
- **Dismiss** → clear error state

---

## 7. useStreamScroll

**File:** `modules/task/hooks/useStreamScroll.ts`

| Behavior | Rule |
|----------|------|
| Auto-scroll | Khi streaming + user near bottom (within 100px) |
| Pause auto-scroll | User scroll up |
| Resume | User scroll to bottom hoặc click scroll button |

Phase 1: **không** ScrollToBottom FAB — optional nếu có thời gian.

---

## 8. Loading states

| State | UI |
|-------|-----|
| Initial load messages | 2 skeleton bubbles |
| Empty task | "Gửi prompt đầu tiên để bắt đầu" |
| Streaming no text yet | Typing indicator (3 dots) |

---

## 9. Markdown security

- `react-markdown` default — không `dangerouslySetInnerHTML`
- Disable raw HTML (`skipHtml` or remark plugin)
- External links sanitized

---

## 10. Accessibility

- Message list `role="log"` `aria-live="polite"` cho streaming
- Agent block header là `<button>` với `aria-expanded`
- Tool chips có `aria-label` mô tả tool name + status

---

## 11. Checklist step 07

- [ ] User + assistant messages render correctly
- [ ] Streaming text updates realtime
- [ ] Agent block opens on agent_start, closes on agent_done
- [ ] Tool chips show spawn_agent + file tools
- [ ] stream_error shows retry card
- [ ] Auto-scroll works during stream
- [ ] Markdown renders headings, lists, code blocks
- [ ] Empty state on new task

---

## 12. Cross-references

| File | Liên quan |
|------|-----------|
| [08-artifact-preview-panel.md](./08-artifact-preview-panel.md) | file_artifact side effect |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §6 | Full message types (Phase 2+) |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §17 | SSE → UI mapping |
