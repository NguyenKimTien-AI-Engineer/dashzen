# So sánh & Tổng hợp: Hermes vs LeadZen vs DashZen

> **Mục đích:** Đối chiếu 2 hệ thống agent hiện đại → rút ra kiến trúc phù hợp cho DashZen  
> **Ngày:** 23/06/2026

---

## 1. Bảng so sánh tổng quan

| Chiều | Hermes Agent | LeadZen | DashZen (current plan) |
|-------|-------------|---------|----------------------|
| **Mục đích** | General-purpose self-improving agent | Landing page AI builder | Dashboard AI builder |
| **Language** | Python (82.6%) + TypeScript | TypeScript (Node.js) | Python + TypeScript |
| **Storage** | SQLite (local) | PostgreSQL (Prisma) | PostgreSQL (SQLAlchemy) |
| **Streaming** | SSE / WebSocket | SSE (async generator → tRPC) | SSE (FastAPI) |
| **Agent loop** | `AIAgent.run_conversation()` | `mainRun()` async generator | `run_task()` + `main_loop.py` |
| **Sub-agent** | `delegate_tool.py` | `agentRun()` + `spawn-agent.ts` | `agent_loop.py` + `spawn.py` |
| **Memory** | `MEMORY.md` + Skills + FTS5 | `memory.md` FSM + workflow injection | `memory.md` FSM + context block |
| **Tool gates** | Command approval patterns | Redis gates (CAS + poll) | Redis gates (CAS + poll) |
| **Context compaction** | 2-tier (microcompact + summary) | 2-tier (identical pattern) | 2-tier (copied from LeadZen) |
| **Tool registry** | Self-registering at import | Explicit tool sets (MAIN/AGENT) | Registry tiers (same concept) |
| **Agent definitions** | No formal markdown registry | `.md` + YAML frontmatter | `.md` + YAML frontmatter |
| **Workflow** | Skills system (flexible) | FSM phases + workflow files | FSM phases + workflow plugins |
| **Multi-platform** | 20 platform adapters | Web only (Next.js) | Web only (Next.js) |
| **Observability** | Basic logging | Structured logger (pino) | OpenTelemetry + structlog |

---

## 2. Điểm tương đồng cốt lõi

### 2.1 Shared Patterns (cả Hermes và LeadZen)

Cả hai hệ thống đều dùng:

1. **Dual-loop architecture** — Main orchestrator loop + Sub-agent isolated loop
2. **Tool call loop** — `for iteration in range(MAX)` với iteration guard
3. **Context compaction** — 2-tier: cheap (microcompact) → expensive (LLM summary)
4. **Prompt stability** — History prefix ổn định, context block động ở cuối
5. **Observable execution** — Mọi tool call emit event tới UI
6. **Interruptible** — AbortSignal propagation qua toàn stack
7. **Artifact buffer** — Stage writes → flush on done (không phantom files)
8. **Recovery paths** — max_tokens / empty / thinking-only với independent budgets

### 2.2 Pattern Convergence (Battle-tested)

Cả hai repo đều arrive tại **cùng solutions** cho cùng problems:

| Problem | Solution (Both) |
|---------|-----------------|
| Context overflow | 2-tier compaction (60%/80% thresholds) |
| Double-approve | Lua CAS SET_IF_PENDING |
| Race condition gate | initGate BEFORE emit SSE |
| Phantom files | ArtifactBuffer stage → flush |
| Loop detection | Sliding window + warn/block |
| Max tokens | inject "continue" + retry |
| Empty response | inject recovery + retry |
| Sub-agent timeout | Wall-clock timer (18 min) |
| Title generation | Concurrent, cheap model, force at turn N |

**Kết luận:** Đây là **battle-tested patterns** — DashZen đã chọn đúng hướng.

---

## 3. Điểm khác biệt quan trọng

### 3.1 Hermes: General-purpose vs DashZen: Domain-specific

| Hermes | DashZen |
|--------|---------|
| Flexible skills system | 5 specialist agents (fixed pipeline) |
| No formal output schema | Pydantic `DashboardSpec` validated output |
| SQLite (local single-user) | PostgreSQL (multi-user, cloud) |
| 70+ tools | ~10 domain tools (file, data, catalog) |
| No workflow determinism | Deterministic dashboard workflow |

