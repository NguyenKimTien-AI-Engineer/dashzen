# Nghiên cứu LeadZen Agent — Production Reference

> **Nguồn:** `/home/kimtien/Project/leadzen`  
> **Ngày nghiên cứu:** 23/06/2026  
> **Stack:** TypeScript (Next.js 16 + tRPC + better-auth + Prisma 7 + GLM)  
> **Mô tả:** AI-powered landing page builder

> **LƯU Ý QUAN TRỌNG:** LeadZen là hệ thống production thực tế được dùng làm reference trực tiếp cho DashZen. Code được nghiên cứu từ source tại `/home/kimtien/Project/leadzen/packages/api/src/modules/task/`.

---

## 1. Tổng quan hệ thống

LeadZen build landing page từ user intent. Architecture chia thành:
- **Web app:** Next.js (apps/web)
- **API package:** tRPC routers + services + **agent engine** (`packages/api`)
- **Shared packages:** db (Prisma), auth (better-auth), config, env, ui

---

## 2. Cấu trúc Engine (`packages/api/src/modules/task/engine/`)

### 2.1 Module map

```
engine/
├── main/
│   ├── main-run.ts          # Main loop (async generator → SSE events)
│   ├── exec-parallel.ts     # Parallel tool execution
│   ├── main-helpers.ts      # loadHistory, flushArtifactBuffer, remapArtifacts
│   └── task-title.ts        # Auto-title generation
├── agent/
│   ├── agent-run.ts         # Sub-agent loop (isolated, no DB persist)
│   └── build-context.ts     # Build context message for agents
├── context/
│   ├── build-history.ts     # Build stable history prefix
│   ├── build-context-message.ts  # # MEMORY / # USER context block
│   ├── compact-history.ts   # Tier-2 summary compaction (LLM)
│   ├── keep-budget.ts       # Token budget constants (shared FE+BE)
│   ├── microcompact.ts      # Tier-1 microcompaction (no LLM)
│   ├── recovery-messages.ts # Inject recovery prompts
│   ├── thinking-codec.ts    # Encode/decode extended thinking
│   └── user-message.ts      # Build user context block
├── prompt/
│   ├── agent-registry.ts    # Load agent .md definitions
│   ├── frontmatter-parser.ts # Parse YAML frontmatter from .md files
│   ├── read-prompt.ts       # Read prompt files
│   └── system-prompt.ts     # System prompt assembly
├── tool/
│   ├── tool-registry.ts     # Tool sets: MAIN_TOOLS, AGENT_TOOLS, tiers
│   ├── tool-execute.ts      # Tool execution pipeline
│   ├── tool-validation.ts   # JSON schema validation
│   ├── loop-detection.ts    # LoopDetector class
│   ├── tool-cache.ts        # ReadCache, capToolResultForHistory
│   ├── tool-errors.ts       # Error envelope, isAbortError
│   ├── file-store.ts        # File upsert operations
│   ├── abort-signals.ts     # composeAbortSignals
│   ├── path-guards.ts       # Path traversal protection
│   └── dev-logger.ts        # Debug tool logging
└── types.ts                 # ToolHandler, ArtifactBuffer, MainStreamEvent, AgentStatus
```

### 2.2 Redis Infrastructure

```
lib/redis/
├── gate-service.ts    # registerGate, resolveGate, initGate, unregisterAllGates
├── stream-lock.ts     # acquireStreamLock, releaseStreamLock, refreshStreamLock
├── rate-limit.ts      # Rate limiting
└── index.ts           # Redis client factory
```

---

## 3. Main Loop (`main-run.ts`) — Phân tích chi tiết

### 3.1 Constants (Hard-coded, battle-tested)

```typescript
const MAX_ITERATIONS = 40              // Max tool-call iterations per turn
const RECOVERY_LIMIT = 5              // Max recovery attempts per path (max_tokens/empty/thinking-only)
const MAX_CONCURRENT_TOOLS = 5        // Parallel tool execution limit
const MAX_AGENTS_PER_TURN = 3         // Cap spawn_agent calls per turn
const TITLE_FORCE_BY_TURN = 8         // Auto-title forced from turn 8
const KEEP_TOKENS = 40_000            // Keep recent history tokens verbatim
const INITIAL_TOKENS_PER_CHAR = 0.34  // Conservative estimate (Vietnam dense tokenization)
const IMAGE_CHAR_EQUIV = 6_000        // Image token cost estimate
```

