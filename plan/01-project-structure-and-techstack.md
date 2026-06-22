# DashZen — Multi-Agent System Architecture

> Kiến trúc dự án & tech stack (v3 — tổ chức theo **system-of-systems**)

## 1. Tổng quan

**DashZen** là một **hệ thống multi-agent** nhận yêu cầu tự nhiên (ví dụ: *"Tạo dashboard doanh thu theo khu vực, có biểu đồ cột và bảng top sản phẩm"*) và sinh ra **dashboard page** hoàn chỉnh: layout, widgets, data binding, và code có thể deploy.

Kiến trúc dựa trên một **self-built agent runtime** (production-proven) — adapt sang Python/FastAPI backend + Next.js Studio UI.

### 1.1 Triết lý kiến trúc

DashZen **không** là một "agent loop" đơn khối. Nó là một **Agent Runtime** đóng vai trò host, được lắp ráp (compose) từ nhiều **subsystem chuyên biệt**, mỗi subsystem có một trách nhiệm duy nhất, interface rõ ràng, và ranh giới phụ thuộc tường minh.

> Mỗi subsystem = một module sở hữu trọn vẹn một mối quan tâm (concern). Đặc tả kiến trúc **và** chi tiết hành vi của concern đó nằm cùng một chỗ — không tách "overview" và "details" ra hai nơi.

```
                         ┌──────────────────────────────┐
   User prompt ───────►  │      AGENT RUNTIME (host)     │  ───────► Dashboard page
                         │  lắp ráp các subsystem dưới  │
                         └──────────────────────────────┘
```

### 1.2 Nguyên tắc thiết kế


| Nguyên tắc                           | Ý nghĩa                                                                        |
| ------------------------------------ | ------------------------------------------------------------------------------ |
| **Single-responsibility subsystems** | Mỗi subsystem một concern, thay thế được độc lập                               |
| **Self-built runtime**               | Orchestration, memory, tool, context tự implement — full control               |
| **Dual-loop**                        | Main loop (persist + điều phối) vs sub-agent loop (ephemeral + compact return) |
| **Prompt-as-config**                 | Agent định nghĩa bằng markdown + YAML — thêm agent không cần deploy code       |
| **Explicit guardrails**              | Max turns, loop detection, Redis gates — không loop vô hạn                     |
| **Fail-closed**                      | Schema validation fail → không render / không deploy                           |
| **Grounded generation**              | Data agent chỉ dùng schema/source đã khai báo, không bịa metric                |
| **Cache-friendly context**           | History prefix ổn định; context block động ở cuối payload                      |


---

## 2. Tech Stack

### 2.1 Core (Backend & Agents)


| Layer                | Công nghệ                           | Lý do chọn                                           |
| -------------------- | ----------------------------------- | ---------------------------------------------------- |
| Language             | **Python 3.12+**                    | Async, typing, ecosystem ML/API                      |
| API                  | **FastAPI**                         | Async, Pydantic native, SSE `StreamingResponse`      |
| Agent runtime        | **Tự build** (`packages/agents/`)   | Compose subsystem — full control                     |
| LLM interface        | **Tự build** (`packages/core/llm/`) | `httpx` streaming; provider adapter                  |
| Schemas & validation | **Pydantic v2**                     | Tool args, dashboard spec, SSE events, API contracts |
| Config               | **pydantic-settings**               | Env-based config dev/staging/prod                    |
| Package manager      | **uv**                              | Lockfile, reproducible builds                        |


### 2.2 LLM Providers


| Mục đích                     | Gợi ý                   | Ghi chú                                    |
| ---------------------------- | ----------------------- | ------------------------------------------ |
| Main orchestrator            | Claude / GPT-4 class    | Tool calling, extended thinking (optional) |
| Sub-agents (specialist)      | Cùng hoặc model nhỏ hơn | Override per-agent trong frontmatter `.md` |
| Dev local                    | **Ollama**              | Default dev                                |
| Fast tasks (classify, title) | Model nhỏ / local       | Giảm cost & latency                        |


Abstract provider qua `LLMClient` (`chat`, `stream`) — interface mỏng, không framework.

### 2.3 Data & Infra backing


| Layer                | Công nghệ                       | Subsystem sử dụng             |
| -------------------- | ------------------------------- | ----------------------------- |
| App DB               | **PostgreSQL**                  | Persistence System            |
| Cache / lock / gates | **Redis**                       | Gate System, Streaming System |
| Vector store         | **Qdrant** (hoặc pgvector)      | Tool System (RAG catalog)     |
| Object storage       | **S3-compatible** (MinIO local) | Artifact System               |


### 2.4 Frontend (Studio UI)


| Layer             | Công nghệ                          | Mục đích                               |
| ----------------- | ---------------------------------- | -------------------------------------- |
| Studio UI         | **Next.js 15** (App Router)        | Chat + canvas preview + debug traces   |
| Dashboard runtime | **React 19** + **TypeScript**      | Page do agent sinh ra                  |
| UI components     | **shadcn/ui** + **Tailwind CSS 4** | Component library                      |
| Charts            | **Recharts**                       | Biểu đồ dashboard                      |
| Chat state        | **useReducer** (TaskContext)       | Streaming state phức tạp               |
| Server state      | **TanStack Query v5**              | CRUD tasks, messages, artifacts        |
| Client UI state   | **Zustand**                        | Sidebar, auth UI — không cho chat core |


### 2.5 Observability & DevOps


| Layer     | Công nghệ                | Mục đích                                |
| --------- | ------------------------ | --------------------------------------- |
| Logging   | **structlog**            | Structured logs, correlation ID         |
| Tracing   | **OpenTelemetry**        | Agent step traces                       |
| Eval      | Custom golden sets       | Dashboard spec validity, render success |
| Container | **Docker** + **Compose** | postgres, redis, qdrant, minio          |
| CI        | GitHub Actions           | Lint, typecheck, test, eval gate        |


---

## 3. Kiến trúc tổng thể — System-of-Systems

### 3.1 Bản đồ subsystem

