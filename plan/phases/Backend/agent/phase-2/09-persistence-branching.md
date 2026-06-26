# 09 — ⑩ Persistence — Message Tree Branching

> Full tree structure — regenerate tạo nhánh mới, branch_info API, AgentRun reload cho UI.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.9

**Location:** `packages/db/src/db/services/message_service.py` + API response shaping  
**Phụ thuộc:** [Phase 1 03-persistence](../phase-1/03-persistence-system.md)

---

## 1. Mục tiêu

- [ ] 1. Message tree branching — regenerate/edit tạo nhánh mới
- [ ] 2. `GET /messages` trả `branch_info` cho siblings
- [ ] 3. AgentRun activities trong messages response
- [ ] 4. Compact role messages — UI boundary (ẩn, không xóa)

---

## 2. Message tree branching

### 2.1 Regenerate assistant message

- [ ] 1. User regenerate assistant message tại node X
- [ ] 2. Tạo message **mới** với cùng `parent_id` — **không overwrite**
- [ ] 3. Tạo nhánh mới từ điểm đó
- [ ] 4. FE navigate giữa sibling branches

### 2.2 Edit user message

- [ ] 1. User edit user message tại node X
- [ ] 2. Tạo user message mới — cùng `parent_id`
- [ ] 3. New branch từ edited point

### 2.3 Stream with parent_id

- [ ] `POST /stream` body `parent_id` trỏ leaf của branch hiện tại
- [ ] `get_tree_path(task_id, parent_id)` load đúng branch history

---

## 3. branch_info in API response

**GET /v1/tasks/{id}/messages**

Mỗi message có siblings:

```json
{
  "id": "uuid",
  "role": "assistant",
  "content": "...",
  "parent_id": "...",
  "branch_info": {
    "sibling_count": 3,
    "sibling_index": 1
  }
}
```

- [ ] 1. `branch_info` chỉ present khi message có siblings
- [ ] 2. `sibling_count` — tổng nhánh tại parent
- [ ] 3. `sibling_index` — 0-based index nhánh hiện tại
- [ ] 4. DoD #10: regenerate → new branch + branch_info

### 3.1 Query logic

- [ ] 1. Group messages by `parent_id`
- [ ] 2. Count siblings per group
- [ ] 3. Determine index by created_at order

---

## 4. Compact role boundary

Messages `role=compact`:

- [ ] 1. **Boundary marker** — messages trước compact boundary ẩn trong UI
- [ ] 2. **Không xóa** — tránh mất dữ liệu
- [ ] 3. `build_history()` xử lý đặc biệt ([05](./05-context-system-compaction.md))
- [ ] 4. FE: không render messages before compact boundary

---

## 5. AgentRun reload cho UI

**GET /v1/tasks/{id}/messages** bổ sung:

Cho mỗi assistant message có tool call `spawn_agent`:

```json
{
  "role": "assistant",
  "tool_calls": [...],
  "agent_runs": [
    {
      "call_id": "uuid",
      "name": "dashboard-planner",
      "status": "done",
      "summary": "...",
      "activities": [...]
    }
  ]
}
```

- [ ] 1. Join AgentRun records by `message_id`
- [ ] 2. FE reconstruct agent activity timeline từ `activities` JSON
- [ ] 3. DoD #11: old task reload shows activities per spawn

### 5.1 activities JSON schema

Từ Phase 1 — cap `ACTIVITY_RESULT_MAX` = 2000 chars, `ACTIVITY_COUNT_MAX` = 200 entries.

---

## 6. message_service updates

| Function | Update |
|----------|--------|
| `get_messages(db, task_id, leaf_id?)` | Optional leaf for branch path |
| `get_siblings(db, parent_id)` | For branch_info |
| `create_message_branch(db, ...)` | Regenerate helper |

- [ ] 1. `get_tree_path` supports any leaf node
- [ ] 2. Efficient query — avoid N+1 for agent_runs

---

## 7. Partial message on stop

Từ [08-streaming](./08-streaming-and-rate-limits.md) stop handshake:

- [ ] 1. Partial assistant message persisted with correct `parent_id`
- [ ] 2. Branch structure maintained

---

## 8. Definition of done — step 09

- [ ] Regenerate assistant → sibling branch created
- [ ] GET /messages returns branch_info
- [ ] Switch branch via parent_id in stream request
- [ ] Agent runs with activities visible on message reload
- [ ] Compact messages hidden before boundary in FE contract

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [05-context-system-compaction.md](./05-context-system-compaction.md) | compact role messages |
| [10-api-layer-extensions.md](./10-api-layer-extensions.md) | messages API shape |
| [`UI/02-ui-features-chat-agent.md`](../../UI/02-ui-features-chat-agent.md) | Branch navigation UI |
