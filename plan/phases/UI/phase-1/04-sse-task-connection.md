# 04 — SSE TaskConnection

> React component đọc SSE stream — keyed remount, parse events, dispatch reducer.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §7, §7.4 | [`Backend/agent/phase-1/09-api-layer.md`](../../Backend/agent/phase-1/09-api-layer.md) §3

**Location:** `apps/studio/modules/task/contexts/task-connection.tsx`  
**Phụ thuộc:** [03-task-context-and-reducer.md](./03-task-context-and-reducer.md), [02-api-client-and-types.md](./02-api-client-and-types.md)

---

## 1. Mục tiêu

- [ ] 1. `TaskConnection` component — POST stream + read SSE
- [ ] 2. Keyed remount pattern (`key={streamKey}`)
- [ ] 3. Parse `data: {...}\n\n` lines → dispatch reducer
- [ ] 4. Handle 409, network error, abort
- [ ] 5. Cleanup AbortController on unmount

---

## 2. Component contract

```typescript
type TaskConnectionProps = {
  taskId: string;
  body: StreamRequest;
  onEvent: (event: StreamEvent) => void;
  onEnd: () => void;
  onError: (error: StreamConnectionError) => void;
};
```

**Render:** `null` — side-effect only component.

**Mount trong TaskProvider:**

```tsx
{streamBody && (
  <TaskConnection
    key={streamKey}
    taskId={taskId}
    body={streamBody}
    onEvent={(e) => dispatch(mapEventToAction(e))}
    onEnd={handleStreamEnd}
    onError={handleStreamError}
  />
)}
```

---

## 3. SSE read loop

### 3.1 Fetch

- `POST /v1/tasks/{taskId}/stream`
- Headers: `Content-Type: application/json`, `credentials: include`
- Body: JSON `StreamRequest`
- `signal`: AbortController

### 3.2 Pre-response errors

| Status | Behavior |
|--------|----------|
| 401 | Session expired — `fetchWithAuth` handles |
| 409 | `onError({ kind: "still_processing" })` — toast, không retry auto Phase 1 |
| 404 | `onError({ kind: "not_found" })` |
| 5xx | `onError({ kind: "server_error" })` |

### 3.3 Read stream

1. `response.body.getReader()` + `TextDecoder`
2. Buffer incomplete lines
3. Split by `\n\n`
4. Lines starting `data:` → parse JSON → `onEvent`
5. `heartbeat` → ignore (keep connection alive)
6. `stream_done` → `onEnd()` + close reader
7. `stream_error` → dispatch + `onEnd()`

### 3.4 Disconnect behavior

Theo BE Phase 1: **client disconnect không cancel LLM**. UI khi user navigate away:

- AbortController abort fetch → UI stops reading
- User quay lại → `GET /messages` restore (useTaskMessages)

Phase 1: **không** ReconnectBanner — chỉ refetch on mount.

---

## 4. Event → action mapper

**File:** `modules/task/lib/map-stream-event.ts`

| StreamEvent.type | Reducer action |
|------------------|----------------|
| `main_text` | STREAM_DELTA |
| `main_think` | STREAM_THINKING_DELTA |
| `main_tool` | TOOL_START |
| `main_result` | TOOL_RESULT |
| `agent_start` | AGENT_START |
| `agent_text`, `agent_think`, `agent_tool`, `agent_result` | AGENT_EVENT |
| `agent_done` | AGENT_DONE |
| `file_artifact` | STREAM_ARTIFACT |
| `task_meta` | SET_TASK_META |
| `stream_done` | STREAM_END |
| `stream_error` | STREAM_ERROR |
| `heartbeat` | (skip) |

---

## 5. Stop integration

### 5.1 User clicks Stop

```
1. POST /v1/tasks/{id}/stop (fire-and-forget ok)
2. abortController.abort() — stop reading SSE
3. dispatch partial STREAM_END nếu có streamingText
4. refetch messages
```

### 5.2 Race: send while streaming

- `sendMessage` guard: reject nếu `isStreaming`
- Optional: await stop trước send mới (Phase 2 `stopInFlightRef`)

---

## 6. 409 handling (Phase 1 basic)

Khi nhận 409:

1. Toast: "Agent đang xử lý yêu cầu trước — vui lòng đợi"
2. `streamStatus = "idle"`
3. **Không** auto-retry 105s (defer Phase 2)

User có thể refresh page → messages đã persist nếu stream background vẫn chạy.

---

## 7. Security

- Không log full SSE content ra console production
- Cookie auth only — không expose token trong EventSource URL

---

## 8. Testing approach

Unit test `parseSSEChunk(buffer)` với fixture:

```
data: {"type":"main_text","delta":"Hello"}\n\n
data: {"type":"stream_done"}\n\n
```

Integration: MSW mock ReadableStream (Phase 2 test suite).

---

## 9. Checklist step 04

- [ ] TaskConnection mounts only when streamBody set
- [ ] streamKey change → previous connection aborted
- [ ] All Phase 1 events dispatch correctly
- [ ] 409 shows toast, không crash
- [ ] stream_done triggers onEnd + refetch
- [ ] heartbeat không spam reducer

---

## 10. Cross-references

| File | Liên quan |
|------|-----------|
| [06-chat-input-and-controls.md](./06-chat-input-and-controls.md) | Stop button |
| [`Backend/agent/phase-1/04-streaming-system.md`](../../Backend/agent/phase-1/04-streaming-system.md) | SSE format |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §7.3–7.4 | Full resilience (Phase 2) |
