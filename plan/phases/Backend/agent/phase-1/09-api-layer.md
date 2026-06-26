# 09 — API Layer (Phase 1)

> FastAPI routes — REST tasks + SSE stream/stop + auth integration + LLM budget.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.9 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §15

**Location:** `apps/api/src/api/routes/`  
**Phụ thuộc:** Tất cả steps 01–08

---

## 1. Mục tiêu

- [ ] 1. Task CRUD REST endpoints
- [ ] 2. `POST /stream` SSE endpoint — core deliverable
- [ ] 3. `POST /stop` abort handshake
- [ ] 4. Auth integration (`get_current_user`)
- [ ] 5. `GET /llm/budget`

---

## 2. Task CRUD

**File:** `apps/api/src/api/routes/tasks.py`

### 2.1 Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/v1/tasks` | Tạo task + seed memory.md |
| `GET` | `/v1/tasks` | List tasks của current user |
| `GET` | `/v1/tasks/{id}` | Task detail |
| `PATCH` | `/v1/tasks/{id}` | Rename (title) |
| `DELETE` | `/v1/tasks/{id}` | Delete task |
| `GET` | `/v1/tasks/{id}/messages` | Flat message list |
| `GET` | `/v1/tasks/{id}/artifacts` | Workspace files |

### 2.2 POST /v1/tasks

**Request:** `{}` hoặc optional metadata

**Response:**
```json
{
  "id": "uuid",
  "title": null,
  "status": "active",
  "type": null,
  "created_at": "ISO8601"
}
```

**Side effects:**
- [ ] 1. Insert Task: `status=active`, `type=null`, `title=null`
- [ ] 2. Seed File `memory.md` với frontmatter `type: chat`

### 2.3 GET /v1/tasks/{id}/messages

Phase 1 flat list — chưa `branch_info`:

```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "...",
      "parent_id": null,
      "created_at": "..."
    }
  ]
}
```

- [ ] 1. Include agent runs / activities trong assistant messages (nếu có spawn)
- [ ] 2. Order by `created_at` ascending

### 2.4 GET /v1/tasks/{id}/artifacts

```json
{
  "files": [
    {
      "name": "spec.md",
      "content": "...",
      "kind": "text",
      "size": 1234
    }
  ]
}
```

### 2.5 Checklist tasks

- [ ] 1. Mọi route verify `task.user_id == current_user.id` → 403
- [ ] 2. Task not found → 404
- [ ] 3. Dùng service layer — không raw SQL

---

## 3. Stream endpoint

**File:** `apps/api/src/api/routes/stream.py`

### 3.1 POST /v1/tasks/{id}/stream

**Request body:**
```json
{
  "message": "tạo dashboard doanh thu",
  "parent_id": null,
  "mode": "auto",
  "thinking_enabled": false
}
```

### 3.2 Handler flow

```
1. verify_task_ownership(task_id, user_id)
2. acquire_stream_lock(task_id)
   → StreamLockError → 409 "Task is already being processed"
3. artifact_buffer = ArtifactBuffer()
4. abort_signal = asyncio.Event()
5. register abort_signal in store (for /stop)
6. ctx = RuntimeContext(...)
7. start heartbeat background task
8. return StreamingResponse(
     run_task(ctx) → serialize SSE events
   )
9. finally:
   - release_stream_lock
   - cancel heartbeat
   - unregister abort_signal
   - safety flush/clear artifact_buffer
```

### 3.3 SSE response

- [ ] 1. `Content-Type: text/event-stream`
- [ ] 2. Serialize events: `data: {json}\n\n`
- [ ] 3. Include heartbeat during idle
- [ ] 4. End with `stream_done` or `stream_error`

### 3.4 Guards integration

- [ ] 1. Pending message reuse ([04-streaming-system.md](./04-streaming-system.md))
- [ ] 2. 5-second dedup
- [ ] 3. Client disconnect → không cancel background task

### 3.5 Error responses

