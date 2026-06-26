# 02 — API Client & Types

> TypeScript API layer và SSE event types — mirror contract Backend Phase 1.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §3 | [`Backend/agent/phase-1/09-api-layer.md`](../../Backend/agent/phase-1/09-api-layer.md)

**Location:** `apps/studio/lib/api/tasks.ts`, `apps/studio/modules/task/types/`  
**Phụ thuộc:** [01-foundation-and-routes.md](./01-foundation-and-routes.md), `lib/api/client.ts`

---

## 1. Mục tiêu

- [ ] 1. `lib/api/tasks.ts` — CRUD + stream + stop
- [ ] 2. `stream-events.ts` — discriminated union mirror BE Pydantic
- [ ] 3. Response types cho Task, Message, File
- [ ] 4. Error mapping: 409, 401, 404
- [ ] 5. Không duplicate logic auth — dùng `fetchWithAuth`

---

## 2. REST API functions

**File:** `apps/studio/lib/api/tasks.ts`

### 2.1 Task CRUD

| Function | Method | Path | Return |
|----------|--------|------|--------|
| `createTask()` | POST | `/v1/tasks` | `Task` |
| `listTasks()` | GET | `/v1/tasks` | `Task[]` |
| `getTask(id)` | GET | `/v1/tasks/{id}` | `Task` |
| `updateTask(id, { title })` | PATCH | `/v1/tasks/{id}` | `Task` |
| `deleteTask(id)` | DELETE | `/v1/tasks/{id}` | `void` |

### 2.2 Messages & artifacts

| Function | Method | Path | Return |
|----------|--------|------|--------|
| `getMessages(taskId)` | GET | `/v1/tasks/{id}/messages` | `Message[]` |
| `getArtifacts(taskId)` | GET | `/v1/tasks/{id}/artifacts` | `FileArtifact[]` |

### 2.3 Stream & stop

| Function | Mô tả |
|----------|-------|
| `streamTask(taskId, body, signal)` | Trả `Response` với `body` ReadableStream — **không** parse ở đây |
| `stopTask(taskId)` | POST `/v1/tasks/{id}/stop` |

**Stream request body:**

```typescript
type StreamRequest = {
  message: string;
  parent_id?: string | null;
  mode: "auto";           // Phase 1: chỉ auto
  thinking_enabled?: boolean;
  user_instructions?: string;
};
```

### 2.4 LLM budget (optional)

| Function | Path | Ghi chú |
|----------|------|---------|
| `getLlmBudget()` | GET `/v1/llm/budget` | `fetchPublic` — chuẩn bị Phase 2 |

---

## 3. Domain types

**File:** `apps/studio/modules/task/types/api.ts` (hoặc inline trong tasks.ts)

### 3.1 Task

| Field | Type | Ghi chú |
|-------|------|---------|
| `id` | `string` (uuid) | |
| `title` | `string \| null` | Auto-set sau stream |
| `status` | `"active" \| "archived"` | |
| `type` | `string \| null` | |
| `created_at` | ISO string | |
| `updated_at` | ISO string | |

### 3.2 Message

| Field | Type | Ghi chú |
|-------|------|---------|
| `id` | string | |
| `role` | `"user" \| "assistant" \| "tool" \| "compact"` | |
| `content` | string | Assistant có thể embed tool_calls JSON |
| `parent_id` | string \| null | |
| `prompt_tokens` | number \| null | |
| `created_at` | ISO string | |

### 3.3 FileArtifact

| Field | Type |
|-------|------|
| `id` | string |
| `name` | string |
| `source` | `"workspace" \| "upload"` |
| `kind` | `"text" \| "image" \| "binary"` |
| `content` | string \| null |
| `size` | number |
| `created_at` | ISO string |

---

## 4. SSE event types

**File:** `apps/studio/modules/task/types/stream-events.ts`

Mirror **chính xác** field names từ `packages/agents/src/agents/streaming/events.py` (camelCase nếu BE dùng snake_case — align với JSON thực tế).

### 4.1 Discriminated union

Mỗi event có `type` literal. Ví dụ shape:

| type | Fields chính |
|------|--------------|
| `main_text` | `delta: string` |
| `main_think` | `delta: string` |
| `main_tool` | `call_id`, `name`, `args` |
| `main_result` | `call_id`, `status`, `result` |
| `agent_start` | `call_id`, `name`, `display_name` |
| `agent_text` | `call_id`, `delta` |
| `agent_think` | `call_id`, `delta` |
| `agent_tool` | `call_id`, `tool_call_id`, `name`, `args` |
| `agent_result` | `call_id`, `tool_call_id`, `status`, `result` |
| `agent_done` | `call_id`, `status`, `summary` |
| `file_artifact` | `name`, `content`, `kind` |
| `task_meta` | `title?`, `task_type?` |
| `heartbeat` | (empty) |
| `stream_done` | `partial_message_id?` |
| `stream_error` | `message` |

### 4.2 Parser helper

`parseStreamEvent(json: string): StreamEvent | null`

- `JSON.parse` + validate `type` field
- Unknown type → log warning, return null (không crash stream)

---

## 5. TanStack Query keys

Định nghĩa consistent query keys:

| Key | Dùng cho |
|-----|----------|
| `["tasks"]` | List tasks |
| `["tasks", taskId]` | Task detail |
| `["tasks", taskId, "messages"]` | Messages |
| `["tasks", taskId, "artifacts"]` | Artifacts |

Invalidate sau `STREAM_END`:

- `messages` + `artifacts` + `tasks` (title có thể đổi)

---

## 6. Error handling

| HTTP | UI behavior |
|------|-------------|
| 401 | `fetchWithAuth` refresh → redirect login |
| 404 | Toast "Task not found" + navigate `/app` |
| 409 | Stream đang chạy — toast "Agent đang xử lý..." (xem step 04) |
| 429 | `RateLimitError` — toast cooldown (basic) |

Tạo `StreamConflictError` hoặc check `ApiError.status === 409` trong TaskConnection.

---

## 7. Checklist step 02

- [ ] `createTask()` + `listTasks()` gọi API thành công (manual hoặc test)
- [ ] Types compile — không `any` cho StreamEvent
- [ ] `parseStreamEvent` handle tất cả Phase 1 event types
- [ ] Query keys documented trong file hoặc `query-keys.ts`

---

## 8. Cross-references

| File | Liên quan |
|------|-----------|
| [03-task-context-and-reducer.md](./03-task-context-and-reducer.md) | Reducer consume events |
| [04-sse-task-connection.md](./04-sse-task-connection.md) | streamTask() caller |
| [`Backend/agent/phase-1/04-streaming-system.md`](../../Backend/agent/phase-1/04-streaming-system.md) | BE schema source |
