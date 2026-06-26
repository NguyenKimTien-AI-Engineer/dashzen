# Nghiên cứu Hermes Agent — NousResearch

> **Nguồn:** https://github.com/NousResearch/hermes-agent.git  
> **Ngày nghiên cứu:** 23/06/2026  
> **Phiên bản mới nhất:** v0.17.0 (v2026.6.19)  
> **Stars:** 200k | **Forks:** 35.7k  
> **Language:** Python 82.6%, TypeScript 13.4%, Shell 0.5%

---

## 1. Tổng quan hệ thống

Hermes Agent là **"The self-improving AI agent"** — agent có khả năng tự học và cải thiện theo thời gian. Đây không phải là một chat bot đơn giản mà là một **agent runtime hoàn chỉnh** với learning loop tích hợp.

### 1.1 Định nghĩa cốt lõi

> "The only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions."

### 1.2 Phạm vi triển khai

- **Chạy được ở mọi nơi:** $5 VPS, GPU cluster, serverless infrastructure
- **Multi-platform:** CLI, Telegram, Discord, Slack, WhatsApp, Signal, Email
- **Multi-provider:** OpenAI, Anthropic, Ollama, 200+ models qua OpenRouter

---

## 2. Kiến trúc hệ thống

### 2.1 Entry Points (Điểm vào)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Entry Points                                  │
│  CLI (cli.py)    Gateway (gateway/run.py)    ACP (acp_adapter/)     │
│  Batch Runner    API Server                  Python Library          │
└──────────┬──────────────┬───────────────────────┬───────────────────┘
           ▼              ▼                       ▼
           AIAgent (run_agent.py) — Core conversation loop
```

**Đặc điểm:** Một `AIAgent` class phục vụ tất cả entry points — CLI, gateway, ACP, batch, API server. Platform differences chỉ ở entry point layer.

### 2.2 Core Agent Loop (AIAgent)

File: `run_agent.py` (large file — đây là engine chính)

Subsystems được compose trong AIAgent:

| Subsystem | File | Vai trò |
|-----------|------|---------|
| Prompt Builder | `agent/prompt_builder.py` | System prompt assembly |
| Provider Resolution | `hermes_cli/runtime_provider.py` | Resolve (provider, model) → credentials |
| Tool Dispatch | `model_tools.py` | Tool discovery, dispatch |
| Compression | `agent/context_compressor.py` | Lossy summarization |
| Memory | `agent/memory_manager.py` | Memory orchestration |
| Session Storage | `hermes_state.py` | SQLite + FTS5 |

### 2.3 Tool System

- **70+ tools** đăng ký qua central registry (`tools/registry.py`)
- **28 toolsets** — tool groupings and platform presets
- **Self-registration:** Tool file tự đăng ký khi import — không có manual import list
- **6 terminal backends:** local, Docker, SSH, Daytona, Modal, Singularity
- **5 browser backends**
- **20 platform adapters** trong gateway

Tool Categories:
```
tools/
├── terminal_tool.py      # Terminal orchestration
├── file_tools.py         # read_file, write_file, patch, search_files
├── web_tools.py          # web_search, web_extract
├── browser_tool.py       # 10 browser automation tools
├── code_execution_tool.py # execute_code sandbox
├── delegate_tool.py      # Subagent delegation
├── mcp_tool.py           # MCP client
└── environments/         # Terminal backends
```

### 2.4 Prompt System (3 tầng)

```
stable     → identity/tool guidance/skills
context    → context files (project context)
volatile   → memory/profile/timestamp blocks (cuối payload)
```

**Nguyên tắc:** System prompt ổn định giữa conversation (cache-friendly). Context block động ở cuối payload.

### 2.5 Context Compression

**2-tier compaction** (giống DashZen plan):
- **Tier 1:** Xóa old tool results (microcompact)
- **Tier 2:** LLM summarizes middle turns

### 2.6 Session Storage

- **SQLite + FTS5** — local, không cần external DB
- Lineage tracking (parent/child across compressions)
- Per-platform isolation

### 2.7 Gateway System

20 platform adapters, message dispatch qua `GatewayRunner`:
```
Platform event → Adapter.on_message() → MessageEvent
  → GatewayRunner._handle_message()
    → authorize user
    → resolve session key
    → create AIAgent with session history
    → AIAgent.run_conversation()
    → deliver response back through adapter
```

### 2.8 Plugin System

3 discovery sources:
1. `~/.hermes/plugins/` (user plugins)
2. `.hermes/plugins/` (project plugins)
3. pip entry points

2 single-select plugin types:
- Memory providers (`plugins/memory/`)
- Context engines (`plugins/context_engine/`)

### 2.9 Skills System (Learning Loop)

**Đây là điểm độc đáo nhất của Hermes:**
- **Autonomous skill creation** sau complex tasks
- **Skills self-improve** during use
- **FTS5 session search** với LLM summarization cho cross-session recall
- **Honcho dialectic user modeling** — builds user model across sessions
- Tương thích với [agentskills.io](https://agentskills.io) open standard

### 2.10 Cron System

First-class agent tasks (không phải shell tasks):
- Jobs lưu trong JSON
- Natural language schedule
- Deliver to any platform
- Attach skills and scripts

### 2.11 Subagent Delegation

```python
# delegate_tool.py — Spawn isolated subagents for parallel workstreams
# Write Python scripts that call tools via RPC
# Collapse multi-step pipelines into zero-context-cost turns
```

---

## 3. Data Flow

### 3.1 CLI Session

```
User input
  → HermesCLI.process_input()
  → AIAgent.run_conversation()
    → prompt_builder.build_system_prompt()
    → runtime_provider.resolve_runtime_provider()
    → API call (chat_completions / codex_responses / anthropic_messages)
    → tool_calls? → model_tools.handle_function_call() → loop
    → final response → display → save to SessionDB
