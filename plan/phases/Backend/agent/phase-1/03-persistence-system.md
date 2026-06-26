# 03 — ⑩ Persistence System

> DB schema + data access layer — không subsystem nào dùng raw SQLAlchemy session ngoài service layer.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.3 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §6.10

**Location:** `packages/db/`  
**Phụ thuộc:** [01-infra-and-monorepo.md](./01-infra-and-monorepo.md)

---

## 1. Mục tiêu

- [ ] 1. SQLAlchemy models: Task, Message, File, AgentRun
- [ ] 2. Alembic migration 001 apply
- [ ] 3. CRUD service layer per model
- [ ] 4. Seed `memory.md` khi tạo task

---

## 2. Task model

**File:** `packages/db/src/db/models/task.py`

| Column | Type | Mô tả |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | Task ownership |
| `title` | String nullable | null = "Untitled" — set bởi auto-title |
| `status` | Enum | `active` \| `archived` |
| `type` | String nullable | null → `chat` → `dashboard` (one-way) |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Checklist Task

- [ ] 1. Index trên `user_id`
- [ ] 2. Index trên `type` (cho Memory FSM Phase 2)
- [ ] 3. `user_id` FK enforce ownership

---

## 3. Message model

**File:** `packages/db/src/db/models/message.py`

| Column | Type | Mô tả |
|--------|------|-------|
| `id` | UUID PK | |
| `task_id` | UUID FK | |
| `role` | Enum | `user` \| `assistant` \| `tool` \| `compact` |
| `content` | Text | Message body |
| `parent_id` | UUID FK nullable | Self-ref → tree structure |
| `prompt_tokens` | Int nullable | Exact count từ provider (assistant only) |
| `thinking` | Text nullable | Encoded thinking blocks |
| `created_at` | DateTime | |

### Checklist Message

- [ ] 1. Index `(task_id, created_at)` cho list queries
- [ ] 2. Index `parent_id` cho tree traversal
- [ ] 3. `get_tree_path(task_id, leaf_id)` — path root → leaf
- [ ] 4. Phase 1: flat list OK; tree structure sẵn sàng Phase 2 branching

---

## 4. File model

**File:** `packages/db/src/db/models/file.py`

| Column | Type | Mô tả |
|--------|------|-------|
| `id` | UUID PK | |
| `task_id` | UUID FK | |
| `message_id` | UUID FK nullable | null = chưa link message |
| `name` | String | e.g. `spec.md`, `memory.md` |
| `source` | Enum | `workspace` \| `upload` |
| `kind` | Enum | `text` \| `image` \| `binary` |
| `content` | Text nullable | Text files only |
| `url` | String nullable | MinIO URL cho binary/image |
| `content_type` | String nullable | MIME |
| `size` | Int | Bytes |
| `created_at` | DateTime | |

### Checklist File

- [ ] 1. **Không** unique constraint `(task_id, name)` — branching cho phép nhiều version
- [ ] 2. Overwrite-by-name ở application layer ([08-artifact-system.md](./08-artifact-system.md))
- [ ] 3. Index `(task_id, name)` cho lookup

---

## 5. AgentRun model

**File:** `packages/db/src/db/models/agent_run.py`

| Column | Type | Mô tả |
|--------|------|-------|
| `id` | UUID PK | |
| `message_id` | UUID FK | Message chứa spawn tool call |
| `call_id` | UUID | Unique per spawn invocation |
| `name` | String | Agent name e.g. `dashboard-planner` |
| `activities` | JSON | Activity timeline array |
| `status` | Enum | `done` \| `wait` \| `fail` |
| `summary` | Text nullable | Agent output summary |
| `created_at` | DateTime | |

### Activities JSON schema (Phase 1 basic)

```json
[
  {
    "tool": "write_file",
    "args": {"path": "spec.md"},
    "result": "... truncated to ACTIVITY_RESULT_MAX ...",
    "ts": "ISO8601"
  }
]
```

### Checklist AgentRun

- [ ] 1. Composite unique index `(message_id, call_id)` — upsert idempotent
- [ ] 2. Cap result length `ACTIVITY_RESULT_MAX` = 2,000 chars
- [ ] 3. Cap entries `ACTIVITY_COUNT_MAX` = 200

---

## 6. CRUD service layer

**Location:** `packages/db/src/db/services/`

### 6.1 task_service.py

| Function | Mô tả |
|----------|-------|
| `create_task(db, user_id)` | Tạo task + seed memory.md |
| `list_tasks(db, user_id)` | List tasks của user |
| `get_task(db, task_id, user_id)` | Get + ownership check |
| `update_task(db, task_id, **fields)` | Rename, archive |
| `delete_task(db, task_id)` | Delete cascade messages/files |
| `bulk_delete_tasks(db, user_id, ids)` | Bulk delete |

**Seed memory.md khi create:**

```yaml
---
type: chat
phase: create-chat
---
```

- [ ] 1. Tạo File record `memory.md` với content trên
- [ ] 2. `type: chat` trong frontmatter

### 6.2 message_service.py

| Function | Mô tả |
|----------|-------|
| `create_message(db, ...)` | Single message |
| `create_messages_batch(db, ...)` | Batch insert |
| `get_messages(db, task_id)` | Flat list Phase 1 |
| `get_tree_path(db, task_id, leaf_id)` | Root → leaf path |

### 6.3 file_service.py

| Function | Mô tả |
|----------|-------|
| `upsert_workspace_file(db, task_id, name, ...)` | Overwrite-by-name logic |
| `get_artifacts(db, task_id)` | List workspace files |
| `get_file(db, task_id, name)` | Single file lookup |
| `list_files(db, task_id)` | Name + size + kind |

### 6.4 agent_run_service.py

| Function | Mô tả |
|----------|-------|
| `upsert_agent_run(db, message_id, call_id, ...)` | Idempotent upsert |
| `get_agent_runs(db, message_id)` | List runs for message |

### Checklist services

- [ ] 1. Không raw SQL trong `apps/api` routes
- [ ] 2. Async SQLAlchemy session pattern
- [ ] 3. Ownership verify ở route layer, không trong service (hoặc optional param)

---

## 7. Migration 001

- [ ] 1. Tạo tables: `tasks`, `messages`, `files`, `agent_runs`
- [ ] 2. FK constraints + indexes
- [ ] 3. Không conflict với auth `users` migration
- [ ] 4. `alembic upgrade head` trên dev DB

---

## 8. Definition of done — step 03

- [ ] `POST /v1/tasks` tạo task với `status=active`, `type=null`, `title=null`
- [ ] Workspace file `memory.md` tồn tại với `type: chat`
- [ ] `GET /v1/tasks/{id}/messages` trả flat list
- [ ] `GET /v1/tasks/{id}/artifacts` trả workspace files
- [ ] AgentRun upsert by `(message_id, call_id)` idempotent

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [08-artifact-system.md](./08-artifact-system.md) | `upsert_workspace_file` implementation |
| [09-api-layer.md](./09-api-layer.md) | REST routes gọi services |
| [`auth/02-backend.md`](../auth/02-backend.md) | User model baseline |