**Implication:** DashZen có thể học **Hermes patterns** nhưng không adopt architecture vì scope khác hoàn toàn.

### 3.2 LeadZen: TypeScript vs DashZen: Python

| LeadZen (TS) | DashZen (Python) |
|-------------|-----------------|
| `async function*` (async generator) | `async def` với `yield` (Python async generator) |
| `prisma.message.create()` | `session.add(message)` (SQLAlchemy) |
| `redis.eval(LUA_SCRIPT)` | `redis.eval(LUA_SCRIPT)` (aioredis) |
| `AbortController` / `AbortSignal` | `asyncio.Event` + `asyncio.CancelledError` |
| `Map<string, string>` | `dict[str, str]` |
| tRPC router | FastAPI router |

**Implication:** Business logic của LeadZen **translate 1:1** sang Python.

---

## 4. Gap Analysis: Plan hiện tại vs Reference systems

### 4.1 Những gì Plan hiện tại đã đúng

Plan DashZen (từ `01-project-structure-and-techstack.md`) đã capture được:

- ✅ Dual-loop architecture (main + sub-agent)
- ✅ Spawn contract (DONE/WAIT/FAIL + Summary ≤ 4KB)
- ✅ 2-tier compaction (60%/80% thresholds)
- ✅ Artifact buffer (stage → flush)
- ✅ Gate system (Redis CAS + poll jitter)
- ✅ Tool registry tiers (READ_ONLY, ASK_BYPASS, VISIBLE, CONCURRENT_SAFE, MAIN, AGENT)
- ✅ FSM memory.md transitions
- ✅ SSE event schema
- ✅ Stream lock (acquire → heartbeat → release)
- ✅ Rate limiting (Redis buckets)
- ✅ `initGate` trước emit SSE
- ✅ `unregisterAllGates` khi stream end

**Kết luận: Plan hiện tại đã bám sát LeadZen production code rất chặt.**

### 4.2 Những gì Plan hiện tại THIẾU hoặc CHƯA ĐỦ DETAIL

| Gap | Severity | Source (evidence) |
|-----|----------|-------------------|
| **Token accounting calibration** | HIGH | LeadZen: `INITIAL_TOKENS_PER_CHAR = 0.34` (Vietnamese!), `tokensPerChar` recalibrate per call |
| **Independent recovery budgets** | HIGH | LeadZen: 3 separate counters, reset on success |
| **composeAbortSignals** | MEDIUM | LeadZen: `abort-signals.ts` — parent + timeout composition cho sub-agent |
| **MAX_AGENTS_PER_TURN enforcement** | MEDIUM | LeadZen: overflow IDs collected trước execution |
| **Title force turn logic** | LOW | LeadZen: TITLE_FORCE_BY_TURN = 8, clarity-gated early |
| **Activity persist on abort** | HIGH | LeadZen: `spawn-agent.ts` recovery block khi `signal.aborted` |
| **withGate pattern** | HIGH | LeadZen: transparent wrap sub-agent tools cho ask mode |
| **Lua script chi tiết** | MEDIUM | CAS pattern, jitter, MAX_CONSECUTIVE_ERRORS = 10 |
| **Image token estimation** | LOW | LeadZen: IMAGE_CHAR_EQUIV = 6_000 |
| **Context block NOT in history** | MEDIUM | Context block append ở cuối payload nhưng KHÔNG persist vào `messages` array |
| **compactSummary prepend pattern** | MEDIUM | Claude layout: summary as LEADING user message, không inject vào context block |

### 4.3 Những gì Hermes có mà DashZen KHÔNG cần

- Skills system / learning loop → DashZen không self-improve (focused tool)
- 20 platform adapters → DashZen web-only
- Trajectory generation → DashZen không train models
- SQLite / FTS5 → DashZen dùng PostgreSQL
- 70+ tools → DashZen ~10 domain tools

### 4.4 Những gì Hermes có mà DashZen NÊN học

