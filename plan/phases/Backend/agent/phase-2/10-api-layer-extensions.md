# 10 — API Layer Extensions (Phase 2)

> Bổ sung endpoints: gates, upload, compact, messages branch_info. Extend stream/tasks.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.5.5, §5.6, §5.7, §5.9 | [Phase 1 09-api](../phase-1/09-api-layer.md)

**Location:** `apps/api/src/api/routes/`  
**Phụ thuộc:** Steps 01–09

---

## 1. Mục tiêu

- [ ] 1. Gate endpoints — tool approve/reject + ask submit
- [ ] 2. Upload endpoint
- [ ] 3. Manual compact endpoint
- [ ] 4. Messages API — branch_info + agent_runs
- [ ] 5. Stream body — mode `ask` | `auto`, parent_id for branching
- [ ] 6. Rate limit middleware on routes

---

## 2. Gate endpoints

**File:** `apps/api/src/api/routes/gates.py`

### 2.1 POST /v1/tasks/{id}/gates/tool

Approve hoặc reject tool call trong ask mode.

**Request:**
```json
{
  "call_id": "uuid",
  "decision": "approved" | "rejected",
  "feedback": "optional string"
}
```

- [ ] 1. Verify task ownership
- [ ] 2. Call `resolve_gate(task_id, call_id, decision, feedback)`
- [ ] 3. Lua CAS — chỉ resolve if pending
- [ ] 4. 404 nếu gate không tồn tại hoặc expired

### 2.2 POST /v1/tasks/{id}/gates/ask

Submit answer cho ask_user tool.

**Request:**
```json
{
  "call_id": "uuid",
  "answer": "user text answer"
}
```

- [ ] 1. Store answer in Redis ask gate key
- [ ] 2. Unblock `register_ask_gate` polling
- [ ] 3. Verify ownership

---

## 3. Upload endpoint

**File:** `apps/api/src/api/routes/upload.py`

### 3.1 POST /v1/tasks/{id}/upload

- [ ] Multipart `file` field
- [ ] MIME whitelist: csv, json, png, jpeg, pdf
- [ ] Size cap 10MB
- [ ] Filename sanitization
- [ ] `source: upload` in File record
- [ ] Rate limit: `upload` bucket

**Response:**
```json
{
  "id": "file-uuid",
  "name": "data.csv",
  "source": "upload",
  "kind": "text",
  "size": 1234,
  "content_type": "text/csv"
}
```

---

## 4. Compact endpoint

**File:** `apps/api/src/api/routes/compact.py`

### 4.1 POST /v1/tasks/{id}/compact

Manual trigger summary compact.

- [ ] 1. Verify ownership
- [ ] 2. Không cần stream active
- [ ] 3. Run tier-2 summary compact logic ([05](./05-context-system-compaction.md))
- [ ] 4. Persist role=compact message

**Response:**
```json
{
  "summary": "compressed conversation summary...",
  "compact_message_id": "uuid"
}
```

---

## 5. Messages API extension

**File:** `apps/api/src/api/routes/tasks.py` — extend GET messages

### 5.1 Query params

| Param | Mô tả |
|-------|-------|
| `leaf_id` | Optional — path to specific branch leaf |

### 5.2 Response shape

```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "...",
      "parent_id": null,
      "branch_info": null,
      "agent_runs": []
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "...",
      "parent_id": "...",
      "branch_info": { "sibling_count": 2, "sibling_index": 0 },
      "agent_runs": [
        {
          "call_id": "uuid",
          "name": "dashboard-planner",
          "status": "done",
          "summary": "...",
          "activities": []
        }
      ]
    }
  ],
  "active_leaf_id": "uuid"
}
```

- [ ] 1. `branch_info` per [09](./09-persistence-branching.md)
- [ ] 2. `agent_runs` embedded per assistant message with spawns

---

## 6. Stream endpoint extensions

**POST /v1/tasks/{id}/stream** — extend Phase 1:

### 6.1 Request body

```json
{
  "message": "tạo dashboard doanh thu theo khu vực",
  "parent_id": "uuid-or-null",
  "mode": "auto" | "ask",
  "thinking_enabled": false
}
```

- [ ] 1. `mode: ask` enables HITL gates
- [ ] 2. `parent_id` for branch continuation
- [ ] 3. Rate limit: `task_stream` bucket

### 6.2 Stream finally block

- [ ] 1. `unregister_all_gates(task_id)`
- [ ] 2. `flush_and_remap()` or clear buffer
- [ ] 3. Release lock

---

## 7. Tasks API extensions

### 7.1 POST /v1/tasks

- [ ] Rate limit: `task_create` bucket (30/hour/user)

### 7.2 PATCH /v1/tasks/{id}

- [ ] Support `title` rename (existing)
- [ ] Optional: `status` archive

---

## 8. Rate limit middleware

Apply per [08](./08-streaming-and-rate-limits.md):

| Route | Bucket |
|-------|--------|
| `POST .../stream` | task_stream |
| `POST .../tasks` | task_create |
| `POST .../upload` | upload |
| All `/v1/*` | global |

- [ ] 429 with `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

---

## 9. Router registration

```python
app.include_router(gates_router, prefix="/v1/tasks")
app.include_router(upload_router, prefix="/v1/tasks")
app.include_router(compact_router, prefix="/v1/tasks")
```

- [ ] All new routes use `get_current_user` dependency
- [ ] All task-scoped routes verify ownership

---

## 10. E2E test script (Phase 2 happy path)

```bash
# 1. Create task + stream dashboard request
curl -b cookies -N -X POST "$API/tasks/$TASK_ID/stream" \
  -d '{"message":"tạo dashboard doanh thu theo khu vực","mode":"auto"}'

# 2. Verify artifacts
curl -b cookies "$API/tasks/$TASK_ID/artifacts"
# Expect: spec.md, bindings.md, layout.md, page.tsx, review.md

# 3. Ask mode test
curl -b cookies -N -X POST "$API/tasks/$TASK_ID/stream" \
  -d '{"message":"sửa chart thành bar","mode":"ask"}'
# → main_tool → POST gates/tool approve

# 4. Upload CSV
curl -b cookies -X POST "$API/tasks/$TASK_ID/upload" -F "file=@data.csv"

# 5. Manual compact
curl -b cookies -X POST "$API/tasks/$TASK_ID/compact"
```

---

## 11. Definition of done — step 10

- [ ] All gate endpoints functional
- [ ] Upload + compact endpoints functional
- [ ] Messages API returns branch_info + agent_runs
- [ ] Stream accepts mode=ask
- [ ] Rate limits return 429 with headers

---

## 12. Cross-references

| File | Liên quan |
|------|-----------|
| [11-checklist.md](./11-checklist.md) | Full E2E DoD |
| [06-gate-system-hitl.md](./06-gate-system-hitl.md) | Gate service |
| [Phase 1 09](../phase-1/09-api-layer.md) | Baseline API |