### 3.2 Luồng chính `mainRun()`

```
1. Persist user message (hoặc reuse pre-saved ID)
2. Load context:
   - loadHistory(prisma, taskId, userMsgId) → stable history prefix
   - Load memory.md từ DB
3. Start title generation (concurrent, cheap model)
4. LLM tool-call loop (max MAX_ITERATIONS):
   a. Refresh memory.md từ artifactBuffer (nếu set_memory đã chạy)
   b. compactIfOverBudget() — tier 1 then tier 2
   c. Build payload = [...messages, buildContextMsg()]
   d. Stream LLM call → yield SSE events
   e. Handle stop reasons (max_tokens, empty, thinking-only) → recovery
   f. Persist assistant message
   g. Execute tools (parallel batches)
   h. Persist tool results
   i. Check rejection (ask mode) → flush artifacts, stop
5. No tool calls → flush artifacts, finalize title, yield stream_done
6. MAX_ITERATIONS hit → yield stream_error
```

### 3.3 Token Accounting (Calibrated)

```typescript
// Dual-measurement system:
// - lastRealPromptTokens: exact from provider usage (ground truth)
// - tokensPerChar: calibrated ratio (updated after each call)
// - delta estimation: for messages appended since last real measurement

const currentInputTokens = (): number => {
  if (lastRealPromptTokens === 0) {
    return Math.ceil(estimateChars(messages) * tokensPerChar)
  }
  const deltaChars = estimateChars(messages.slice(lenAtLastCall))
  return lastRealPromptTokens + Math.ceil(deltaChars * tokensPerChar)
}
```

**Key insight:** Conservative estimate (overestimates) → compact early rather than overflow.

### 3.4 2-Tier Compaction (Production-proven)

```typescript
const compactIfOverBudget = async (): Promise<void> => {
  if (compactionExhausted) return
  if (currentInputTokens() <= microAtTokens) return  // Below tier-1 threshold

  // Tier 1: microcompact (cheap, in-memory, no LLM)
  const micro = microcompactMessages(messages, { keepCharBudget })
  if (micro.cleared > 0) resetTokenBase()

  // Still above tier-2 threshold?
  if (currentInputTokens() <= compactAtTokens) return

  // Tier 2: summary compaction (LLM call)
  // Reload from DB, summarize old portion, rebuild from kept tail
  const compaction = await compactHistoryIfNeeded(prisma, taskId, path, { signal, keepCharBudget })
  if (!compaction) { compactionExhausted = true; return }

  // Rebuild messages with summary prepended
  compactSummary = compaction.summary
  const rebuilt = buildHistory(compaction.keptPath)
  rebuilt.unshift(buildCompactSummaryMessage(compactSummary))
  messages.splice(0, messages.length, ...rebuilt)
  resetTokenBase()
}
```

**Tier thresholds:**
- Tier 1 (microcompact): 60% of `LLM_INPUT_BUDGET_TOKENS`
- Tier 2 (summary compact): 80% of `LLM_INPUT_BUDGET_TOKENS`

### 3.5 Recovery Paths (Independent budgets)

3 recovery paths với **independent budgets** (không share RECOVERY_LIMIT):
- `maxTokensRecoveryCount` — max_tokens không có tool calls
- `emptyResponseRecoveryCount` — empty response
- `thinkingOnlyRecoveryCount` — thinking nhưng không có text

Pattern: inject recovery message → `continue` (không tạo tool errors cascade).

### 3.6 Artifact Buffer

```typescript
// ArtifactBuffer = Map<string, {id: string, content: string}>
// Stage file writes trong turn → flush khi stream_done hoặc interrupt
// Tránh phantom files khi user cancel giữa chừng
const artifactBuffer = input.artifactBuffer  // Shared với stream route

// Flush on clean exit:
await flushArtifactBuffer(prisma, taskId, artifactBuffer, assistantMsg.id)

// Flush on rejection (ask mode):
await flushArtifactBuffer(prisma, taskId, artifactBuffer, lastChainParentId)
```

### 3.7 Spawn Agent Cap