| Feature | Hermes approach | DashZen consideration |
|---------|----------------|----------------------|
| **Profile isolation** | Per-profile HERMES_HOME | Multi-tenant `user_id` isolation trong DB |
| **Observable execution** | Callbacks với spinner | SSE events cho mọi action (đã có) |
| **Interruptible API calls** | Cancel mid-flight | asyncio.CancelledError handling |
| **ACP pattern** | stdio/JSON-RPC cho IDE | Không cần ngay, nhưng pattern tốt |

---

## 5. Kiến trúc Đề xuất cho DashZen

### 5.1 Nguyên tắc từ Research

Từ việc nghiên cứu cả hai hệ thống, đề xuất DashZen adopt:

**Từ LeadZen (direct reference, same use case):**
1. `mainRun()` pattern → `main_loop.py` async generator
2. `agentRun()` pattern → `agent_loop.py` isolated, no persist
3. `partitionBatches()` → `partition.py` (same logic, Python)
4. `gate-service.ts` → `gates/gate_service.py` (Lua scripts identical)
5. `stream-lock.ts` → `streaming/lock.py` (same CAS pattern)
6. Token accounting calibration (INITIAL_TOKENS_PER_CHAR phù hợp với Vietnamese text)
7. `spawn-agent.ts` withGate pattern → `spawn.py` với gate wrapping
8. Activity persist on abort (recovery block)

**Từ Hermes (general patterns):**
1. Tool self-registration pattern (thay vì manual import list)
2. Platform-agnostic core (AgentRuntime không phụ thuộc FastAPI)
3. Observable execution via callbacks
4. Interruptible at all levels

**DashZen-specific additions:**
1. Pydantic schemas cho structured output (không có ở cả hai)
2. 5-agent deterministic workflow (không có ở Hermes, LeadZen có 1 agent pipeline)
3. Canvas preview integration (domain-specific)
4. RAG component catalog (domain-specific)

### 5.2 Architectural Decision Record

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Python vs TypeScript | **Python** | ML ecosystem, Pydantic, FastAPI async |
| SQLite vs PostgreSQL | **PostgreSQL** | Multi-user, cloud, branching |
| Single agent vs multi-agent | **Multi-agent pipeline** | Dashboard creation cần specialized experts |
| Framework-based vs self-built | **Self-built** | Full control, no LangChain overhead |
| Hermes patterns vs LeadZen | **LeadZen-first** | Same use case, same patterns, TypeScript → Python translate |
| General skills vs fixed workflow | **Fixed 5-agent pipeline** | Dashboard creation có deterministic steps |
| SSE vs WebSocket | **SSE** | Simpler, proven, one-way server push |

### 5.3 Tình trạng Plan hiện tại

| File | Status | Assessment |
|------|--------|------------|
| `01-project-structure-and-techstack.md` | ✅ Complete | Solid architecture, aligned với LeadZen |
| `02-ui-features-chat-agent.md` | ✅ Complete | UI/UX detailed spec |
| `agent/phase-1-foundation.md` | ✅ Good | P0-P1 scope rõ ràng |
| `agent/phase-2-agent-pipeline.md` | ✅ Good | P2-P3 deliverables |
| `agent/phase-3-scale-production.md` | ✅ Good | P5 scope |
| `03-agent-runtime-and-memory.md` | ❌ MISSING | **Blocker** — main_loop detail, gate payloads |
| `04-dashboard-spec-schema.md` | ❌ MISSING | **Blocker** — Pydantic schemas |
| `05-mvp-scope.md` | ❌ MISSING | **Blocker** — MVP scope chốt |
| `06-api-contracts.md` | ❌ MISSING | **Blocker** — OpenAPI + SSE schema |

**→ Plan agentic cần được làm detail hơn với data từ research.**

---

## 6. Key Numbers (Production-proven từ hai repo)

Từ LeadZen code thực tế, các constants đã được battle-tested:

