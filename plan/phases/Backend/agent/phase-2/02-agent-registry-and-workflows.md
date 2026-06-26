# 02 — ② Agent Registry — Full 5 Agents & Workflows

> Thêm 4 agents còn lại + 4 workflow files. Registry loader **không đổi code** — chỉ thêm `.md` files.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.2

**Location:** `packages/agents/prompts/agents/` + `packages/agents/prompts/workflows/`  
**Phụ thuộc:** [Phase 1 06-agent-registry](../phase-1/06-agent-registry.md)

---

## 1. Mục tiêu

- [ ] 1. 5 specialist agent markdown files
- [ ] 2. 4 workflow markdown files
- [ ] 3. `dashboard-planner.md` updated — conform `DashboardSpec` schema
- [ ] 4. Loader hot-reload picks up new files

---

## 2. Five specialist agents

**Directory:** `packages/agents/prompts/agents/`

### 2.1 dashboard-planner.md

| Field | Value |
|-------|-------|
| Input | User intent |
| Output | `spec.md` |
| Tools | `read_file`, `write_file` |
| maxTurns | 20 |
| Schema | Output **phải conform `DashboardSpec`** Pydantic schema |

**Prompt requirements:**

- [ ] 1. Phân tích widgets, metrics, filters, layout hints
- [ ] 2. Ghi `spec.md` qua `write_file`
- [ ] 3. Output contract: `**Status:** DONE` + `**Summary:**` ≤ 2000 chars

### 2.2 data-binder.md

| Field | Value |
|-------|-------|
| Input | `spec.md` |
| Output | `bindings.md` |
| Tools | `read_file`, `write_file`, `schema_inspector` |
| Grounding | **Không được bịa metric** không có trong schema |

**Prompt requirements:**

- [ ] 1. Map từng metric → query/API binding
- [ ] 2. Dùng `schema_inspector` — Phase 2 mock schema hardcoded trong tool
- [ ] 3. Validate grounded generation

### 2.3 layout-designer.md

| Field | Value |
|-------|-------|
| Input | `spec.md` + `bindings.md` |
| Output | `layout.md` |
| Tools | `read_file`, `write_file` |

**Prompt requirements:**

- [ ] 1. Grid layout responsive
- [ ] 2. Positions, sizes, breakpoints per widget
- [ ] 3. Biết Recharts component types và sizing constraints

### 2.4 dashboard-builder.md

| Field | Value |
|-------|-------|
| Input | `spec.md` + `bindings.md` + `layout.md` |
| Output | `page.tsx` + widget files |
| Tools | `read_file`, `write_file`, `edit_file` |
| maxTurns | **Cao nhất** trong 5 agents |
| maxTokens | Có thể lớn hơn default |

**Prompt requirements:**

- [ ] 1. Sinh React component `page.tsx`
- [ ] 2. Widget files theo spec
- [ ] 3. Agent nặng nhất — cần budget cao

### 2.5 dashboard-critic.md

| Field | Value |
|-------|-------|
| Input | Tất cả output files |
| Output | `review.md` |
| Tools | `read_file`, `write_file` |

**Validation scope:**

- [ ] 1. Spec compliance
- [ ] 2. a11y basics
- [ ] 3. Grounded claims — widget không bind metric không tồn tại trong bindings.md
- [ ] 4. Render sanity check
- [ ] 5. Output: status **PASS** hoặc **FAIL** + list issues

---

## 3. Workflow files

**Directory:** `packages/agents/prompts/workflows/`

### 3.1 dashboard/create-dashboard.md

- [ ] 1. Mô tả spawn sequence cho orchestrator:
  - Bước 1: spawn planner
  - Bước 2: spawn binder
  - Bước 3: spawn designer
  - Bước 4: spawn builder
  - Bước 5: spawn critic
- [ ] 2. Mỗi bước có **acceptance criteria**
- [ ] 3. Orchestrator check output trước khi spawn bước tiếp
- [ ] 4. Critic FAIL → chuyển repair workflow

### 3.2 dashboard/edit-dashboard.md

- [ ] 1. Edit dashboard đã có
- [ ] 2. Planner đọc spec cũ + user request → updated spec
- [ ] 3. Pipeline tiếp tục từ binder

### 3.3 dashboard/repair-dashboard.md

- [ ] 1. Đọc `review.md` với list issues
- [ ] 2. Minor issues → builder chỉnh tại chỗ
- [ ] 3. Fundamental issues → restart từ planner

### 3.4 chat/create-chat.md

- [ ] 1. Free-form conversation
- [ ] 2. Thu thập thông tin dashboard user muốn build
- [ ] 3. Trước khi trigger `create-dashboard` workflow

---

## 4. DashboardSpec schema

**File:** `packages/core/src/core/schemas/dashboard_spec.py` (hoặc tương đương)

- [ ] 1. Pydantic model `DashboardSpec`
- [ ] 2. Fields: widgets, metrics, filters, layout hints
- [ ] 3. Validate planner output spec.md (Phase 3 fail-closed export)
- [ ] 4. Phase 2: validation optional warning — full fail-closed Phase 3

---

## 5. Registry loader — no code change

Từ Phase 1 `loader.py`:

- [ ] 1. `load_agent_registry()` auto picks up 5 files
- [ ] 2. `load_workflow(type, phase)` loads workflow files
- [ ] 3. Hot reload on mtime change

---

## 6. Agent frontmatter checklist

Mỗi agent file cần:

```yaml
---
name: agent-name
displayName: Display Name
tools: [...]
disallowedTools: []
maxTurns: N
maxTokens: optional
model: optional
temperature: 0.3
---
```

- [ ] 1. `name` kebab-case, unique
- [ ] 2. `tools` allowlist matches agent role
- [ ] 3. `AGENT_TOOLS` tier enforced at spawn

---

## 7. Definition of done — step 02

- [ ] 5 agent files exist và load OK
- [ ] 4 workflow files exist và `load_workflow()` returns content
- [ ] `get_agent("data-binder")` etc. resolve correctly
- [ ] create-dashboard.md documents 5-step spawn + acceptance criteria

---

## 8. Cross-references

| File | Liên quan |
|------|-----------|
| [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) | workflow.py parses spawn sequence |
| [01-memory-system.md](./01-memory-system.md) | Workflow inject via set_memory |
| [Phase 1 06](../phase-1/06-agent-registry.md) | Loader baseline |