```typescript
// Count spawn_agent per turn — cap at MAX_AGENTS_PER_TURN
const overflowAgentIds = new Set<string>()
{
  let agentCount = 0
  for (const tc of iterToolCalls) {
    if (tc.name === 'spawn_agent') {
      agentCount++
      if (agentCount > MAX_AGENTS_PER_TURN) overflowAgentIds.add(tc.id)
    }
  }
}
// Overflow agents get error result: "Re-call in next turn after first N finish"
```

### 3.8 Auto-title Generation

```typescript
// Concurrent với turn 1, cheap model
// Turns 1-7: model CÓ THỂ từ chối nếu intent chưa rõ
// Turn 8+: FORCE phải có title (TITLE_FORCE_BY_TURN = 8)
// Race-safe: prisma.task.updateMany({ where: { id: taskId, title: null } })
// → Không overwrite user rename (user rename → title không null)
```

---

## 4. Sub-Agent Loop (`agent-run.ts`) — Phân tích chi tiết

### 4.1 Khác biệt với main-run

| Đặc điểm | main-run | agent-run |
|----------|----------|-----------|
| DB persist | Có (full message tree) | Không |
| Stream tới user | Có (yield SSE events) | Không (callback onEvent) |
| Thinking display | main_think SSE | agent_think via onEvent |
| Context history | Load từ DB | Fresh messages array |
| Spawn đệ quy | Có (spawn_agent) | Không (AGENT_TOOLS không có spawn) |
| ask_user | Có | Không (agents headless) |
| Timeout | Không cố định | 18 phút (SUBAGENT_TIMEOUT_MS = 1_080_000) |
| Abort signal | User cancel | Parent signal + internal timeout |

### 4.2 Context Layout (mirroring Claude Code pattern)

```
system field    = agent system prompt + operating contract (stable, cache-friendly)
user msg #1     = <system-reminder> # MEMORY(agentPrompt) </system-reminder>
user msg #2     = <system-reminder> context </system-reminder>  (nếu có)
user msg #3     = task (actual work)
```

### 4.3 AgentRunResult (compact return)

```typescript
interface AgentRunResult {
  output: string      // Full agent output text
  toolsUsed: string[] // Tool names used
  iterations: number  // Actual iterations
  timedOut: boolean   // True if internal timeout fired
}
```

### 4.4 Output Compaction (spawn-agent.ts)

```typescript
const COMPACT_THRESHOLD = 4_000
if (output.length <= COMPACT_THRESHOLD) {
  execResult = output  // Return full
} else {
  // Large output → compact envelope từ Status/Summary
  const statusLine = parsed.status ? `**Status:** ${parsed.status.toUpperCase()}` : null
  const summaryLine = parsed.summary ? `**Summary:** ${parsed.summary}` : null
  // Không có Status/Summary + output lớn → errResult (main loop treat as failure)
}
```

---

## 5. Tool System

### 5.1 Tool Sets (Single source of truth)

```typescript
// MAIN_TOOLS — full set (main agent)
export const MAIN_TOOLS: ToolHandler[] = [
  writeFile, editFile, readFile, listFile,
  searchWeb, fetchWeb,
  askUser, setMemory,
  spawnTask, spawnAgent,
  viewImage, grepReference
]

// AGENT_TOOLS — curated subset (no agent/ask/memory/task tools)
export const AGENT_TOOLS: ToolHandler[] = [
  writeFile, editFile, readFile, listFile,
  searchWeb, fetchWeb,
  generateImage, viewImage, grepReference
]
```

**Rationale:**
- `spawn_agent` excluded từ AGENT_TOOLS → ngăn infinite recursion
- `ask_user` excluded → agents run headlessly
- `set_memory` excluded → state machine chỉ main loop control

### 5.2 Tool Tiers

```typescript
// READ_ONLY_TOOLS — bypass ask-mode gates
export const READ_ONLY_TOOLS = new Set([
  'read_file', 'list_file', 'search_web', 'fetch_web', 'grep_reference'
])

// ASK_BYPASS — skip Y/N approval card
export const ASK_BYPASS = new Set([
  ...READ_ONLY_TOOLS, 'ask_user', 'spawn_agent', 'set_memory'
])

// VISIBLE_TOOLS — emit activity row to UI
export const VISIBLE_TOOLS = new Set([
  'write_file', 'edit_file', 'search_web', 'fetch_web',
  'spawn_agent', 'spawn_task', 'generate_image', 'ask_user'
])

// CONCURRENT_SAFE — safe to run concurrently
export const CONCURRENT_SAFE = new Set([...READ_ONLY_TOOLS, 'ask_user'])
// spawn_agent KHÔNG concurrent — full LLM loop, không race với nhau
```

