# 03 — TaskContext & Reducer

> State management lõi cho chat streaming — `useReducer` + TaskProvider.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §3.1, §7.2, §18 | Học LeadZen `modules/task/`

**Location:** `apps/studio/modules/task/contexts/`  
**Phụ thuộc:** [02-api-client-and-types.md](./02-api-client-and-types.md)

---

## 1. Mục tiêu

- [ ] 1. `task-reducer.ts` — pure reducer, subset actions Phase 1
- [ ] 2. `task-context.tsx` — Provider expose `sendMessage`, `stop`, selectors
- [ ] 3. `task-state.ts` — state shape authoritative
- [ ] 4. Bridge `STREAM_END` → refetch messages (TanStack Query)
- [ ] 5. Optimistic user message on send

---

## 2. State shape

**File:** `modules/task/types/task-state.ts`

### 2.1 Top-level TaskState

| Field | Type | Mô tả |
|-------|------|-------|
| `taskId` | string | Current task |
| `streamStatus` | `"idle" \| "sending" \| "streaming" \| "error"` | Input state machine |
| `streamKey` | number | Increment mỗi send → remount TaskConnection |
| `messages` | `DisplayMessage[]` | Merged DB + streaming |
| `streamingText` | string | Accumulated main_text chưa flush |
| `thinkingText` | string | Accumulated main_think |
| `toolCalls` | `Map<callId, ToolCallState>` | Main loop tools |
| `agentBlocks` | `Map<callId, AgentBlockState>` | Sub-agent blocks |
| `artifacts` | `Map<string, FileArtifactState>` | name → content |
| `taskMeta` | `{ title?: string; type?: string }` | From task_meta SSE |
| `error` | `StreamErrorState \| null` | Last stream error |

### 2.2 DisplayMessage (UI model)

Tách khỏi API Message — cho phép optimistic + streaming:

| Field | Mô tả |
|-------|-------|
| `id` | uuid hoặc `optimistic-*` |
| `role` | user / assistant |
| `content` | markdown text |
| `status` | `sent` \| `streaming` \| `error` |
| `createdAt` | Date |

### 2.3 AgentBlockState

| Field | Mô tả |
|-------|-------|
| `callId` | string |
| `name` | agent name |
| `displayName` | human label |
| `status` | `running` \| `done` \| `error` |
| `summary` | from agent_done |
| `timeline` | `AgentTimelineEntry[]` |
| `textBuffer` | streamed agent_text |

---

## 3. Reducer actions (Phase 1 subset)

Chỉ implement actions cần cho BE Phase 1 — **không** `TOOL_PENDING`, `ASK_PENDING`, `SET_TIP`:

| Action | Trigger | Effect |
|--------|---------|--------|
| `STREAM_START` | sendMessage | streamStatus=streaming, optimistic user msg, streamKey++ |
| `STREAM_DELTA` | main_text | Append streamingText |
| `STREAM_THINKING_DELTA` | main_think | Append thinkingText |
| `TOOL_START` | main_tool | Add tool chip running |
| `TOOL_RESULT` | main_result | Update tool chip done |
| `AGENT_START` | agent_start | Open agent block |
| `AGENT_EVENT` | agent_* | Update block timeline/text |
| `AGENT_DONE` | agent_done | Close block + summary |
| `STREAM_ARTIFACT` | file_artifact | Update artifacts map |
| `SET_TASK_META` | task_meta | Update taskMeta |
| `STREAM_END` | stream_done | streamStatus=idle, flush streaming → message |
| `STREAM_ERROR` | stream_error | streamStatus=error, set error |
| `SET_MESSAGES` | refetch done | Replace với DB messages |
| `SET_ARTIFACTS` | refetch done | Merge artifacts từ API |
| `RESET` | unmount / navigate | Clear state |

### 3.1 STREAM_END bridge

Khi `stream_done`:

1. Nếu `streamingText` không rỗng → tạo assistant `DisplayMessage` final
2. Clear `streamingText`, `thinkingText`
3. `streamStatus = "idle"`
4. Callback `onStreamEnd()` → invalidate queries

---

## 4. TaskProvider API

**File:** `modules/task/contexts/task-context.tsx`

### 4.1 Context value

| Method / field | Mô tả |
|----------------|-------|
| `sendMessage(text: string)` | Dispatch STREAM_START + mount TaskConnection |
| `stop()` | POST stop + local streamStatus update |
| `state` | Full TaskState |
| `isStreaming` | derived from streamStatus |
| `retry()` | Re-send last failed message |

### 4.2 sendMessage flow

```
1. Guard: không send nếu isStreaming hoặc text empty
2. dispatch(STREAM_START, { content: text })
3. Set streamBody = { message, mode: "auto", parent_id: lastMessageId }
4. streamKey++ → TaskConnection remounts
```

### 4.3 Initial message (from Home)

Task page nhận `initialMessage` (searchParams hoặc sessionStorage):

- On mount: nếu có initialMessage và messages empty → auto `sendMessage`

---

## 5. useTask hook

**File:** `modules/task/hooks/useTask.ts`

Thin wrapper:

- `sendMessage`, `stop`, `retry`
- `isStreaming`, `streamError`
- `messages`, `agentBlocks`, `artifacts`

Throw nếu dùng ngoài TaskProvider.

---

## 6. useTaskMessages hook

**File:** `modules/task/hooks/useTaskMessages.ts`

- `useQuery` → `getMessages(taskId)`
- On success → `dispatch(SET_MESSAGES, normalized)`
- `normalizeMessages(apiMessages): DisplayMessage[]` — parse assistant content có tool_calls JSON

Phase 1: **flat list** — không branch navigation.

---

## 7. Normalization rules

Khi load từ DB sau stream:

| API role | UI render |
|----------|-----------|
| `user` | User bubble |
| `assistant` | Assistant bubble — strip embedded tool_calls JSON nếu có |
| `tool` | **Không** render riêng — đã có trong tool chips từ stream; optional skip |

Agent activities: Phase 1 BE lưu `AgentRun` — optional hiển thị từ messages reload (basic). Full reload timeline từ `AgentRun` API → **UI Phase 2** nếu BE chưa expose endpoint.

---

## 8. Checklist step 03

- [ ] Reducer pure — unit test với fixture events
- [ ] STREAM_DELTA append đúng
- [ ] AGENT_START → AGENT_DONE lifecycle
- [ ] STREAM_END flush text + trigger refetch callback
- [ ] TaskProvider throw outside tree
- [ ] Không dùng Zustand cho streaming state

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [04-sse-task-connection.md](./04-sse-task-connection.md) | dispatch từ SSE |
| [07-conversation-view.md](./07-conversation-view.md) | Render state |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §7.2 | Full action list (Phase 2+) |