Agent Runtime lắp ráp 11 subsystem. Mỗi cạnh là một quan hệ "gọi/đọc", không phải import vòng.

```
                          ┌───────────────────────────────────────────┐
                          │            AGENT RUNTIME (host)             │
                          │   run_task() → wiring + lifecycle các SS    │
                          └───────────────────────────────────────────┘
                                            │ điều phối
              ┌─────────────────────────────┼─────────────────────────────┐
              ▼                             ▼                              ▼
   ┌────────────────────┐      ┌────────────────────────┐      ┌────────────────────┐
   │ ① ORCHESTRATION    │◄────►│ ② AGENT REGISTRY       │      │ ③ MEMORY           │
   │   main/sub loop    │ load │   prompt-as-config     │      │   memory.md FSM    │
   │   spawn + workflow │      │   agents/system/wf .md │      │   context blocks   │
   └─────────┬──────────┘      └────────────────────────┘      └─────────┬──────────┘
             │                                                            │ # MEMORY/USER/WF
             ▼ tool calls                                                 ▼
   ┌────────────────────┐      ┌────────────────────────┐      ┌────────────────────┐
   │ ④ TOOL SYSTEM      │◄────►│ ⑤ CONTEXT SYSTEM       │◄────►│ ⑥ LLM SYSTEM       │
   │   registry tiers   │ gate │   budget + compaction  │ msgs │   providers/stream │
   │   exec pipeline    │      │   history builder      │      │   recovery paths   │
   └─────────┬──────────┘      └────────────────────────┘      └────────────────────┘
             │ gate / write
      ┌──────┼───────────────────────────┐
      ▼      ▼                            ▼
┌──────────┐ ┌────────────────────┐  ┌────────────────────┐
│⑦ GATE    │ │ ⑧ ARTIFACT         │  │ ⑨ STREAMING        │
│  HITL    │ │   buffer + file    │  │   EventBus → SSE   │
│  Redis   │ │   staging/flush    │  │   lock + guards    │
└──────────┘ └─────────┬──────────┘  └─────────┬──────────┘
                       ▼                        ▼
              ┌────────────────────┐  ┌────────────────────┐
              │ ⑩ PERSISTENCE      │  │ ⑪ OBSERVABILITY    │
              │   PG msg tree      │  │   logs/trace/eval  │
              │   AgentRun/File    │  │                    │
              └────────────────────┘  └────────────────────┘
```

### 3.2 Catalog subsystem (single source of truth)


| #   | Subsystem          | Trách nhiệm duy nhất                             | Package / vị trí                    | Phụ thuộc | Chi tiết |
| --- | ------------------ | ------------------------------------------------ | ----------------------------------- | --------- | -------- |
| ①   | **Orchestration**  | Dual-loop, spawn_agent, chạy workflow, recovery  | `agents/orchestration/`             | ②③④⑤⑥⑨    | §4       |
| ②   | **Agent Registry** | Nạp & cache agent/system/workflow từ markdown    | `agents/registry/` + `prompts/`     | —         | §5       |
| ③   | **Memory**         | `memory.md` FSM, transitions, lắp context block  | `agents/memory/`                    | ②         | §6       |
| ④   | **Tool**           | Registry tiers, execution pipeline, loop detect  | `agents/tools/` + `packages/tools/` | ⑤⑦⑧       | §7       |
| ⑤   | **Context**        | Token budget, history builder, 2-tier compaction | `agents/context/`                   | ⑥         | §8       |
| ⑥   | **LLM**            | Provider adapter, streaming, recovery messages   | `core/llm/`                         | —         | §9       |
| ⑦   | **Gate (HITL)**    | Redis approval gates, CAS, feedback              | `agents/gates/`                     | — (Redis) | §10      |
| ⑧   | **Artifact**       | Artifact buffer, file model, staging → flush     | `agents/artifacts/`                 | ⑩ (S3)    | §11      |
| ⑨   | **Streaming**      | EventBus, SSE schema, stream lock & guards       | `agents/streaming/`                 | — (Redis) | §12      |
| ⑩   | **Persistence**    | DB models, message tree, branching               | `packages/db/`                      | —         | §13      |
| ⑪   | **Observability**  | Logging, tracing, eval golden sets               | `packages/eval/` + infra            | —         | §14      |


### 3.3 Luật ranh giới (boundary rules)

- **Một concern, một subsystem.** Token budget chỉ Context System sở hữu; gates chỉ Gate System; SSE schema chỉ Streaming System.
- **Orchestration là điểm wiring duy nhất.** Subsystem khác không tự gọi chéo lung tung — chúng nhận dependency qua `RuntimeContext` do Orchestration tạo.
- **Không import vòng.** Hướng phụ thuộc theo bảng §3.2; vi phạm = refactor.
- **Frontend chỉ giao tiếp qua HTTP/SSE** — không import Python.

---

## 4. ① Orchestration System

> **Concern:** Điều phối — quyết định *khi nào* chạy LLM, *khi nào* spawn agent, *khi nào* chạy workflow, và *khi nào* recovery. Là chủ của vòng lặp.

### 4.1 Thành phần


| File                             | Vai trò                                                                  |
| -------------------------------- | ------------------------------------------------------------------------ |
| `orchestration/runtime.py`       | `run_task()` — entry point, wiring tất cả subsystem vào `RuntimeContext` |
| `orchestration/main_loop.py`     | Main loop (orchestrator "DashZen AI")                                    |
| `orchestration/agent_loop.py`    | Sub-agent loop (specialist, ephemeral)                                   |
| `orchestration/spawn.py`         | `spawn_agent` — tạo & chạy sub-agent loop, parse output contract         |
| `orchestration/workflow.py`      | Chạy workflow plugin (spawn sequence + acceptance criteria)              |
| `orchestration/recovery.py`      | LLM recovery paths (max_tokens, empty, thinking-only)                    |
| `orchestration/exec_parallel.py` | Batch tool execution (ủy thác policy cho Tool System)                    |


### 4.2 Dual-loop architecture

