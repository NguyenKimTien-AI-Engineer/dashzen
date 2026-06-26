# 08 — ⑨ Streaming — Full Guards & Rate Limiting

> Production resilience guards bổ sung + 5 Redis token bucket rate limits.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.8

**Location:** `packages/agents/src/agents/streaming/guards.py` + `packages/agents/src/agents/streaming/rate_limit.py`  
**Phụ thuộc:** [Phase 1 04-streaming](../phase-1/04-streaming-system.md)

---

## 1. Mục tiêu

- [ ] 1. Production resilience guards (enhance Phase 1)
- [ ] 2. 5 rate limit buckets — Redis token bucket algorithm
- [ ] 3. 429 responses với standard headers

---

## 2. Production resilience guards

**File:** `packages/agents/src/agents/streaming/guards.py`

Bổ sung/harden so với Phase 1:

### 2.1 Pending message reuse

- [ ] Trước main loop tạo user message
- [ ] Check orphan user message (no assistant response — crash trước)
- [ ] Nội dung giống request hiện tại → reuse message ID

### 2.2 5-second dedup

- [ ] Track `(task_id, content_hash, timestamp)` tuples
- [ ] Exact same request trong 5s → **200 OK** với `message: "deduplicated"`
- [ ] Không gọi LLM

### 2.3 Safety-net orphan lock monitor

- [ ] Background asyncio task scan periodically
- [ ] Lock không được refresh (heartbeat stopped) → abort + cleanup

### 2.4 Stop handshake (enhanced)

`POST /stop` không chỉ set abort signal:

- [ ] 1. Đợi main loop acknowledge abort
- [ ] 2. Flush artifact buffer (giữ work đã làm)
- [ ] 3. Tạo partial assistant message trong DB
- [ ] 4. Return `partial_message_id` để FE reload

---

## 3. Rate limiting

**File:** `packages/agents/src/agents/streaming/rate_limit.py`

Redis token bucket algorithm — 5 buckets riêng biệt:

| Bucket | Limit | Trigger |
|--------|-------|---------|
| `task_stream` | 100 requests/giờ/user | `POST /stream` |
| `task_create` | 30 tasks/giờ/user | `POST /tasks` |
| `upload` | 30 uploads/giờ/user | `POST /upload` |
| `dashboard_create` | 20 dashboards/ngày/user | `set_memory` type=dashboard |
| `global` | 1000 requests/phút | Toàn hệ thống |

### 3.1 Implementation

- [ ] 1. Redis keys per bucket: `ratelimit:{bucket}:{user_id}` hoặc `ratelimit:global`
- [ ] 2. Token bucket: refill rate + capacity
- [ ] 3. Check before handler executes
- [ ] 4. Decrement on allowed request

### 3.2 429 response

Khi rate limited:

```
HTTP 429 Too Many Requests
X-RateLimit-Limit: {limit}
X-RateLimit-Remaining: {remaining}
Retry-After: {seconds}
```

- [ ] 1. All three headers present
- [ ] 2. DoD #9: >100 stream requests/hour → 429

### 3.3 dashboard_create bucket

- [ ] Trigger khi `set_memory` changes type to `dashboard`
- [ ] 20 per day per user

---

## 4. Middleware integration

- [ ] 1. Rate limit check in route dependencies hoặc middleware
- [ ] 2. `global` bucket on all `/v1/*` routes
- [ ] 3. Per-route bucket for stream/create/upload

---

## 5. Definition of done — step 08

- [ ] Dedup returns 200 without LLM on duplicate 5s request
- [ ] Stop handshake creates partial assistant message
- [ ] >100 stream/hour → 429 with correct headers
- [ ] Orphan lock monitor releases stale locks
- [ ] dashboard_create rate limit on set_memory

---

## 6. Cross-references

| File | Liên quan |
|------|-----------|
| [10-api-layer-extensions.md](./10-api-layer-extensions.md) | Routes apply rate limits |
| [07-artifact-and-upload.md](./07-artifact-and-upload.md) | Upload bucket |
| [01-memory-system.md](./01-memory-system.md) | dashboard_create trigger |
