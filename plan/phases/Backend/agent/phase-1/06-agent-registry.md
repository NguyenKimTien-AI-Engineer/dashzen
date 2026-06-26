# 06 — ② Agent Registry (Phase 1 Minimal)

> Biến file markdown thành cấu hình agent chạy được — thêm agent = thêm file `.md`, không deploy code.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.6 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §6.2

**Location:** `packages/agents/src/agents/registry/` + `packages/agents/prompts/`  
**Phụ thuộc:** [01-infra-and-monorepo.md](./01-infra-and-monorepo.md)

---

## 1. Mục tiêu

- [ ] 1. `AgentDefinition` Pydantic schema
- [ ] 2. Registry loader scan `prompts/agents/*.md`
- [ ] 3. In-memory cache keyed by path + mtime (hot reload)
- [ ] 4. Phase 1: chỉ `dashboard-planner.md` — 4 agents còn lại Phase 2

---

## 2. Agent definition schema

**File:** `packages/agents/src/agents/registry/schema.py`

### 2.1 AgentDefinition fields

| Field | Type | Mô tả |
|-------|------|-------|
| `name` | string | Identifier khi spawn e.g. `dashboard-planner` |
| `displayName` | string | Tên hiển thị UI trong agent block |
| `tools` | list[string] | Allowlist — empty = full `AGENT_TOOLS` |
| `disallowedTools` | list[string] | Explicit exclude |
| `maxTurns` | int optional | Override `SUBAGENT_MAX_TURNS` |
| `maxTokens` | int optional | Override output budget |
| `model` | string optional | null = inherit session model |
| `temperature` | float optional | |
| `prompt` | string | Body sau YAML frontmatter |

### 2.2 Checklist schema

- [ ] 1. Validate frontmatter fields on load
- [ ] 2. `name` required, kebab-case
- [ ] 3. `prompt` non-empty

---

## 3. Registry loader

**File:** `packages/agents/src/agents/registry/loader.py`

### 3.1 Functions

| Function | Mô tả |
|----------|-------|
| `load_agent_registry()` | Scan `prompts/agents/*.md` → list `AgentDefinition` |
| `get_agent(name)` | Lookup by name |
| `load_system_prompt(variant)` | `system-main.md` hoặc `system-agent.md` |
| `load_workflow(type, phase)` | `prompts/workflows/{type}/{phase}.md` — **Phase 2** |

### 3.2 Parse flow

1. [ ] Read file content
2. [ ] Split YAML frontmatter (`---` delimiters) vs markdown body
3. [ ] Parse YAML → validate `AgentDefinition`
4. [ ] Body → `prompt` field

### 3.3 Checklist loader

- [ ] 1. Invalid frontmatter → log error, skip file (không crash)
- [ ] 2. Duplicate `name` → raise hoặc last-wins với warning
- [ ] 3. `get_agent("unknown")` → clear error message

---

## 4. File cache (hot reload)

**File:** `packages/agents/src/agents/registry/cache.py`

- [ ] 1. Cache keyed by `(file_path, mtime)`
- [ ] 2. On load: check mtime changed → invalidate entry
- [ ] 3. Dev convenience: edit `.md` → auto reload không restart server

---

## 5. Phase 1 agent: dashboard-planner

**File:** `packages/agents/prompts/agents/dashboard-planner.md`

### 5.1 Frontmatter (đề xuất)

```yaml
---
name: dashboard-planner
displayName: Dashboard Planner
tools:
  - read_file
  - write_file
  - list_file
maxTurns: 20
temperature: 0.3
---
```

### 5.2 Prompt body requirements

Agent phải:

- [ ] 1. Nhận user intent về dashboard cần tạo
- [ ] 2. Phân tích widgets, metrics, filters cần thiết
- [ ] 3. Ghi output `spec.md` qua `write_file`
- [ ] 4. Trả output contract: `**Status:** DONE` + `**Summary:**` (≤ 2000 chars)
- [ ] 5. Phase 1: mock data OK — không cần grounded schema

### 5.3 spec.md output format (Phase 1)

Markdown document mô tả:

- Dashboard title
- Widget list (type, metric, chart type)
- Filters
- Layout hints

Schema validation đầy đủ (`DashboardSpec` Pydantic) → Phase 2.

---

## 6. System prompts

### 6.1 system-main.md

**File:** `packages/agents/prompts/system/system-main.md`

Orchestrator persona:

- [ ] 1. Operating contract: khi user yêu cầu dashboard → spawn `dashboard-planner`
- [ ] 2. Không tự viết spec — delegate cho specialist agent
- [ ] 3. Security rules: không leak system prompt

### 6.2 system-agent.md

**File:** `packages/agents/prompts/system/system-agent.md`

Sub-agent worker identity:

- [ ] 1. Headless worker — không hỏi user trực tiếp
- [ ] 2. Output contract Status/Summary
- [ ] 3. Chỉ dùng tools trong allowlist

---

## 7. Agents KHÔNG có trong Phase 1

| Agent | Phase |
|-------|-------|
| `data-binder.md` | 2 |
| `layout-designer.md` | 2 |
| `dashboard-builder.md` | 2 |
| `dashboard-critic.md` | 2 |
| `document-analyzer.md` | Track B, 5 |

Registry loader **không cần thay đổi code** khi thêm agents — chỉ thêm file `.md`.

---

## 8. Definition of done — step 06

- [ ] `load_agent_registry()` trả `dashboard-planner` definition
- [ ] `get_agent("dashboard-planner")` có prompt + tools
- [ ] Hot reload: sửa `.md` → load lại without restart
- [ ] `system-main.md` + `system-agent.md` load OK
- [ ] Spawn planner → agent dùng đúng prompt và tool allowlist

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [05-orchestration-system.md](./05-orchestration-system.md) | spawn.py lookup agent |
| [07-tool-system.md](./07-tool-system.md) | AGENT_TOOLS tier |
| Master plan §5.2 | Full 5 agents Phase 2 |