Hai vòng lặp LLM tách biệt — pattern cốt lõi:

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN LOOP (main_loop)                                          │
│  • User-facing orchestrator — "DashZen AI"                      │
│  • Persist full message tree (qua Persistence System)           │
│  • Tools: spawn_agent, ask_user, set_memory, read/write file…   │
│  • Max 40 iterations/turn, max 3 spawn_agent/turn               │
└────────────────────────────┬────────────────────────────────────┘
                             │ spawn_agent("dashboard-planner", …)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  SUB-AGENT LOOP (agent_loop)                                    │
│  • Specialist — định nghĩa trong prompts/agents/*.md            │
│  • KHÔNG persist message nội bộ — chỉ trả compact summary       │
│  • Persist AgentRun.activities JSON → UI reload                 │
│  • Tools subset (không spawn_agent, không ask_user)             │
│  • Max 40 turns, timeout 18 phút                                │
└─────────────────────────────────────────────────────────────────┘
```


|                  | **Main loop**                   | **Sub-agent loop**               |
| ---------------- | ------------------------------- | -------------------------------- |
| File             | `orchestration/main_loop.py`    | `orchestration/agent_loop.py`    |
| System prompt    | `prompts/system/system-main.md` | `prompts/system/system-agent.md` |
| Persist messages | Có — message tree               | Không — compact return           |
| UI events        | `main_`*                        | `agent_*`                        |
| Spawn đệ quy     | Có (`spawn_agent`)              | Không                            |


### 4.3 Workflow execution (deterministic pipeline)

Khi Memory System chuyển sang `phase: create-dashboard`, Orchestration chạy workflow plugin thay vì để main loop spawn tùy ý:

```
set_memory({type: dashboard, phase: create-dashboard})
  → Memory System inject workflow create-dashboard.md
  → spawn_agent("dashboard-planner") → spec.md
  → spawn_agent("data-binder")       → bindings.md
  → spawn_agent("layout-designer")   → layout.md
  → spawn_agent("dashboard-builder") → page.tsx
  → spawn_agent("dashboard-critic")  → review.md (pass → done, fail → repair)
```

### 4.4 Spawn contract (sub-agent output)

`spawn.py` enforce hợp đồng output — sub-agent **bắt buộc** kết thúc bằng:

```markdown
**Status:** DONE | WAIT | FAIL
**Summary:** <compact summary cho main loop>
```


| Rule                              | Chi tiết                                                          |
| --------------------------------- | ----------------------------------------------------------------- |
| Output ≤ 4KB                      | Trả full text cho main loop                                       |
| Output > 4KB                      | Chỉ trả Status + Summary — tránh blow-up context                  |
| Thiếu Status/Summary + output lớn | **FAIL** — orchestrator repair                                    |
| `AgentRun.activities`             | JSON timeline (max 200 entries, result cap 2KB/entry) — UI reload |


### 4.5 LLM recovery paths

`recovery.py` xử lý khi LLM trả bất thường (phối hợp LLM System ⑥):

- `append_recovery_messages()` — inject system reminder theo từng failure mode (max_tokens, empty response, thinking-only).
- Retry budget **riêng** per path — không dùng chung max iterations.
- `compaction_exhausted` flag — dừng retry compaction khi đã compact hết.

### 4.6 Task lifecycle phụ trợ


| Concern          | Hành vi                                                                                                                                                                                                                       |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Title generation | Concurrent với turn đầu, model nhỏ. Turns 1–7 đặt title khi đủ rõ (sentinel `UNTITLED`), turn 8+ bắt buộc. Race-safe `UPDATE ... WHERE title IS NULL`. Strong trigger: `set_memory({type: dashboard})`. Emit `task_meta` SSE. |
| Iteration guard  | Max 40 iterations/turn, max 3 spawn/turn                                                                                                                                                                                      |


---

## 5. ② Agent Registry System

> **Concern:** Biến markdown thành cấu hình agent runtime. Là hiện thân của nguyên tắc **prompt-as-config** — thêm agent mới = thêm file `.md`, không deploy code.

### 5.1 Thành phần


| File                 | Vai trò                                                            |
| -------------------- | ------------------------------------------------------------------ |
| `registry/loader.py` | `load_agent_registry()`, `load_system_prompt()`, `load_workflow()` |
| `registry/cache.py`  | Cache parse kết quả (invalidate khi file đổi — dev hot reload)     |
| `registry/schema.py` | Pydantic model cho frontmatter agent definition                    |


### 5.2 Agent definition (markdown + YAML frontmatter)

```yaml
# dashboard-planner.md
---
name: dashboard-planner
displayName: Dashboard Planner
tools: read_file, write_file, list_file, search_components
maxTurns: 20
maxTokens: 32000
model: null        # inherit from session
outputSchema: DashboardSpec
---
# Role, Process, Output spec...
```

### 5.3 Specialist agents (dashboard pipeline)


| Agent                 | File                   | Trách nhiệm                            | Workspace output    |
| --------------------- | ---------------------- | -------------------------------------- | ------------------- |
| **dashboard-planner** | `dashboard-planner.md` | Intent → widgets, metrics, filters     | `spec.md`           |
| **data-binder**       | `data-binder.md`       | Map metrics → queries, validate schema | `bindings.md`       |
| **layout-designer**   | `layout-designer.md`   | Grid, responsive, widget ordering      | `layout.md`         |
| **dashboard-builder** | `dashboard-builder.md` | Sinh React/TSX từ spec + layout        | `page.tsx`, widgets |
| **dashboard-critic**  | `dashboard-critic.md`  | Validate spec, a11y, grounded claims   | `review.md`         |


### 5.4 Tài nguyên prompt (đọc bởi Registry)

```
prompts/
├── system/
│   ├── system-main.md          # system prompt main loop
│   └── system-agent.md         # system prompt sub-agent loop
├── agents/                     # ⑤.3 specialist definitions (*.md + YAML)
│   ├── dashboard-planner.md
│   ├── data-binder.md
│   ├── layout-designer.md
│   ├── dashboard-builder.md
│   └── dashboard-critic.md
└── workflows/                  # phase instructions, đọc bởi Memory System ③
    ├── dashboard/
    │   ├── create-dashboard.md  # spawn sequence + acceptance criteria
    │   ├── edit-dashboard.md     # follow-up edits
    │   └── repair-dashboard.md   # critic fail → retry
    └── chat/
        └── create-chat.md        # free-form, thu thập facts
```

> Registry **chỉ nạp & validate**. Việc *chọn* workflow nào để inject thuộc Memory System; việc *chạy* workflow thuộc Orchestration.

---

## 6. ③ Memory System

> **Concern:** Trạng thái workflow của task (`memory.md` FSM) và lắp ráp **context block động** mỗi turn. Đây là "bộ nhớ làm việc" định hướng hành vi orchestrator — tách hẳn khỏi lịch sử hội thoại (Persistence) và token budget (Context).

### 6.1 Thành phần


| File                      | Vai trò                                                     |
| ------------------------- | ----------------------------------------------------------- |
| `memory/state_machine.py` | FSM `set_memory` — enforce transitions                      |
| `memory/memory_file.py`   | Đọc/ghi `memory.md` (frontmatter YAML + body)               |
| `memory/context_block.py` | Lắp block `# MEMORY` / `# USER` / `# WORKFLOW` cuối payload |


### 6.2 `memory.md` — workflow state

```yaml
---
type: dashboard            # chat | dashboard
phase: create-dashboard    # create-dashboard | edit-dashboard | repair-dashboard
---
```


| Tool         | Vai trò                                                                           |
| ------------ | --------------------------------------------------------------------------------- |
| `set_memory` | Chuyển `type` + `phase` → chọn workflow plugin (Registry nạp, Orchestration chạy) |


### 6.3 State machine (enforced transitions)

Không chỉ inject workflow — **enforce transitions** trong code:

```python
ALLOWED_TRANSITIONS = {
    ("chat", "create-chat"): [("dashboard", "create-dashboard")],
    ("dashboard", "create-dashboard"): [("dashboard", "edit-dashboard"), ("dashboard", "repair-dashboard")],
    ("dashboard", "repair-dashboard"): [("dashboard", "create-dashboard"), ("dashboard", "edit-dashboard")],
    ("dashboard", "edit-dashboard"): [("dashboard", "edit-dashboard"), ("dashboard", "repair-dashboard")],
    # terminal phases: không transition ra ngoài trừ explicit reset
}
```

- `set_memory` trả workflow plugin **mỗi lần gọi** (không chỉ khi transition) — hỗ trợ regenerate/resume.
- `Task.type` sync từ `memory.md.type` (DB field qua Persistence System).

### 6.4 Context block injection

Mỗi turn, Memory System dựng block động ở **cuối** payload (history prefix giữ ổn định để cache-friendly):

```markdown
# MEMORY
{memory.md frontmatter + body}

# USER
{custom_instructions từ user prefs}

# WORKFLOW
{workflow plugin theo type/phase}
```

> History prefix (ổn định, cache-friendly) do Context System dựng; context block (rebuild mỗi turn) do Memory System dựng. Hai phần ghép lại tạo payload cuối.

---

## 7. ④ Tool System

> **Concern:** Mọi thứ về tools — định nghĩa, phân tầng quyền, và pipeline thực thi an toàn. Tách **runtime** (registry + pipeline, trong `agents/`) khỏi **implementations** (handlers, trong `packages/tools/`).

### 7.1 Thành phần


| File                             | Vai trò                                                                  |
| -------------------------------- | ------------------------------------------------------------------------ |
| `agents/tools/registry.py`       | Single source of truth cho tool tiers                                    |
| `agents/tools/pipeline.py`       | Execution pipeline (validate → loop → cache → gate → execute → truncate) |
| `agents/tools/loop_detection.py` | Phát hiện tool call lặp                                                  |
| `agents/tools/partition.py`      | `partition_batches()` — nhóm parallel/serial                             |
| `agents/tools/read_cache.py`     | Per-run ReadCache, invalidate on write                                   |
| `packages/tools/`*               | Implementations (file, orchestration, data, catalog)                     |


### 7.2 Tool contract

```python
class ToolHandler(Protocol):
    name: str
    display_name: str
    description: str
    parameters: dict  # JSON Schema
    async def execute(self, args: dict, ctx: ToolContext) -> str: ...
```

### 7.3 Registry tiers (single source of truth)


| Set               | Tools (ví dụ)                                 | Hành vi                    |
| ----------------- | --------------------------------------------- | -------------------------- |
| `READ_ONLY_TOOLS` | `read_file`, `list_file`, `search_components` | Bypass ask-mode gate       |
| `ASK_BYPASS`      | `set_memory`, `ask_user`                      | Không cần Y/N approval     |
| `VISIBLE_TOOLS`   | Tất cả trừ internal                           | Hiện activity chip trên UI |
| `CONCURRENT_SAFE` | Read-only subset                              | Chạy parallel trong batch  |
| `MAIN_TOOLS`      | + `spawn_agent`, `ask_user`                   | Chỉ main loop              |
| `AGENT_TOOLS`     | Subset + `write_file`, `edit_file`            | Chỉ sub-agent loop         |


### 7.4 Execution pipeline (thứ tự cố định mỗi tool call)

```
validate args (JSON Schema)
  → loop detection (warn @3, block @5, sliding window)
  → read cache dedup (per-run ReadCache, invalidate on write)
  → gate (ask mode → ủy thác Gate System ⑦)
  → execute (handler)
  → truncate result (per-tool cap + history cap 100k)
  → error envelope chuẩn
```

### 7.5 Batching & loop control

- `partition_batches()` — read-only parallel (max 5), write/spawn serial.
- `with_gate()` — wrap sub-agent tools khi ask mode (delegate Gate System).
- Loop detection — warn/block repeated identical tool calls (sliding window).

### 7.6 Tool implementations (theo nhóm)


| Nhóm          | Tools                                               | Package                         |
| ------------- | --------------------------------------------------- | ------------------------------- |
| File          | `read_file`, `write_file`, `edit_file`, `list_file` | `packages/tools/file/`          |
| Orchestration | `spawn_agent`, `set_memory`, `ask_user`             | `packages/tools/orchestration/` |
| Data          | `schema_inspector`, `csv_preview`                   | `packages/tools/data/`          |
| Catalog (RAG) | `search_components`                                 | `packages/tools/catalog/`       |


---

## 8. ⑤ Context System

> **Concern:** Quản lý cửa sổ context — token accounting và 2-tier compaction. Là **nguồn truth duy nhất** cho token budget (BE engine + FE context donut dùng chung).

### 8.1 Thành phần


| File                               | Vai trò                                                 |
| ---------------------------------- | ------------------------------------------------------- |
| `core/llm/budget.py`               | Shared token constants (FE + BE)                        |
| `agents/context/history.py`        | Dựng history prefix ổn định (cache-friendly)            |
| `agents/context/compaction.py`     | 2-tier compaction                                       |
| `agents/context/thinking_codec.py` | Encode/decode extended thinking                         |
| `agents/context/accounting.py`     | Per-message `prompt_tokens`, tokens_per_char calibrated |


### 8.2 Shared budget (single source)

```python
LLM_CONTEXT_WINDOW = 128_000
LLM_INPUT_BUDGET_TOKENS = ...       # reserved for output + thinking + overhead
MICRO_COMPACT_FRACTION = 0.6        # tier 1
SUMMARY_COMPACT_FRACTION = 0.8      # tier 2
COMPACT_THRESHOLD_PCT = 50          # manual compact button eligibility
```

> Export sang TS qua OpenAPI hoặc shared JSON artifact → FE `GET /v1/llm/budget`.

### 8.3 Two-tier compaction


| Tier            | Trigger          | Hành động                                            |
| --------------- | ---------------- | ---------------------------------------------------- |
| Microcompact    | 60% input budget | Xóa tool results read-only cũ                        |
| Summary compact | 80% input budget | LLM tóm tắt phần history cũ → message role `compact` |


### 8.4 Token accounting

- `prompt_tokens` lưu per message (DB) — phục vụ FE context donut.
- Provider-calibrated `tokens_per_char` (không chỉ ước lượng thô).
- `KEEP_TOKENS` char budget derived từ `LLM_INPUT_BUDGET_TOKENS`.

### 8.5 Phân công dựng payload

```
[ history prefix (ổn định) ]  ← Context System
[ # MEMORY / # USER / # WORKFLOW ]  ← Memory System ③
= payload gửi LLM System ⑥
```

---

## 9. ⑥ LLM System

> **Concern:** Trừu tượng hóa nhà cung cấp LLM. Interface mỏng, không framework — đổi provider không chạm Orchestration.

### 9.1 Thành phần


| File                              | Vai trò                                  |
| --------------------------------- | ---------------------------------------- |
| `core/llm/client.py`              | `LLMClient` interface (`chat`, `stream`) |
| `core/llm/providers/openai.py`    | Adapter OpenAI                           |
| `core/llm/providers/anthropic.py` | Adapter Anthropic                        |
| `core/llm/providers/ollama.py`    | Adapter Ollama (dev default)             |


### 9.2 Interface

```python
class LLMClient(Protocol):
    async def chat(self, messages, tools, **opts) -> LLMResponse: ...
    async def stream(self, messages, tools, **opts) -> AsyncIterator[LLMDelta]: ...
```


| Concern        | Hành vi                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------- |
| Streaming      | `httpx` SSE/chunk → `LLMDelta` (text / thinking / tool_call)                              |
| Model override | Per-session hoặc per-agent (frontmatter `model`)                                          |
| Failure modes  | Trả tín hiệu chuẩn (`max_tokens`, `empty`, `thinking_only`) → Orchestration recovery §4.5 |


> LLM System chỉ *phát hiện* failure mode và báo cáo; *quyết định* recovery thuộc Orchestration.

---

## 10. ⑦ Gate System (Human-in-the-loop)

> **Concern:** Cơ chế chặn/duyệt qua Redis. Tách hẳn khỏi Tool System: Tool gọi `with_gate()`, còn vòng đời gate (init/register/resolve/cleanup) thuộc subsystem này.

### 10.1 Thành phần


| File                        | Vai trò                                 |
| --------------------------- | --------------------------------------- |
| `agents/gates/tool_gate.py` | Gate duyệt tool (ask mode)              |
| `agents/gates/ask_gate.py`  | Gate `ask_user` form                    |
| `agents/gates/registry.py`  | `init/register/resolve/unregister`, CAS |


### 10.2 Loại gate


| Gate           | Trigger                    | UI                                    |
| -------------- | -------------------------- | ------------------------------------- |
| Tool gate      | Ask mode + non-bypass tool | ActionCard Y/N                        |
| Ask gate       | `ask_user` tool            | ActionCard form input                 |
| Sub-agent gate | Ask mode + agent tool      | ActionCard trong agent activity block |


### 10.3 Flow & chi tiết

```
init_gate (TRƯỚC khi emit SSE) → emit pending qua Streaming ⑨
  → register_gate (poll Redis) → user resolve qua API → resume execution
```


| Pattern                         | Chi tiết                                                |
| ------------------------------- | ------------------------------------------------------- |
| `init_gate` trước SSE emit      | Tránh race approve                                      |
| Namespace riêng                 | `gate:` (tool) vs `ask:`                                |
| CAS `SET_IF_PENDING`            | Chống double-approve                                    |
| Poll jitter + fail-safe unblock | Tránh hung stream khi Redis flaky                       |
| Gate feedback                   | Approve/reject message inject vào `tool_result` cho LLM |
| `unregister_all_gates`          | Cleanup khi stream end / task delete                    |


---

## 11. ⑧ Artifact System

> **Concern:** Vòng đời file workspace — staging trong stream, flush an toàn, tránh phantom file khi cancel. Sở hữu model `File` thống nhất.

### 11.1 Thành phần


| File                               | Vai trò                                     |
| ---------------------------------- | ------------------------------------------- |
| `agents/artifacts/buffer.py`       | `ArtifactBuffer` (in-memory Map per stream) |
| `agents/artifacts/file_service.py` | CRUD `File`, overwrite-by-name, R2/S3 path  |


### 11.2 Artifact buffer

Stage file writes trong shared `ArtifactBuffer` suốt stream:

- Flush khi `stream_done` hoặc interrupt có save.
- Tránh phantom files khi user cancel giữa chừng.
- Workspace files: `spec.md`, `bindings.md`, `layout.md`, `page.tsx`, `memory.md`.

### 11.3 File model (unified)

Một model `File`, không dùng `Artifact` riêng:


| Field / rule | Giá trị                                                                  |
| ------------ | ------------------------------------------------------------------------ |
| `source`     | `upload` | `workspace`                                                   |
| `kind`       | `text` | `image` | `binary`                                              |
| Overwrite    | App-level overwrite-by-name trong workspace (không DB unique constraint) |
| Staging      | `write_file`/`edit_file` → `ArtifactBuffer` → flush on done/interrupt    |
| Storage path | `attachments/{task_id}/` — validate task ownership                       |
| Branch scope | `get_artifacts` chỉ files trên active branch path                        |


---

## 12. ⑨ Streaming System

> **Concern:** Vận chuyển sự kiện ra client. Sở hữu **SSE event schema** (single source), EventBus, và toàn bộ stream lock & resilience guards.

### 12.1 Thành phần


| File                            | Vai trò                             |
| ------------------------------- | ----------------------------------- |
| `agents/streaming/event_bus.py` | EventBus nội bộ → SSE serializer    |
| `agents/streaming/events.py`    | SSE event type definitions          |
| `agents/streaming/lock.py`      | Redis stream lock, heartbeat        |
| `agents/streaming/guards.py`    | Dedup, disconnect, safety-net abort |


### 12.2 SSE event schema (single source)

```python
# Main orchestrator
main_text      # streaming text delta
main_think     # extended thinking (optional)
main_tool      # tool call started
main_result    # tool result
main_ask       # ask_user form
# Sub-agent
agent_start    # {agentName, displayName}
agent_text     # streaming text trong agent block
agent_think    # thinking trong agent block
agent_tool     # tool call trong agent
agent_result   # tool result trong agent
agent_done     # {status, summary}
# Lifecycle
file_artifact  # workspace file created/updated
task_meta      # title update
heartbeat      # keep-alive (KHÔNG dùng "ping")
stream_done
stream_error
```

### 12.3 Stream lock & resilience guards


| Guard                      | Hành vi                                                               |
| -------------------------- | --------------------------------------------------------------------- |
| `acquire_stream_lock`      | 409 nếu task đang chạy                                                |
| Pending user message reuse | Tránh duplicate LLM run khi client retry                              |
| 5s dedup                   | Cùng content trong 5s → short-circuit                                 |
| Lock refresh               | Heartbeat 5s refresh Redis TTL                                        |
| Lock lost                  | Abort ghost run nếu mất lock                                          |
| Client disconnect          | **Không abort** LLM — preserve work                                   |
| Gate + client gone         | Abort nếu `pending_user_input` + client disconnect                    |
| Safety net                 | 10 phút auto-abort non-interactive run (orphan lock)                  |
| Stop handshake             | `POST /stop` → abort + `cleanup_done` + return `partial_message_id`   |
| Partial save               | Lưu assistant partial + flush artifact buffer kể cả khi không có text |


### 12.4 Rate limiting (Redis buckets)


| Bucket             | Limit       | Trigger                  |
| ------------------ | ----------- | ------------------------ |
| `task_stream`      | 100/hr/user | `POST /stream`           |
| `task_create`      | 30/hr/user  | `POST /tasks`            |
| `upload`           | 30/hr/user  | `POST /upload`           |
| `dashboard_create` | 20/day/user | `set_memory` → dashboard |
| `global`           | 1000/min    | Tất cả API               |


---

## 13. ⑩ Persistence System

> **Concern:** Lưu trữ bền — message tree, task, file, agent run. Sở hữu schema DB & branching logic.

### 13.1 Database models


| Model      | Vai trò                                                                       |
| ---------- | ----------------------------------------------------------------------------- |
| `Task`     | Conversation container (title, user_id, status, `type`)                       |
| `Message`  | Tree node: user / assistant / tool / **compact** (`parent_id` links)          |
| `File`     | Workspace + upload files (spec.md, page.tsx, …) — model trong Artifact System |
| `AgentRun` | Sub-agent activities JSON + status per spawn call                             |


Message tree: `parent_id` links — branching (regenerate/edit tạo nhánh mới, phase 2).

### 13.2 Schemas cốt lõi (Pydantic, trong `core/schemas/`)


| Schema            | Mô tả                                  |
| ----------------- | -------------------------------------- |
| `DashboardSpec`   | Widgets, metrics, filters (từ planner) |
| `DataBindingPlan` | Query/API per widget                   |
| `LayoutSpec`      | Grid positions, responsive rules       |
| `GeneratedPage`   | File paths, entry component            |
| `ReviewResult`    | Critic pass/fail + fixes               |
| `StreamEvent`     | Union type cho SSE events              |
| `AgentActivity`   | Timeline entry cho UI reload           |


---

## 14. ⑪ Observability System

> **Concern:** Nhìn xuyên runtime — logs, traces, eval. Cross-cutting nhưng tách thành subsystem để không rải rác.


| Layer   | Công nghệ                             | Mục đích                                         |
| ------- | ------------------------------------- | ------------------------------------------------ |
| Logging | **structlog**                         | Structured logs, correlation ID per task/run     |
| Tracing | **OpenTelemetry**                     | Span theo từng step main/sub loop, tool call     |
| Eval    | Custom golden sets (`packages/eval/`) | Dashboard spec validity, render success, CI gate |


---

## 15. Cấu trúc thư mục (mirror theo subsystem)

Cây thư mục phản chiếu trực tiếp catalog §3.2 — mỗi subsystem một thư mục, dễ định vị code theo concern.

```
dashzen/
├── plan/
│   ├── 01-project-structure-and-techstack.md
│   ├── 02-ui-features-chat-agent.md
│   └── ...
│
├── apps/
│   ├── api/                              # FastAPI — REST + SSE (adapter layer)
│   │   ├── src/api/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── tasks.py              # CRUD task
│   │   │   │   ├── stream.py             # POST /tasks/{id}/stream — SSE
│   │   │   │   ├── gates.py              # resolve tool/ask gate → Gate System ⑦
│   │   │   │   └── upload.py
│   │   │   ├── deps.py
│   │   │   └── middleware/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── studio/                           # Next.js — chat + canvas (xem plan 02)
│       ├── app/
│       ├── modules/task/
│       ├── lib/
│       └── package.json
│
├── packages/
│   ├── core/                             # ⑥ LLM + schemas + config (zero agent logic)
│   │   ├── src/core/
│   │   │   ├── config.py
│   │   │   ├── llm/                       # ⑥ LLM System
│   │   │   │   ├── client.py
│   │   │   │   ├── budget.py              # ⑤ shared token constants (FE+BE)
│   │   │   │   └── providers/             # openai, anthropic, ollama
│   │   │   ├── schemas/                   # DashboardSpec, SSE events, ...
│   │   │   └── exceptions.py
│   │   └── pyproject.toml
│   │
│   ├── agents/                           # Agent Runtime — compose các subsystem
│   │   ├── src/agents/
│   │   │   ├── orchestration/            # ① main_loop, agent_loop, spawn, workflow, recovery, runtime
│   │   │   ├── registry/                 # ② loader, cache, schema
│   │   │   ├── memory/                    # ③ state_machine, memory_file, context_block
│   │   │   ├── tools/                     # ④ registry, pipeline, loop_detection, partition, read_cache
│   │   │   ├── context/                   # ⑤ history, compaction, thinking_codec, accounting
│   │   │   ├── gates/                     # ⑦ tool_gate, ask_gate, registry
│   │   │   ├── artifacts/                 # ⑧ buffer, file_service
│   │   │   └── streaming/                 # ⑨ event_bus, events, lock, guards
│   │   │
│   │   ├── prompts/                       # ② tài nguyên prompt-as-config
│   │   │   ├── system/                    # system-main.md, system-agent.md
│   │   │   ├── agents/                    # *.md + YAML frontmatter
│   │   │   └── workflows/                 # dashboard/, chat/
│   │   │
│   │   └── pyproject.toml
│   │
│   ├── tools/                            # ④ tool implementations (handlers)
│   │   ├── src/tools/
│   │   │   ├── file/                      # read, write, edit, list
│   │   │   ├── orchestration/             # spawn_agent, set_memory, ask_user
│   │   │   ├── data/                      # schema_inspector, csv_preview
│   │   │   └── catalog/                   # search_components (RAG)
│   │   └── pyproject.toml
│   │
│   ├── db/                               # ⑩ Persistence System
│   │   ├── src/db/models/                 # task, message, file, agent_run
│   │   └── pyproject.toml
│   │
│   ├── rag/                              # vector store cho ④ catalog tools
│   └── eval/                             # ⑪ golden sets
│
├── templates/                            # Widget templates cho CodeGen
├── generated/                            # Output sandbox (gitignored)
├── infra/
│   ├── compose/docker-compose.yml         # postgres, redis, qdrant, minio
│   └── docker/
│
├── pyproject.toml
├── .env.example
└── README.md
```

### 15.1 Dependency direction

```
api      → agents, db, core
agents   → tools, db, core          (orchestration wiring các subsystem nội bộ)
tools    → core
studio   → (HTTP/SSE only, no Python import)
```

Nội bộ `agents/` tuân theo hướng phụ thuộc §3.2: `orchestration` phụ thuộc các subsystem khác; không subsystem nào import ngược lên `orchestration`.

---

## 16. API surface

> Tầng `apps/api` là **adapter mỏng**: dịch HTTP ↔ Agent Runtime. Không chứa business logic agent.

### 16.1 REST (CRUD)


| Method   | Endpoint                    | Subsystem | Mô tả                             |
| -------- | --------------------------- | --------- | --------------------------------- |
| `POST`   | `/v1/auth/login`            | —         | JWT + httpOnly cookie             |
| `POST`   | `/v1/auth/refresh`          | —         | Silent refresh                    |
| `POST`   | `/v1/tasks`                 | ⑩         | Tạo task + seed `memory.md`       |
| `GET`    | `/v1/tasks`                 | ⑩         | List tasks (recents)              |
| `GET`    | `/v1/tasks/{id}`            | ⑩         | Task detail                       |
| `PATCH`  | `/v1/tasks/{id}`            | ⑩         | Rename                            |
| `DELETE` | `/v1/tasks/{id}`            | ⑩         | Delete task                       |
| `GET`    | `/v1/tasks/{id}/messages`   | ⑩         | Message tree + agent activities   |
| `GET`    | `/v1/tasks/{id}/artifacts`  | ⑧         | Workspace files (branch-scoped)   |
| `POST`   | `/v1/tasks/{id}/gates/tool` | ⑦         | Approve/reject tool gate          |
| `POST`   | `/v1/tasks/{id}/gates/ask`  | ⑦         | Submit ask_user answer            |
| `POST`   | `/v1/tasks/{id}/compact`    | ⑤         | Manual context compaction         |
| `GET`    | `/v1/llm/budget`            | ⑤         | Shared token constants (FE donut) |


### 16.2 Streaming (SSE)


| Method | Endpoint                | Subsystem | Mô tả                                  |
| ------ | ----------------------- | --------- | -------------------------------------- |
| `POST` | `/v1/tasks/{id}/stream` | ① ⑨       | Main chat stream                       |
| `POST` | `/v1/tasks/{id}/stop`   | ⑨         | Abort + cleanup (stop handshake §12.3) |
| `POST` | `/v1/tasks/{id}/upload` | ⑧         | Upload attachment                      |


Chi tiết SSE schema & guards: §12. Auth (JWT MVP → better-auth phase 2): xem plan 02 / 06.

---

## 17. Quyết định đã chốt


| Quyết định       | Lựa chọn                                        | Lý do                                   |
| ---------------- | ----------------------------------------------- | --------------------------------------- |
| Generated page   | **Runtime JSON spec** MVP + export file phase 2 | Preview nhanh trong canvas              |
| Auth MVP         | Single-user + JWT, interface sẵn multi-tenant   | Giảm scope P0                           |
| Data sources MVP | Mock data + CSV upload                          | SQL connector phase 3                   |
| LLM dev default  | **Ollama local** + adapter cloud                | Zero cost dev                           |
| ReAct per agent  | **Multi-turn tool loop** (max 20 turns/agent)   | Cần cho grounded generation             |
| Streaming        | **SSE** (không WebSocket)                       | Đơn giản, proven                        |
| Orchestration    | **Main spawn + workflow plugins**               | Chat linh hoạt, dashboard deterministic |
| Chat terminology | **Task**                                        | Đơn giản UX                             |
| Tổ chức code     | **System-of-systems** (1 subsystem = 1 thư mục) | Ranh giới concern rõ, thay thế độc lập  |


---

## 18. Giai đoạn triển khai (theo subsystem)


| Phase  | Mục tiêu                | Subsystem chính   | Deliverable                                              |
| ------ | ----------------------- | ----------------- | -------------------------------------------------------- |
| **P0** | Nền tảng                | ⑥ ⑩ + infra       | `core/llm`, `db` models, docker compose                  |
| **P1** | Loop tối thiểu + stream | ① ⑨ + 1 agent (②) | Chat stream, `dashboard-planner` → mock spec             |
| **P2** | Full pipeline           | ① ② ③             | 5 sub-agents + workflow plugins + critic repair          |
| **P3** | Production patterns     | ④ ⑤ ⑦ ⑧           | Tool pipeline, gates, 2-tier compaction, artifact buffer |
| **P4** | Studio UI đầy đủ        | (FE, plan 02)     | TaskContext reducer, canvas preview, Ask/Auto            |
| **P5** | RAG + connectors + eval | ④ (catalog) ⑪     | Component catalog, CSV upload, golden tests              |


---

## 19. Phạm vi self-built vs thư viện hạ tầng


| Tự build (logic DashZen)        | Subsystem | Dùng thư viện hạ tầng (OK)                   |
| ------------------------------- | --------- | -------------------------------------------- |
| Dual-loop + spawn + workflow    | ①         | FastAPI, httpx, SQLAlchemy                   |
| Markdown agent registry         | ②         | Pydantic, structlog                          |
| `memory.md` FSM + context block | ③         | PostgreSQL, Redis                            |
| Tool registry tiers + pipeline  | ④         | MinIO/S3                                     |
| Two-tier compaction + budget    | ⑤         | —                                            |
| Provider adapter mỏng           | ⑥         | —                                            |
| Redis gates + CAS               | ⑦         | —                                            |
| Artifact buffer + file model    | ⑧         | —                                            |
| EventBus + stream guards        | ⑨         | —                                            |
| **Không dùng**                  | —         | LangGraph, LangChain, CrewAI, MCP, Mem0, Zep |


---

## 20. Checklist gaps — cần ghi trong plan 03–06


| #   | Gap                                               | Subsystem | Target plan                | Priority |
| --- | ------------------------------------------------- | --------- | -------------------------- | -------- |
| 1   | `main_loop` iteration detail + recovery           | ①         | `03-agent-runtime`         | P0       |
| 2   | Gate payloads + CAS + feedback                    | ⑦         | `03` + `06`                | P0       |
| 3   | SSE full schema + stream guards                   | ⑨         | `06-api-contracts`         | P0       |
| 4   | `set_memory` FSM transitions                      | ③         | `03`                       | P1       |
| 5   | Sub-agent output parse + activities cap           | ①         | `03`                       | P1       |
| 6   | Tool pipeline (validate→loop→cache→gate→truncate) | ④         | `03`                       | P1       |
| 7   | Title generation algorithm                        | ①         | `03`                       | P1       |
| 8   | Message tree + branch API                         | ⑩         | `06`                       | P1       |
| 9   | File model + upload security                      | ⑧         | `06`                       | P1       |
| 10  | Rate limit matrix                                 | ⑨         | `06`                       | P1       |
| 11  | `normalise_messages` + reload UI                  | (FE)      | `02` (đã có §15–17)        | P1       |
| 12  | `DashboardSpec` Pydantic full                     | ⑩         | `04-dashboard-spec-schema` | P1       |
| 13  | MVP scope chốt                                    | —         | `05-mvp-scope`             | P0       |
| 14  | Eval golden sets + CI migration                   | ⑪         | `05` + infra               | P2       |
| 15  | OpenTelemetry wiring                              | ⑪         | infra                      | P3       |


**Đã cover trong plan 01/02:** decomposition subsystem, dual-loop, tool tiers, compaction 2-tier, gates (overview), SSE events core, TaskContext pattern, Ask/Auto, artifact buffer.

**Chưa có file plan:** `03`, `04`, `05`, `06` — blocker trước khi code P1.

---

## 21. Bước tiếp theo trong `plan/`

1. `03-agent-runtime-and-memory.md` — chi tiết Orchestration ①, Memory ③, Tool pipeline ④, Gate ⑦, recovery, title
2. `04-dashboard-spec-schema.md` — Pydantic models + JSON Schema export (Persistence ⑩)
3. `05-mvp-scope.md` — Scope P0–P1, promote/demote từ gap audit
4. `06-api-contracts.md` — OpenAPI + SSE schema ⑨ + rate limits + branching API