```

### 3.2 API Modes

3 modes cho different provider backends:
1. `chat_completions` — OpenAI-compatible
2. `codex_responses` — Codex-specific
3. `anthropic_messages` — Anthropic Messages API

### 3.3 File Dependency Chain

```
tools/registry.py (no deps)
    ↑
tools/*.py (self-register at import)
    ↑
model_tools.py (imports registry + triggers discovery)
    ↑
run_agent.py, cli.py, batch_runner.py
```

---

## 4. Design Principles

| Nguyên tắc | Ý nghĩa |
|-----------|---------|
| **Prompt stability** | System prompt không đổi giữa conversation |
| **Observable execution** | Mọi tool call visible qua callbacks |
| **Interruptible** | API calls và tool execution có thể cancel mid-flight |
| **Platform-agnostic core** | AIAgent phục vụ mọi entry point |
| **Loose coupling** | Optional subsystems dùng registry patterns, check_fn gating |
| **Profile isolation** | Mỗi profile có riêng HERMES_HOME, config, memory, sessions |

---

## 5. Cấu trúc thư mục chính

```
hermes-agent/
├── run_agent.py              # AIAgent — core loop
├── cli.py                    # HermesCLI — terminal UI
├── model_tools.py            # Tool discovery, schema, dispatch
├── toolsets.py               # Tool groupings + platform presets
├── hermes_state.py           # SQLite session DB with FTS5
├── agent/                    # Agent internals
│   ├── prompt_builder.py     # System prompt assembly
│   ├── context_engine.py     # ContextEngine ABC (pluggable)
│   ├── context_compressor.py # Lossy summarization
│   ├── memory_manager.py     # Memory orchestration
│   └── trajectory.py         # Training data helpers
├── tools/                    # 70+ tool implementations
├── gateway/                  # 20 platform adapters
├── acp_adapter/              # IDE integration (VS Code, Zed, JetBrains)
├── cron/                     # Scheduler (jobs.py, scheduler.py)
├── plugins/memory/           # Memory provider plugins
├── skills/                   # Bundled skills
└── optional-skills/          # Optional installable skills
```

---

## 6. Công nghệ và Dependencies

| Layer | Công nghệ |
|-------|-----------|
| Language | Python 3.11 |
| Package manager | uv |
| Session storage | SQLite + FTS5 |
| Terminal UI | Textual (TUI) |
| Platform adapters | 20 adapters (Telegram, Discord, ...) |
| MCP | Model Context Protocol client |
| Memory | Honcho + agent-curated + FTS5 |
| Deployment | Docker, Nix, Modal, Daytona |

---

## 7. Unique Features (Phân biệt với các agent khác)

### 7.1 Self-Learning Loop

```
Complex task hoàn thành
  → Agent tự tạo Skill mới (procedural memory)
  → Skill tự cải thiện khi dùng
  → FTS5 search qua past conversations
  → Honcho user model → agent hiểu user hơn theo thời gian
```

### 7.2 Trajectory Generation

- **Batch trajectory generation** cho training data
- **ShareGPT format** — dùng để train next generation models
- **Trajectory compression** — compress cho fine-tuning

### 7.3 Serverless-first

- Daytona và Modal: environment hibernates khi idle, wakes on demand
- Cost ~$0 khi không active

### 7.4 ACP Integration

Expose Hermes as editor-native agent qua stdio/JSON-RPC cho VS Code, Zed, JetBrains — biến agent thành IDE plugin.

---

## 8. Bài học quan trọng cho DashZen

| Lesson | Áp dụng vào DashZen |
|--------|---------------------|
| **Platform-agnostic core** | `AIAgent` → `AgentRuntime` không phụ thuộc FastAPI route |
| **Tool self-registration** | Tool files tự đăng ký — không cần maintain import list |
| **Prompt stability** | History prefix ổn định → cache-friendly (đã có trong plan) |
| **Skills as procedural memory** | DashZen có thể học pattern dashboard từ user qua thời gian |
| **Observable execution** | Mọi tool call emit SSE event → UI thấy được |
| **Interruptible** | Cancel mid-flight không corrupt state |
| **Profile isolation** | Multi-tenant isolation từ kiến trúc |

---

## 9. Những gì Hermes KHÔNG có (mà DashZen cần)

- **Domain-specific orchestration:** Hermes là general-purpose; DashZen cần workflow deterministic cho dashboard pipeline
- **Structured artifact output:** DashZen cần `DashboardSpec` Pydantic schema, không chỉ file text
- **Frontend integration:** Hermes là CLI-first; DashZen cần SSE streaming tích hợp với Next.js
- **Multi-user production:** Hermes profile isolation là single-user per profile; DashZen cần multi-tenant DB-backed
- **Workflow state machine:** FSM enforced transitions (Dashboard/Edit/Repair) — Hermes không có khái niệm này