| Status | Condition |
|--------|-----------|
| 401 | No valid JWT |
| 403 | Task not owned by user |
| 404 | Task not found |
| 409 | Stream lock held |
| 429 | Rate limit — **Phase 2** |

---

## 4. Stop endpoint

**File:** `apps/api/src/api/routes/stream.py` (hoặc `stop.py`)

### 4.1 POST /v1/tasks/{id}/stop

- [ ] 1. Verify ownership
- [ ] 2. Lookup abort_signal for task_id
- [ ] 3. `abort_signal.set()`
- [ ] 4. Wait main loop acknowledge (optional timeout)
- [ ] 5. Response: `{ "partial_message_id": "uuid" }`

### 4.2 Behavior

- [ ] Main loop stops iteration
- [ ] Flush artifact buffer
- [ ] Emit `stream_done` với `partial_message_id`
- [ ] Release stream lock

---

## 5. Auth integration

**Không implement mới** — dùng auth đã có.

**File reference:** [`auth/02-backend.md`](../auth/02-backend.md)

### 5.1 Dependencies

- [ ] 1. `get_current_user` dependency trên mọi protected route
- [ ] 2. `POST /v1/auth/login` → JWT httpOnly cookie
- [ ] 3. Protected endpoint không có cookie → 401

### 5.2 Phase 1 auth scope

- [ ] Single-user JWT — không multi-tenant admin
- [ ] Task ownership via `user_id` FK

---

## 6. LLM budget endpoint

**File:** `apps/api/src/api/routes/llm.py`

### 6.1 GET /v1/llm/budget

**Response:**
```json
{
  "contextWindow": 128000,
  "inputBudgetTokens": 120000,
  "microCompactFraction": 0.6,
  "summaryCompactFraction": 0.8,
  "keepTokens": 40000,
  "initialTokensPerChar": 0.34,
  "imageCharEquiv": 6000
}
```

- [ ] 1. Public endpoint (hoặc auth optional)
- [ ] 2. Values từ `packages/core/src/core/llm/budget.py`
- [ ] 3. FE không hardcode numbers

---

## 7. Health & meta

- [ ] 1. `GET /health` → `{ "status": "ok" }`
- [ ] 2. `GET /v1/meta` optional — version, build info

---

## 8. Router registration

**File:** `apps/api/src/api/main.py`

```python
# Conceptual
app.include_router(auth_router, prefix="/v1/auth")
app.include_router(tasks_router, prefix="/v1/tasks")
app.include_router(stream_router, prefix="/v1/tasks")
app.include_router(llm_router, prefix="/v1/llm")
```

- [ ] 1. CORS middleware cho `localhost:3000`
- [ ] 2. Exception handlers → JSON errors
- [ ] 3. Lifespan: Redis connection pool, DB engine

---

## 9. Manual E2E test script

```bash
# 1. Login
curl -c cookies.txt -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}'

# 2. Create task
TASK_ID=$(curl -b cookies.txt -X POST http://localhost:8000/v1/tasks | jq -r .id)

# 3. Stream
curl -b cookies.txt -N -X POST "http://localhost:8000/v1/tasks/$TASK_ID/stream" \
  -H "Content-Type: application/json" \
  -d '{"message":"tạo dashboard doanh thu","mode":"auto"}'

# 4. Artifacts
curl -b cookies.txt "http://localhost:8000/v1/tasks/$TASK_ID/artifacts"
```

---

## 10. Definition of done — step 09

- [ ] All task CRUD endpoints functional
- [ ] Stream returns SSE `main_text` + `agent_*` + `file_artifact` + `stream_done`
- [ ] 409 on concurrent stream
- [ ] Stop endpoint works during active stream
- [ ] Auth 401 without cookie
- [ ] Budget endpoint returns required keys

---

## 11. Cross-references

| File | Liên quan |
|------|-----------|
| [10-checklist.md](./10-checklist.md) | Full E2E definition of done |
| [`auth/04-api-contracts.md`](../auth/04-api-contracts.md) | Auth API contracts |
| [`UI/02-ui-features-chat-agent.md`](../../UI/02-ui-features-chat-agent.md) | FE integration |