### 5.3 Batch Partitioning

```typescript
// Consecutive concurrent-safe tools → 1 parallel batch
// Mỗi non-safe tool → serial batch riêng (path races)
export function partitionBatches(toolCalls): Batch[] {
  return toolCalls.reduce((acc, tc) => {
    const safe = CONCURRENT_SAFE.has(tc.name)
    if (safe && acc[acc.length - 1]?.isConcurrencySafe) {
      acc[acc.length - 1].toolCalls.push(tc)  // Merge vào batch hiện tại
    } else {
      acc.push({ isConcurrencySafe: safe, toolCalls: [tc] })  // Tạo batch mới
    }
    return acc
  }, [])
}
```

---

## 6. Gate System (Redis-backed HITL)

### 6.1 Gate Flow

```
Agent muốn run write_file (non-safe)
  → initGate(taskId, callId) — SET 'pending' NX BEFORE emit SSE
  → emit main_tool SSE → UI hiện Y/N card
  → registerGate(taskId, callId) — poll Redis every 300ms
  → User approve/reject → resolveGate() — SET_IF_PENDING (Lua CAS)
  → Gate resolved → tool execute / reject
  → unregisterAllGates(taskId) khi stream_done
```

### 6.2 Anti-race Patterns

```typescript
// 1. initGate TRƯỚC emit SSE
//    → Nếu client trả lời nhanh hơn gate được init → không mất event
await initGate(taskId, callId)
ctx.emit({ type: 'main_tool', callId, ... })

// 2. CAS via Lua SET_IF_PENDING
//    → Chống double-approve (2 concurrent requests)
const SET_IF_PENDING = `
  if redis.call('GET', KEYS[1]) == 'pending' then
    return redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
  end
  return nil
`

// 3. Poll jitter
pollTimer = setTimeout(poll, POLL_INTERVAL_MS + Math.floor(Math.random() * 100))
// → Tránh thundering herd khi nhiều gates resolve đồng thời

// 4. Fail-safe unblock sau 10 Redis errors liên tiếp
if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) { stop(expired); return }
// → Không treo stream khi Redis flaky
```

### 6.3 Ask Gate vs Tool Gate

```typescript
// Tool gate: approve/reject tool execution
gate:${taskId}:${callId}  → 'pending' | 'approved' | 'rejected' | 'approved_with:...' | 'rejected_with:...'

// Ask gate: user submits text answer
ask:${taskId}:${callId}  → 'pending' | <user_answer_string>
```

**Feedback injection:**
- `approved + feedback` → feedback appended to tool_result (LLM sees guidance)
- `rejected + feedback` → feedback injected AS tool_result (LLM continues same turn)
- `rejected` (no feedback) → stream stops

### 6.4 In-memory Fallback (Dev mode)

```typescript
// Không cần Redis cho dev — globalThis singleton để survive Turbopack hot reload
const memoryGates = (globalForGates.__memoryGates ??= new Map())
```

---

## 7. Stream Lock System

```typescript
const LOCK_TTL_SEC = 90             // Short TTL — heartbeat refreshes
const LOCK_REFRESH_INTERVAL_MS = 20_000  // Heartbeat every 20s

// Atomic acquire (SET NX EX) → token UUID
// Atomic release (Lua compare-and-delete) → chỉ release nếu token match
// Atomic refresh (Lua compare-and-expire) → chỉ refresh nếu token match
// → Prevents stale cleanup từ releasing successor's lock
```

---

## 8. Memory System (`set-memory.ts`)

### 8.1 memory.md Format

```yaml
---
type: page
phase: create-page
---
```

### 8.2 Transition Map (Enforced server-side)

```typescript
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  '': ['create-chat', 'create-page', 'create-image', 'create-video', 'create-campaign'],
  'create-chat': ['create-page', 'create-image', 'create-video', 'create-campaign'],
  'create-page': ['edit-page'],
  'edit-page': [],         // terminal
  'create-image': [],      // terminal
  'create-video': ['edit-video'],
  'edit-video': [],
  'create-campaign': ['edit-campaign'],
  'edit-campaign': [],
}
```