```python
# Orchestration
MAX_ITERATIONS = 40              # Main loop max tool-call iterations
MAX_AGENTS_PER_TURN = 3         # Prevent agent cascades
RECOVERY_LIMIT = 5              # Per recovery path
TITLE_FORCE_BY_TURN = 8         # Auto-title forced

# Sub-agent
SUBAGENT_MAX_TURNS = 40
SUBAGENT_TIMEOUT_MS = 1_080_000  # 18 minutes
MAX_OUTPUT_TOKENS_RECOVERY_LIMIT = 3

# Context / Compaction
MICRO_COMPACT_FRACTION = 0.60   # Tier 1 threshold
SUMMARY_COMPACT_FRACTION = 0.80  # Tier 2 threshold
KEEP_TOKENS = 40_000            # Recent history verbatim
INITIAL_TOKENS_PER_CHAR = 0.34  # Vietnamese-tuned conservative estimate
IMAGE_CHAR_EQUIV = 6_000        # Image block token estimate

# Tools
MAX_CONCURRENT_TOOLS = 5        # Parallel tool execution cap

# Gates
GATE_TTL_SEC = 1200             # 20 min orphan cleanup
POLL_INTERVAL_MS = 300          # 300ms poll interval
MAX_CONSECUTIVE_ERRORS = 10     # Fail-safe unblock after N Redis errors

# Stream Lock
LOCK_TTL_SEC = 90               # Short TTL (heartbeat refreshes)
LOCK_REFRESH_INTERVAL_MS = 20_000  # Heartbeat every 20s

# Artifact
ACTIVITY_RESULT_MAX = 2_000     # Per activity result cap
ACTIVITY_COUNT_MAX = 200        # Total activities cap
COMPACT_THRESHOLD = 4_000       # Agent output compact threshold

# Spawn
MAX_SPAWN_OUTPUT_COMPACT = 4_000  # > 4KB → compact envelope
SPAWN_SUMMARY_MAX = 2_000       # Summary cap
```

---

## 7. Mapping Plan → Code Files

Từ research, mapping giữa DashZen plan subsystems và LeadZen reference:

| DashZen Subsystem | LeadZen Reference | DashZen File |
|-------------------|------------------|--------------|
| ① Orchestration main_loop | `engine/main/main-run.ts` | `agents/orchestration/main_loop.py` |
| ① Orchestration agent_loop | `engine/agent/agent-run.ts` | `agents/orchestration/agent_loop.py` |
| ① spawn.py | `tools/orchestration/spawn-agent.ts` | `agents/orchestration/spawn.py` |
| ① exec_parallel.py | `engine/main/exec-parallel.ts` | `agents/orchestration/exec_parallel.py` |
| ① task_title | `engine/main/task-title.ts` | `agents/orchestration/task_title.py` |
| ② Agent Registry | `engine/prompt/agent-registry.ts` | `agents/registry/loader.py` |
| ② Frontmatter parser | `engine/prompt/frontmatter-parser.ts` | `agents/registry/schema.py` |
| ③ Memory FSM | `tools/state/set-memory.ts` | `agents/memory/state_machine.py` |
| ③ memory_file | `engine/tool/file-store.ts` (memory.md) | `agents/memory/memory_file.py` |
| ③ context_block | `engine/context/build-context-message.ts` | `agents/memory/context_block.py` |
| ④ Tool registry | `engine/tool/tool-registry.ts` | `agents/tools/registry.py` |
| ④ Loop detection | `engine/tool/loop-detection.ts` | `agents/tools/loop_detection.py` |
| ④ Read cache | `engine/tool/tool-cache.ts` | `agents/tools/read_cache.py` |
| ④ Partition | `partitionBatches()` | `agents/tools/partition.py` |
| ⑤ History builder | `engine/context/build-history.ts` | `agents/context/history.py` |
| ⑤ Compaction | `engine/context/compact-history.ts` + `microcompact.ts` | `agents/context/compaction.py` |
| ⑤ Token accounting | `estimateChars()` + `tokensPerChar` calibration | `agents/context/accounting.py` |
| ⑤ Thinking codec | `engine/context/thinking-codec.ts` | `agents/context/thinking_codec.py` |
| ⑥ LLM client | `lib/llm/index.ts` | `core/llm/client.py` |
| ⑦ Gate system | `lib/redis/gate-service.ts` | `agents/gates/gate_service.py` |
| ⑧ Artifact buffer | `ArtifactBuffer` in types | `agents/artifacts/buffer.py` |
| ⑨ Stream lock | `lib/redis/stream-lock.ts` | `agents/streaming/lock.py` |
| ⑨ SSE events | `MainStreamEvent` union | `agents/streaming/events.py` |
