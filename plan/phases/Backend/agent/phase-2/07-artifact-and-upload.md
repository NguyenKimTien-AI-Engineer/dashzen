# 07 — ⑧ Artifact System — Production Buffer & Upload

> Nâng cấp ArtifactBuffer với flush_and_remap + file upload endpoint.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.7

**Location:** `packages/agents/src/agents/artifacts/` + `apps/api/src/api/routes/upload.py`  
**Phụ thuộc:** [Phase 1 08-artifact-system](../phase-1/08-artifact-system.md)

---

## 1. Mục tiêu

- [ ] 1. `flush_and_remap()` — link files về final assistant message
- [ ] 2. `POST /v1/tasks/{id}/upload` — attach files
- [ ] 3. MIME whitelist + size cap + path traversal prevention
- [ ] 4. Uploaded files `source: upload`

---

## 2. ArtifactBuffer nâng cấp

**File:** `packages/agents/src/agents/artifacts/buffer.py`

### 2.1 flush_and_remap()

```python
flush_and_remap(
    db, task_id,
    tool_call_msg_ids,
    final_message_id,
    run_started_at
)
```

**Sau khi main loop kết thúc turn:**

- [ ] 1. Flush tất cả staged entries → DB
- [ ] 2. Remap `message_id` của files tạo trong turn → `final_message_id`
- [ ] 3. `final_message_id` = assistant message cuối cùng của turn
- [ ] 4. UI canvas hiển thị files linked với assistant message — **không** tool messages

### 2.2 vs Phase 1 flush

| Phase 1 | Phase 2 |
|---------|---------|
| `flush()` basic | `flush_and_remap()` với ownership |
| message_id optional | message_id = final assistant |

### 2.3 run_started_at filter

- [ ] Chỉ remap files created during current run (timestamp filter)
- [ ] Tránh remap files từ turns trước

---

## 3. Phantom file prevention (production)

Giữ behavior Phase 1, verify Phase 2 scenarios:

| Scenario | Expected |
|----------|----------|
| Cancel stream during builder writing page.tsx | **No** page.tsx in artifacts |
| POST /stop during builder | Files flushed **before** stop point kept |
| Successful 5-agent pipeline | All 5 output files in artifacts with correct message_id |

- [ ] 1. DoD #7 Phase 2: cancel mid-builder → no phantom page.tsx
- [ ] 2. DoD #8: stop → partial files flushed correctly

---

## 4. File upload endpoint

**File:** `apps/api/src/api/routes/upload.py`

### 4.1 POST /v1/tasks/{id}/upload

- [ ] 1. Multipart file upload
- [ ] 2. Task ownership verification — reject nếu không thuộc user
- [ ] 3. Store file trong File model + MinIO nếu binary

### 4.2 Validation

| Rule | Value |
|------|-------|
| MIME whitelist | `text/csv`, `application/json`, `image/png`, `image/jpeg`, `application/pdf` |
| Size cap | 10MB |
| Filename | Strip `../`, `/`, `\` — path traversal prevention |
| source | `upload` (phân biệt workspace files) |

### 4.3 Storage

| kind | Storage |
|------|---------|
| text (csv) | `content` column + optional MinIO |
| image | MinIO `url` |
| binary/pdf | MinIO `url` |

- [ ] 1. `content_type` từ validated MIME
- [ ] 2. Appear in `GET /artifacts` với `source: upload`

### 4.4 Rate limit

- [ ] `upload` bucket: 30 uploads/giờ/user ([08](./08-streaming-and-rate-limits.md))

---

## 5. csv_preview integration

- [ ] 1. `csv_preview` tool reads uploaded CSV (`source: upload`)
- [ ] 2. DoD #15: upload CSV → artifacts với source=upload

---

## 6. Definition of done — step 07

- [ ] flush_and_remap links spec.md/page.tsx to final assistant message
- [ ] Cancel mid-builder → no phantom page.tsx in GET /artifacts
- [ ] POST /stop → partial files flushed, visible in artifacts
- [ ] Upload CSV → source=upload in artifacts
- [ ] Path traversal in filename rejected

---

## 7. Cross-references

| File | Liên quan |
|------|-----------|
| [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) | main_loop calls flush_and_remap |
| [04-tool-system-full-pipeline.md](./04-tool-system-full-pipeline.md) | csv_preview |
| [10-api-layer-extensions.md](./10-api-layer-extensions.md) | Upload route details |