### 8.3 Workflow Injection

```typescript
// Phase thay đổi → load workflow file và return cho LLM
const workflowContent = readPrompt(`context/plugin/memory/${resolvedType}/${resolvedPhase}.md`)
// LLM nhận workflow instructions như injected context
```

### 8.4 set_memory Là ASK_BYPASS

`set_memory` không cần user approval (luôn bypass gate) — state machine changes không require HITL.

### 8.5 artifactBuffer Integration

```typescript
// set_memory stage vào artifactBuffer → main-run refreshes context block
ctx.artifactBuffer.set('memory.md', { id, content })
// → Trong main loop iteration tiếp theo: memoryContent = appendWorkflowToMemory(bufferedMemory.content)
```

---

## 9. Agent Registry (`agent-registry.ts`)

- Agent definitions: `.md` files với YAML frontmatter
- Auto-discovery: adding new `.md` = new agent (no code change, no restart)
- Frontmatter fields: `name`, `displayName`, `tools`, `disallowedTools`, `maxTurns`, `maxTokens`, `model`, `temperature`

```typescript
// Getter (re-evaluated per request) — hot reload support
get description() { return buildDescription() }
```

---

## 10. Spawn Agent Activities

```typescript
// Activity types persisted to AgentRun.activities
type PersistedActivity =
  | { type: 'text'; content: string }
  | { type: 'thinking'; content: string }
  | { type: 'tool'; callId: string; toolName: string; displayName?: string; args: unknown; approval: 'approved' | 'rejected' | null; result: string | null }

// Limits:
const ACTIVITY_RESULT_MAX = 2_000   // Cap result per activity
const ACTIVITY_COUNT_MAX = 200      // Cap total activities

// Persist via AgentRun.upsert (messageId + callId unique key)
// → UI can reload và reconstruct agent timeline
```

---

## 11. Recovery từ Abort (spawn-agent.ts)

```typescript
// Khi stream abort (lock lost / server restart) giữa agent run
// → spawn-agent tự persist tool result trực tiếp vào DB
// → Task history intact trên client reconnect
if (ctx.signal?.aborted && ctx.messageId && ctx.callId) {
  await ctx.prisma.message.create({
    data: { tool_call_id: ctx.callId, result: execResult, parentId: ctx.messageId }
  })
}
```

---

## 12. LLM Client (`lib/llm/`)

```typescript
// Key pool rotation — nhiều API keys
// Fetch-with-retry — exponential backoff
// Ollama client — local dev
// Streaming: async generator → LLMChunk[]
```

---

## 13. Bài học quan trọng từ LeadZen cho DashZen

| Pattern | LeadZen implementation | DashZen adaptation |
|---------|------------------------|-------------------|
| **Async generator loop** | `mainRun()` yields `MainStreamEvent` | Same pattern, Python `async_generator` |
| **Independent recovery budgets** | 3 separate counters (max_tokens/empty/thinking) | Copy exact constants |
| **Calibrated token ratio** | `tokensPerChar` updated after each call | Implement trong `context/accounting.py` |
| **artifactBuffer pattern** | Stage → flush on done/interrupt | Tránh phantom files |
| **initGate before emit** | Race-condition prevention | Critical pattern cho gate |
| **Lua CAS SET_IF_PENDING** | Double-approve prevention | Copy exact Lua script |
| **composeAbortSignals** | Parent + timeout abort composition | Cho sub-agent timeout |
| **Activity cap** | 200 activities, 2KB result cap | UI performance bound |
| **Agent output compact threshold** | 4KB threshold | Prevent context blow-up |
| **Recovery tool result persist** | Abort → direct DB write | Data integrity on restart |
| **withGate pattern** | Wrap sub-agent tools transparently | Ask mode cho sub-agents |
| **Workflow file as tool result** | `set_memory` returns workflow content | LLM nhận instructions inline |
| **Title force turn** | TITLE_FORCE_BY_TURN = 8 | User experience |
| **Short lock TTL + heartbeat** | 90s TTL + 20s refresh | Nhanh detect orphan lock |
