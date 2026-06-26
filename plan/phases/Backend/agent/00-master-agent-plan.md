# DashZen — Master Agent Plan

> **Phiên bản:** 3.0  
> **Ngày cập nhật:** 23/06/2026  
> **Trạng thái:** Authoritative implementation guide — supersedes `phase-1.md`, `phase-2.md`, `phase-3.md`  
> **Tác giả:** Nghiên cứu từ Hermes Agent (NousResearch, 200k★) + LeadZen (production codebase)

---

## Mục lục

| # | Nội dung | Priority |
|---|----------|----------|
| §1 | [Quan hệ với các file Plan khác](#1-quan-hệ-với-các-file-plan-khác) | P0 — đọc trước |
| §2 | [Hai Track chính & Nguyên tắc kiến trúc](#2-hai-track-chính--nguyên-tắc-kiến-trúc) | P0 |
| §3 | [Constants production-proven](#3-constants-production-proven) | P0 — tham chiếu khi code |
| §4 | [Track A — Phase 1: Foundation & Minimal Loop](#4-track-a--phase-1-foundation--minimal-loop) | P0 |
| §5 | [Track A — Phase 2: Full 5-Agent Dashboard Pipeline](#5-track-a--phase-2-full-5-agent-dashboard-pipeline) | P1 |
| §6 | [Track A — Phase 3: Production Hardening](#6-track-a--phase-3-production-hardening) | P2 |
| §7 | [Track B — Phase 4: RAG Foundation](#7-track-b--phase-4-rag-foundation) | P3 — sau khi Track A xong |
| §8 | [Track B — Phase 5: Document-driven Dashboard](#8-track-b--phase-5-document-driven-dashboard) | P3 |
| §9 | [Dependency Graph tổng thể](#9-dependency-graph-tổng-thể) | — |
| §10 | [File Map: Plan → Code](#10-file-map-plan--code) | — |

---

## 1. Quan hệ với các file Plan khác

### 1.1 Câu hỏi: Ngoài file này, còn cần dùng file plan nào nữa không?

Hệ thống plan của DashZen gồm nhiều file, mỗi file có vai trò riêng. File này (`00-master-agent-plan.md`) là **implementation guide duy nhất cho backend agent** — nhưng vẫn cần đọc kết hợp với các file sau:

**CẦN THIẾT — Phải đọc trước khi code bất kỳ subsystem nào:**

| File | Vai trò | Khi nào dùng |
|------|---------|-------------|
| `plan/phases/Backend/01-project-structure-and-techstack.md` | **Kiến trúc tổng thể** — 11 subsystem catalog, tech stack, monorepo layout, API surface, nguyên tắc boundary | Đọc khi cần hiểu "tại sao kiến trúc thiết kế như vậy" và "subsystem X nằm ở package nào". File này là nền tảng, file này là implementation guide |
| `plan/phases/Backend/agent/phase-1/` | **Step-by-step Phase 1** — tách §4 thành 11 file `00`–`10` (như `auth/`) | Khi implement Track A Phase 1: đọc `README.md` → follow thứ tự `00` → `10` |
| `plan/phases/Backend/agent/phase-2/` | **Step-by-step Phase 2** — tách §5 thành 12 file `00`–`11` | Khi implement Track A Phase 2: **sau Phase 1 Done** → đọc `README.md` → `00` → `11` |
| `plan/research/02-leadzen-agent-research.md` | **Reference implementation** — code patterns từ production codebase TypeScript | Đọc khi cần hiểu chi tiết thuật toán: 2-tier compaction, gate service, token accounting. Code TypeScript trong file này là "bản gốc" để translate sang Python |
| `plan/research/03-comparison-synthesis.md` | **Bảng mapping** — đối chiếu subsystem DashZen ↔ file LeadZen tương ứng | Dùng khi muốn tìm "file LeadZen nào là reference cho subsystem này?" |

**KHÔNG CẦN cho backend agent (dùng cho team FE):**

| File | Dành cho |
|------|---------|
| `plan/phases/UI/02-ui-features-chat-agent.md` | Frontend team: TaskContext, SSE integration, UI components |
| `plan/phases/UI/UX/` | Frontend UX phases |
| `plan/phases/Backend/auth/` | Auth system (đã xong riêng) |

### 1.2 Tóm tắt: Luồng đọc cho developer

```
Lần đầu tiếp cận dự án:
  1. Đọc 01-project-structure-and-techstack.md §1-§4 → hiểu kiến trúc tổng thể
  2. Đọc 00-master-agent-plan.md §1-§3 → hiểu scope và constants
  3. Chọn phase cần build → đọc section tương ứng trong file này
     Phase 1: mở phase-1/README.md → implement theo 00-10
     Phase 2: mở phase-2/README.md → implement theo 00-11 (sau Phase 1 Done)

Khi implement một subsystem cụ thể:
  1. Đọc section trong file này → "phải làm gì"
  2. Đọc file step tương ứng trong phase-1/ hoặc phase-2/ → checklist chi tiết
  3. Tra cứu research/02-leadzen → "làm như thế nào" (code TypeScript reference)
  4. Tra cứu research/03-comparison → "file TypeScript nào tương ứng"
```

---

## 2. Hai Track chính & Nguyên tắc kiến trúc

### 2.1 Tại sao tách hai Track?

DashZen được chia thành **hai mảng độc lập, tuần tự**. Track B **không được bắt đầu** khi Track A chưa hoàn chỉnh. Lý do:

- **Track A** xây dựng nền tảng agent: khả năng chat tự do, tạo dashboard từ yêu cầu ngôn ngữ tự nhiên, pipeline 5 agent hoạt động ổn định, streaming production-grade. Đây là giá trị cốt lõi của sản phẩm.
- **Track B** mở rộng khả năng nhập liệu: thay vì user tự mô tả bằng lời, user tải tài liệu thực (báo cáo, file Excel, PDF) lên và agent tự đọc, hiểu, rồi tạo dashboard dựa trên dữ liệu thực trong tài liệu đó. Track B phụ thuộc hoàn toàn vào hệ thống agent của Track A đã hoạt động đúng.

```
TRACK A ──────────────────────────────────────────────── TRACK B
[Phase 1] → [Phase 2] → [Phase 3]   SAU ĐÓ   [Phase 4] → [Phase 5]
Foundation   5-Agent     Hardening             RAG Core   Doc-Dashboard
```

### 2.2 Phạm vi từng Track

**Track A — Agent Core** (Phases 1–3):
User nhắn tin bằng ngôn ngữ tự nhiên → hệ thống agent hiểu intent → tạo dashboard hoàn chỉnh. Dữ liệu dashboard là mock data hoặc schema mà user khai báo bằng tay. Không có document upload, không có RAG.

**Track B — Document Intelligence** (Phases 4–5):
User tải lên tài liệu có nghĩa (báo cáo doanh thu PDF, file Excel dữ liệu, bản kế hoạch Word) → hệ thống phân tích, lập index, lưu vector → khi user yêu cầu dashboard, agent có thể truy vấn tài liệu đó để bind dữ liệu thực vào widgets thay vì dùng mock data.

### 2.3 Nguyên tắc kiến trúc KHÔNG thay đổi

Các nguyên tắc này được rút ra từ nghiên cứu Hermes (200k stars) và LeadZen (production), cả hai đều converge về cùng giải pháp. **Không thay đổi** trừ khi có evidence từ profiling thực tế.

1. **Không dùng framework agent:** Không LangGraph, LangChain, CrewAI, MCP, Mem0. Agent runtime tự build để kiểm soát hoàn toàn behavior — framework sẽ che khuất logic và gây debug phức tạp khi có lỗi production.

2. **Dual-loop tách biệt:** Main loop là orchestrator user-facing (persist mọi message vào DB, stream trực tiếp về client). Sub-agent loop là worker headless (không persist message nội bộ, chỉ trả kết quả compact về main loop). Hai loop dùng hệ thống context riêng biệt.

3. **Artifact buffer:** Mọi file write trong suốt một stream đều được stage vào bộ nhớ tạm (ArtifactBuffer), không ghi DB ngay. Chỉ flush xuống DB khi stream kết thúc thành công hoặc bị ngắt có chủ ý. Điều này đảm bảo không có "phantom files" tồn tại trong DB khi user cancel giữa chừng.

4. **initGate trước emit SSE:** Khi cần user approve một tool call, gate phải được khởi tạo trong Redis TRƯỚC khi emit SSE event về phía client. Nếu làm ngược lại, có race condition: client approve quá nhanh trước khi gate tồn tại → approve bị bỏ mất.

5. **Independent recovery budgets:** Khi LLM trả về lỗi (cắt giữa chừng vì token, không có text, chỉ có thinking), mỗi loại lỗi có một counter riêng và ngân sách retry riêng. Không gộp chung để một loại lỗi không "ăn" hết budget của loại khác.

6. **Token accounting calibrated:** Thay vì chỉ ước lượng token bằng tỉ lệ char/token cố định, sau mỗi lần gọi LLM thực tế, hệ thống nhận được số token chính xác từ provider và recalibrate tỉ lệ đó. Điều này đặc biệt quan trọng với tiếng Việt (tokenize dày hơn tiếng Anh — khoảng 2.9 chars/token).

7. **Context block ở cuối payload:** Phần history message là stable prefix (cache-friendly với Anthropic prefix caching). Phần context block động (memory.md + user instructions + workflow) luôn append ở cuối payload mỗi turn, không bao giờ lưu vào mảng messages — điều này giữ prefix ổn định và không vô hiệu hóa cache.

8. **CompactSummary là leading user message:** Khi history bị compress, phần summary không inject vào context block mà được prepend như message user đầu tiên (theo layout của Claude). Điều này đảm bảo model đọc summary trước khi đọc phần history còn lại.

---

## 3. Constants Production-proven

Các giá trị này được validate từ LeadZen production. **Không thay đổi** trừ khi có evidence cụ thể từ profiling (ví dụ: user thực tế gặp timeout với 18 phút, hoặc microcompact không đủ hiệu quả).

Tất cả constants tập trung tại `agents/orchestration/constants.py` — không rải rác khắp codebase.

### 3.1 Vòng lặp chính

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `MAX_ITERATIONS` | 40 | Số lần LLM call tối đa trong một turn. Sau 40 lần tool-calling mà vẫn chưa kết thúc → báo lỗi "agent reached tool call limit". Con số này đã được tính toán để cover các workflow phức tạp nhất (5-agent pipeline) mà không để agent chạy vô hạn |
| `MAX_AGENTS_PER_TURN` | 3 | Số lần spawn_agent tối đa trong một turn. Khi main loop muốn gọi agent thứ 4+, các call đó nhận ngay một error message yêu cầu gọi lại ở turn sau. Ngăn cascade agent bùng nổ |
| `RECOVERY_LIMIT` | 5 | Số lần retry tối đa cho mỗi loại lỗi LLM (max_tokens, empty response, thinking-only). Mỗi loại có counter riêng — exhausting một loại không ảnh hưởng loại kia |
| `TITLE_FORCE_BY_TURN` | 8 | Turn thứ 8 trở đi, auto-title generation bắt buộc phải đặt tên cho task (trước đó model có thể từ chối nếu chưa đủ context). Đảm bảo không có task nào còn tên "Untitled" sau 8 lượt chat |

### 3.2 Sub-agent

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `SUBAGENT_MAX_TURNS` | 40 | Giới hạn iteration cho sub-agent loop (giống main loop) |
| `SUBAGENT_TIMEOUT_MS` | 1,080,000 (18 phút) | Wall-clock timeout cho một sub-agent run. Nếu agent chạy quá 18 phút, bị abort để tránh block server. Giá trị = 90% của SUBAGENT_MAX_TURNS × 30s/turn worst-case |
| `MAX_OUTPUT_TOKENS_RECOVERY_LIMIT` | 3 | Recovery limit cho agent loop (ít hơn main loop vì sub-agent không stream trực tiếp đến user) |

### 3.3 Context & Compaction

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `LLM_CONTEXT_WINDOW` | 128,000 tokens | Kích thước context window của model chính |
| `MICRO_COMPACT_FRACTION` | 0.60 (60%) | Khi input vượt 60% budget → trigger Tier 1 compaction (xóa old tool results không quan trọng, không cần gọi LLM) |
| `SUMMARY_COMPACT_FRACTION` | 0.80 (80%) | Khi input vượt 80% budget → trigger Tier 2 compaction (gọi LLM để tóm tắt phần history cũ, đắt hơn nhưng giảm được nhiều hơn) |
| `KEEP_TOKENS` | 40,000 tokens | Phần history gần nhất được giữ nguyên khi compact (không tóm tắt). Đảm bảo context ngay trước tool call cuối cùng luôn rõ ràng |
| `INITIAL_TOKENS_PER_CHAR` | 0.34 | Tỉ lệ ước lượng token/char khi chưa có real data từ provider. Giá trị 0.34 là conservative (overestimate) để compact sớm hơn là overflow — được tune cho tiếng Việt (tokenize dày) |
| `IMAGE_CHAR_EQUIV` | 6,000 chars | Một image block tương đương ~6,000 chars khi ước lượng token cost. Images cost ~2,000 tokens flat, tỉ lệ 0.34 suy ra 6,000 chars |

### 3.4 Tool execution

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `MAX_CONCURRENT_TOOLS` | 5 | Số tool chạy song song tối đa trong một batch. Chỉ áp dụng cho CONCURRENT_SAFE tools (read-only). Write tools và spawn luôn chạy serial |

### 3.5 Gate (HITL)

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `GATE_TTL_SEC` | 1,200 (20 phút) | TTL của Redis gate key — chỉ dùng cho orphan cleanup (nếu server crash, gate key tự xóa sau 20 phút). Không phải behavioral timeout |
| `POLL_INTERVAL_MS` | 300ms | Frequency poll Redis để check xem user đã approve/reject chưa |
| `MAX_CONSECUTIVE_ERRORS` | 10 | Nếu Redis lỗi 10 lần liên tiếp, fail-safe unblock gate (không để stream treo vĩnh viễn khi Redis flaky) |

### 3.6 Stream Lock

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `LOCK_TTL_SEC` | 90 giây | TTL ngắn để detect orphan lock nhanh. An toàn vì heartbeat refresh liên tục |
| `LOCK_REFRESH_INTERVAL_MS` | 20,000ms (20 giây) | Heartbeat interval — refresh TTL của lock mỗi 20s để chứng minh stream vẫn đang sống |

### 3.7 Artifact & Activities

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `ACTIVITY_RESULT_MAX` | 2,000 chars | Cap kết quả của mỗi tool call khi lưu vào activities JSON của AgentRun. Giữ DB size kiểm soát được |
| `ACTIVITY_COUNT_MAX` | 200 entries | Số lượng activity entries tối đa per agent run. Sau 200, entries mới bị bỏ qua |
| `AGENT_OUTPUT_COMPACT_THRESHOLD` | 4,000 chars | Nếu output của sub-agent ≤ 4,000 chars → trả full về main loop. Nếu > 4,000 → chỉ trả Status + Summary để tránh blow-up context main loop |
| `SPAWN_SUMMARY_MAX` | 2,000 chars | Cap độ dài Summary trong spawn output contract |

---

## 4. Track A — Phase 1: Foundation & Minimal Loop

> **Mục tiêu:** Dựng hạ tầng và agent runtime tối thiểu — đủ để gửi một prompt, nhận stream SSE về, agent con ghi ra một file kết quả.
>
> **Deliverable cuối phase:** User gửi "tạo dashboard doanh thu" → main agent spawn dashboard-planner → planner ghi `spec.md` → FE nhận `file_artifact` event và hiển thị spec.
>
> **Chưa cần:** Memory FSM, full workflow pipeline, HITL gates, context compaction, upload, rate limiting.

### 4.1 Hạ tầng & Scaffold (Infra)

**1.1 Docker Compose services:**
Dựng 3 services cần thiết: PostgreSQL 16 làm database chính (với healthcheck `pg_isready` để các service khác biết khi nào DB sẵn sàng), Redis 7 Alpine làm cache và lock store (bật `appendonly yes` để data survive restart), MinIO làm object storage S3-compatible cho workspace files và attachments. Mỗi service cần persistent volume để data không mất khi container restart.

**1.2 Environment variables:**
File `.env.example` phải khai báo đầy đủ tất cả biến môi trường. Nhóm biến theo từng service: connection strings cho DB/Redis/MinIO, JWT secret (random 64 bytes), LLM provider config (mặc định là Ollama local cho dev, có thể override bằng Anthropic/OpenAI key cho production). Không hardcode bất kỳ credential nào trong code.

**1.3 Monorepo packages scaffold:**
Cấu trúc `uv` workspaces gồm 5 packages: `apps/api` (FastAPI adapter layer), `packages/core` (LLM client + schemas + config, zero agent logic), `packages/agents` (agent runtime subsystems), `packages/tools` (tool implementations/handlers), `packages/db` (SQLAlchemy models + Alembic migrations). Dependency direction: `api → agents, db, core` | `agents → tools, db, core` | `tools → core`. Không để `core` import từ `agents`.

**1.4 Alembic migration setup:**
Khởi tạo Alembic trong `packages/db/`. File `alembic.ini` phải đọc DATABASE_URL từ environment variable — không hardcode connection string. Migration đầu tiên (001_initial_schema) tạo đủ 4 tables cho Phase 1.

### 4.2 ⑥ LLM System (`packages/core/src/core/llm/`)

LLM System là lớp trừu tượng mỏng giữa agent runtime và các AI provider. Mục tiêu: thay đổi provider không chạm vào Orchestration layer. Toàn bộ streaming, retry, format conversion nằm ở đây.

**2.1 LLMClient Protocol (interface):**
Định nghĩa `LLMClient` là một Protocol (không phải abstract class) với hai method: `chat()` cho non-streaming (dùng cho title generation, compaction) và `stream()` cho streaming (dùng cho main loop). Method `stream()` phải là async generator trả về các chunk: text delta, thinking delta, tool call, done/error. Interface này giữ cho Orchestration layer không biết provider là Ollama hay Anthropic.

**2.2 Ollama provider (dev default):**
Sử dụng `httpx.AsyncClient` để gọi Ollama REST API. Endpoint: `/api/chat` với `stream: true`. Parse từng JSON line từ response stream và emit `LLMDelta` events tương ứng. Lưu ý: Ollama không hỗ trợ extended thinking, `thinking_delta` events sẽ không bao giờ được emit từ provider này. Tất cả dev workflow sẽ dùng Ollama để zero-cost.

**2.3 Anthropic provider (production):**
Sử dụng Anthropic Messages API (`/v1/messages`) với streaming. Cần handle: tool use content blocks (Anthropic format khác OpenAI), extended thinking blocks (signature + text + redacted), usage tracking (promptTokens là exact count từ provider — dùng để calibrate token ratio). Provider này là primary production provider.

**2.4 OpenAI provider (alternative):**
Sử dụng OpenAI Chat Completions API với streaming. Tool calls format trong delta khác Anthropic. Đây là fallback khi không dùng Anthropic. Không hỗ trợ extended thinking native (có thể fake với system prompt nhưng không nên).

**2.5 Token budget constants (`budget.py`):**
File này export tất cả các số liên quan đến token budget. Frontend dùng cùng constants này để render context donut (gauge hiển thị % context đã dùng). Constants được expose qua `GET /v1/llm/budget` để FE không hardcode. Xem §3.3 cho giá trị cụ thể.

### 4.3 ⑩ Persistence System (`packages/db/`)

Persistence System sở hữu toàn bộ DB schema và data access layer. Không subsystem nào được import và dùng trực tiếp SQLAlchemy session ngoài lớp service của `packages/db`.

**3.1 Task model:**
Lưu thông tin mỗi conversation: `id` (UUID), `user_id` (FK về User), `title` (null = "Untitled" — chỉ set khi auto-title chạy xong), `status` (active/archived), `type` (null → chat → dashboard, không thể đi ngược), `created_at`, `updated_at`. Field `type` quan trọng cho Memory FSM ở Phase 2 — đảm bảo column này có index.

**3.2 Message model:**
Lưu mọi message trong tree: `id` (UUID), `task_id` (FK), `role` (user/assistant/tool/compact), `content` (nội dung), `parent_id` (FK → Message tự trỏ — tạo tree structure), `prompt_tokens` (null nếu không phải assistant message, là exact count từ provider), `thinking` (encoded thinking blocks nếu có), `created_at`. Column `parent_id` là cơ chế branching: regenerate một message tạo nhánh mới thay vì overwrite.

**3.3 File model:**
Sở hữu unified model cho tất cả files trong workspace: `id`, `task_id`, `message_id` (null = file chưa được link về message cụ thể), `name` (e.g. "spec.md", "memory.md"), `source` (workspace | upload), `kind` (text | image | binary), `content` (chỉ cho text files), `url` (cho binary/image trên MinIO), `content_type`, `size`. Overwrite-by-name được xử lý ở application layer, không có unique constraint trên (task_id, name) — nhiều phiên bản của cùng file có thể tồn tại với các message_id khác nhau (branching).

**3.4 AgentRun model:**
Lưu timeline activities của mỗi sub-agent spawn: `id`, `message_id` (FK về message chứa tool call), `call_id` (UUID unique per spawn call), `name` (tên agent), `activities` (JSON array — xem §5.3 cho schema chi tiết), `status` (done/wait/fail), `summary`. Composite unique index trên `(message_id, call_id)` cho phép upsert idempotent.

**3.5 CRUD service layer:**
Mỗi model có service file riêng: `task_service.py` (create, list, get, update, delete, bulk delete), `message_service.py` (create single, create batch, get tree path từ root đến leaf), `file_service.py` (upsert by name, get artifacts filtered by task, get single file), `agent_run_service.py` (upsert by messageId+callId). Không để raw SQL rải rác trong routes.

### 4.4 ⑨ Streaming System — Core (`packages/agents/src/agents/streaming/`)

Streaming System chịu trách nhiệm vận chuyển events từ agent loop về client qua SSE. Nó sở hữu schema event (single source of truth cho cả FE và BE) và cơ chế lock để đảm bảo chỉ một stream chạy per task tại một thời điểm.

**4.1 SSE Event Schema (`events.py`) — single source of truth:**
Định nghĩa toàn bộ các Pydantic models cho SSE events. Nhóm sự kiện:
- **Main loop events:** `main_text` (streaming text delta từ orchestrator), `main_think` (extended thinking delta), `main_tool` (tool call bắt đầu — hiển thị activity chip trên UI), `main_result` (kết quả tool — success/rejected/error), `main_ask` (agent hỏi user — trigger form input)
- **Sub-agent events:** `agent_start` (agent được spawn — mở block trong UI), `agent_text` (text delta từ agent), `agent_think` (thinking delta từ agent), `agent_tool` (agent call một tool), `agent_result` (kết quả tool trong agent), `agent_done` (agent kết thúc với status + summary)
- **Lifecycle events:** `file_artifact` (file workspace được tạo/cập nhật — trigger canvas preview), `task_meta` (title hoặc type thay đổi), `heartbeat` (keep-alive, KHÔNG dùng "ping"), `stream_done` (kết thúc thành công), `stream_error` (lỗi, message user-friendly)

FE phải consume tất cả event types này. File này export `MainStreamEvent = Union[tất cả events]` để type-safe.

**4.2 Stream Lock (`lock.py`):**
Cơ chế đảm bảo không có hai stream chạy đồng thời trên cùng một task. Khi stream route nhận request: thử acquire lock bằng atomic Redis `SET NX EX` với UUID token. Nếu lock đã tồn tại → trả 409. Nếu acquire thành công → bắt đầu stream. Trong suốt stream, background heartbeat task refresh TTL của lock mỗi 20 giây. Khi stream kết thúc (dù success hay error) → release lock bằng Lua compare-and-delete (chỉ xóa nếu token match — ngăn stream sau vô tình xóa lock của stream mới hơn). In-memory fallback cho dev khi không có Redis: dùng dict singleton trên `globalThis` equivalent.

**4.3 EventBus (`event_bus.py`):**
Internal pub/sub giữa agent loop và stream route. Agent loop gọi `emit(event)`, stream route consume events và serialize sang SSE format (`data: <json>\n\n`). Implement bằng `asyncio.Queue` — producer (agent) put events, consumer (route) get events trong async for loop. EventBus không persist events — là ephemeral transport layer.

**4.4 Stream resilience guards (`guards.py`):**
- **Pending message reuse:** Trước khi tạo user message mới, kiểm tra xem task có message user nào đang "orphaned" (không có assistant response tương ứng) không. Nếu có, reuse message ID đó thay vì tạo duplicate — tránh duplicate LLM run khi client retry request.
- **5-second dedup:** Nếu cùng content message gửi trong vòng 5 giây → short-circuit, không gọi LLM. Chống double-submit.
- **Safety-net 10 phút:** Background task kiểm tra orphan locks mỗi vài phút — nếu lock tồn tại nhưng heartbeat không được refresh (server crash) → auto-abort và release lock.
- **Stop handshake:** `POST /stop` set abort signal → main loop nhận signal, dừng lại, flush artifacts đã stage, trả `stream_done` kèm partial_message_id. Client dùng partial_message_id để hiển thị partial response.

### 4.5 ① Orchestration — Minimal (`packages/agents/src/agents/orchestration/`)

Orchestration là subsystem điều phối toàn bộ luồng chạy — nó gọi tất cả subsystem khác, không subsystem nào gọi ngược lại Orchestration.

**5.1 RuntimeContext và run_task() (`runtime.py`):**
`RuntimeContext` là dataclass tập hợp tất cả dependencies cần thiết cho một task run: task_id, user_id, DB session, Redis client, ArtifactBuffer (shared giữa route và main loop), mode (ask/auto), thinking_enabled flag, user_instructions, và abort signal. `run_task()` là entry point duy nhất: nhận RuntimeContext, user message, parent_id, tool list, system prompt → wiring tất cả subsystem → gọi `main_loop()`. API route không import gì từ `main_loop.py` trực tiếp — chỉ gọi `run_task()`.

**5.2 Main loop (`main_loop.py`):**
Đây là engine cốt lõi. Là async generator, mỗi iteration `yield` các SSE events về caller. Luồng hoạt động của một turn:

- Bước 1 — Lưu user message: Tạo Message record trong DB ngay lúc đầu. Nếu reuse pre-saved (từ dedup guard), skip bước này.
- Bước 2 — Load context: Song song load 2 thứ: message tree path (lịch sử hội thoại từ root đến parent_id) và file memory.md hiện tại từ workspace. Đây là nền tảng của payload sẽ gửi LLM.
- Bước 3 — Bắt đầu title generation (concurrent): Fire-and-forget một asyncio task gọi cheap model để đặt tên task. Task này chạy song song với main loop iteration đầu tiên — khi main loop finish iteration, title đã sẵn sàng.
- Bước 4 — LLM tool-call loop (max MAX_ITERATIONS lần): Mỗi iteration: refresh memory content từ ArtifactBuffer (nếu set_memory đã chạy ở iteration trước), compact history nếu cần (xem §5.2 context compaction), xây payload = history prefix + context block mới nhất, stream LLM call, yield text/thinking events về client, collect tool calls. Sau stream: persist assistant message vào DB, execute tool calls (theo batches), persist tool results. Nếu không có tool calls → iteration kết thúc → main loop done. Nếu có rejection trong ask mode → flush artifacts + done.
- Bước 5 — Kết thúc turn: Flush ArtifactBuffer (lưu tất cả files đã stage xuống DB), remap artifact ownership về final assistant message, finalize title (emit `task_meta` nếu title changed), yield `stream_done`.

**5.3 Sub-agent loop (`agent_loop.py`):**
Loop chạy trong một lần `spawn_agent` tool call. Khác với main loop ở những điểm then chốt:
- Không persist messages vào DB (giữ history trong memory-only list)
- Không yield SSE trực tiếp — events được forward qua callback `onEvent` về spawn.py → main loop emit
- Có internal timeout (18 phút) tạo bằng `asyncio.wait_for` hoặc asyncio.Event với separate abort controller
- Khi kết thúc, trả về `AgentRunResult` (output string, toolsUsed list, iterations count, timedOut flag)
- Nếu bị abort (parent signal), set `timedOut=True` và trả về partial output thay vì raise exception

**5.4 spawn.py — spawn_agent tool:**
Đây là cầu nối giữa main loop và agent loop. Khi main loop gọi `spawn_agent`, spawn.py thực hiện:
- Lookup agent definition từ registry theo tên
- Resolve tool list cho agent (AGENT_TOOLS subset, lọc theo frontmatter allowlist/disallowlist)
- Nếu mode=ask: wrap từng non-safe tool bằng `withGate()` — transparent wrapper làm tool đó pause để hỏi user approve trước khi execute. Read-only tools bypass gate.
- Emit `agent_start` event
- Gọi `agent_run()`, forward events qua callback
- Sau khi agent xong: parse Status/Summary từ output, emit `agent_done`
- Persist activities JSON vào AgentRun model (upsert bằng messageId+callId)
- Nếu output ≤ 4,000 chars → trả full. Nếu > 4,000 → chỉ trả Status/Summary envelope để tránh blow-up main loop context
- **Recovery on abort:** Nếu parent signal bị abort (stream lock lost, server restart), persist tool result trực tiếp vào DB từ trong spawn.py để task history intact khi client reconnect

**5.5 Auto-title generation (`task_title.py`):**
Chạy concurrent với main loop turn đầu tiên. Dùng cheap/fast model (không phải main model). Ở turns 1–7, model có thể từ chối đặt tên nếu intent chưa đủ rõ (trả `null`). Từ turn 8 (TITLE_FORCE_BY_TURN), model bắt buộc phải đặt tên. Persist title bằng conditional update `WHERE title IS NULL` — đảm bảo user rename không bị overwrite, và concurrent calls không conflict.

**5.6 Parallel tool execution (`exec_parallel.py`):**
Nhận list tool calls từ main loop, partition thành batches (xem partition.py §4.7), execute từng batch. Batch concurrent-safe chạy tối đa MAX_CONCURRENT_TOOLS tool song song. Batch non-safe chạy serial. Collect results, trả về Map keyed by tool_call_id. Handle `overflowAgentIds` (spawn_agent calls vượt MAX_AGENTS_PER_TURN) — những calls này nhận ngay error message, không execute.

### 4.6 ② Agent Registry — Phase 1 Minimal (`packages/agents/src/agents/registry/`)

Agent Registry biến các file markdown thành cấu hình agent chạy được. Thêm agent mới = thêm một file `.md`, không cần thay đổi code.

**6.1 Agent definition schema (`schema.py`):**
Pydantic model `AgentDefinition` map các YAML frontmatter fields: `name` (identifier dùng khi spawn), `displayName` (tên hiển thị trên UI trong agent block), `tools` (list tên tools được phép dùng — nếu empty → dùng full AGENT_TOOLS), `disallowedTools` (explicitly exclude), `maxTurns` (override SUBAGENT_MAX_TURNS), `maxTokens` (override output budget), `model` (override model — null = inherit từ session), `temperature`, và `prompt` (body của .md file sau frontmatter — injected vào context của agent).

**6.2 Registry loader (`loader.py`):**
`load_agent_registry()` scan thư mục `prompts/agents/*.md`, parse YAML frontmatter của từng file, validate schema, trả về list AgentDefinition. `load_system_prompt(variant)` load `prompts/system/system-main.md` hoặc `system-agent.md`. `load_workflow(type, phase)` load `prompts/workflows/{type}/{phase}.md`. Tất cả đều có in-memory cache keyed by file path + mtime — hot reload tự động khi file đổi (dev convenience).

**6.3 Phase 1: chỉ cần load `dashboard-planner.md`.**
Các agents còn lại (data-binder, layout-designer, builder, critic) sẽ được thêm vào Phase 2. Registry loader không cần thay đổi code khi thêm agents.

### 4.7 ④ Tool System — Phase 1 Basic (`packages/agents/src/agents/tools/`)

**7.1 Tool registry và tiers (`registry.py`):**
Single source of truth cho việc phân loại tools. Có 6 tiers phân cấp:
- `READ_ONLY_TOOLS`: Các tool không thay đổi state (read_file, list_file). Tự động bypass ask-mode gate — không cần user approve.
- `ASK_BYPASS`: Bao gồm READ_ONLY_TOOLS + ask_user, spawn_agent, set_memory. Những tools này không hiện Y/N approval card trong ask mode vì bản thân chúng đã là interaction (ask_user) hoặc điều phối (spawn_agent, set_memory).
- `VISIBLE_TOOLS`: Tools hiển thị activity row trên UI (write_file, edit_file, spawn_agent, ask_user). Internal tools không hiện.
- `CONCURRENT_SAFE`: Tools an toàn chạy song song (READ_ONLY_TOOLS + ask_user). spawn_agent không concurrent vì mỗi spawn là full LLM loop.
- `MAIN_TOOLS`: Full tool set cho main loop (bao gồm spawn_agent, ask_user, set_memory).
- `AGENT_TOOLS`: Subset cho sub-agent (không có spawn_agent để ngăn đệ quy, không có ask_user vì agent headless, không có set_memory vì FSM chỉ main loop control).

**7.2 Loop detection (`loop_detection.py`):**
`LoopDetector` class track lịch sử tool calls trong một iteration window. Nếu cùng một tool call (tên + args identical) lặp lại ≥ 3 lần → warn (inject warning vào tool result). Lặp ≥ 5 lần → block (trả error message, không execute). Sliding window đảm bảo detect loop ngay cả khi xen kẽ với calls khác.

**7.3 Read cache (`read_cache.py`):**
`ReadCache` class dedup read operations trong cùng một run. Nếu `read_file("spec.md")` được gọi 3 lần trong cùng một turn và file không bị thay đổi → chỉ đọc disk/DB lần đầu, lần sau trả từ cache. Invalidate cache khi `write_file` hoặc `edit_file` được gọi lên cùng path.

**7.4 Batch partitioning (`partition.py`):**
`partition_batches()` nhận list tool calls, chia thành batches để optimize parallel execution. Thuật toán: duyệt linear, nếu call hiện tại là CONCURRENT_SAFE và batch cuối cùng cũng là CONCURRENT_SAFE → merge vào batch đó. Ngược lại → tạo batch mới serial. Điều này đảm bảo: read-only calls nhóm chạy song song, write/spawn calls chạy serial. Single source of truth dùng cho cả main loop lẫn agent loop.

**7.5 Phase 1 tool implementations (`packages/tools/src/tools/file/`):**
- `read_file.py`: Đọc file từ workspace của task. Validate path không có traversal sequences (`../`). Tra cứu trong File model theo (task_id, name). Nếu không tìm thấy → trả error message rõ ràng thay vì exception.
- `write_file.py`: Ghi file vào workspace. Stage vào ArtifactBuffer thay vì ghi thẳng DB. Emit `file_artifact` SSE event ngay lập tức để FE có thể preview file mới (dù chưa flush xuống DB). Invalidate ReadCache cho path đó.
- `list_file.py`: List tất cả files trong workspace của task. Trả danh sách name + size + kind + created_at. Không trả content (quá lớn).

### 4.8 ⑧ Artifact System — Phase 1 Basic (`packages/agents/src/agents/artifacts/`)

**8.1 ArtifactBuffer (`buffer.py`):**
Dict in-memory keyed by file name, mỗi entry có `id` (UUID) và `content` (string). Stage thêm/sửa file: `buffer.stage(name, id, content)`. Get content hiện tại (để main loop đọc memory.md freshly): `buffer.get(name)`. Flush: iterate over tất cả entries, gọi `upsert_workspace_file()` cho mỗi entry, xóa buffer sau flush. Buffer được tạo fresh ở đầu mỗi stream, shared giữa stream route và main_run — route có thể flush trong `finally` block kể cả khi stream bị interrupt.

**8.2 File service (`file_service.py`):**
`upsert_workspace_file(db, task_id, name, ...)`: Logic overwrite-by-name ở application layer (không dùng `ON CONFLICT` DB constraint). Tìm file theo (task_id, name) — nếu tồn tại update content/metadata, nếu không tạo mới. `get_artifacts(db, task_id)`: Trả danh sách files workspace. `get_file(db, task_id, name)`: Lấy một file cụ thể.

### 4.9 API Layer — Phase 1 (`apps/api/src/api/routes/`)

**9.1 Task CRUD (`routes/tasks.py`):**
Các endpoint chuẩn REST: tạo task + seed memory.md với `type: chat`, list tasks của user, get task detail, rename task (PATCH title), delete task. GET messages trả flat list (Phase 1, chưa cần branch info). GET artifacts trả workspace files.

**9.2 Stream endpoint (`routes/stream.py`):**
`POST /v1/tasks/{id}/stream` là endpoint quan trọng nhất. Luồng:
1. Xác thực ownership (task thuộc về current user)
2. Acquire stream lock → 409 nếu đang chạy
3. Tạo ArtifactBuffer mới (shared với main_run)
4. Tạo RuntimeContext từ request body (mode, user message, parent_id)
5. Start stream: acquire lock → bắt đầu heartbeat background task → gọi `run_task()` → yield SSE events
6. Finally (dù success/error/disconnect): release lock, unregister all gates, cancel heartbeat
`POST /v1/tasks/{id}/stop`: Set abort signal → main loop nhận và dừng lại.

**9.3 Auth endpoints (`routes/auth.py`):**
`POST /v1/auth/login` → validate credentials → generate JWT → set httpOnly cookie. `POST /v1/auth/refresh` → validate refresh token → issue new access token. Phase 1 là single-user JWT, không cần full auth system.

**9.4 LLM budget endpoint:**
`GET /v1/llm/budget` trả JSON chứa tất cả token constants từ `budget.py`. FE dùng để render context donut mà không hardcode numbers.

### 4.10 Definition of Done — Phase 1

Checklist phải PASS toàn bộ trước khi bắt đầu Phase 2. Không có ngoại lệ.

- [ ] 1. `docker compose up` → cả 3 services (postgres, redis, minio) healthy, không crash sau 30 giây
- [ ] 2. `POST /v1/auth/login` với credentials hợp lệ → nhận JWT cookie; gọi protected endpoint không có cookie → 401
- [ ] 3. `POST /v1/tasks` → task được tạo trong DB với status=active, type=null, title=null; workspace file `memory.md` được tạo với `type: chat`
- [ ] 4. `POST /v1/tasks/{id}/stream` với user message → nhận SSE events bao gồm ít nhất một `main_text` event
- [ ] 5. Main loop gọi `spawn_agent("dashboard-planner")` → nhận sequence `agent_start` → một hoặc nhiều `agent_tool`/`agent_result` → `agent_done` với status "done"
- [ ] 6. Dashboard planner gọi `write_file("spec.md")` → nhận `file_artifact` event với name="spec.md" và content
- [ ] 7. Sau khi stream kết thúc, `GET /v1/tasks/{id}/messages` → trả message list bao gồm cả user message và assistant message; agent activities visible trong response
- [ ] 8. `GET /v1/tasks/{id}/artifacts` → trả danh sách files bao gồm spec.md với content đúng
- [ ] 9. `POST /v1/tasks/{id}/stop` trong khi stream đang chạy → stream dừng lại, `stream_done` được emit, lock được release
- [ ] 10. Gửi `POST /v1/tasks/{id}/stream` khi task đang stream → nhận 409 "Task is already being processed"
- [ ] 11. Đóng browser/ngắt kết nối client khi stream đang chạy → LLM KHÔNG bị cancel, khi reconnect vẫn thấy message được persist đầy đủ
- [ ] 12. `GET /v1/llm/budget` → trả JSON object với các keys: `contextWindow`, `inputBudgetTokens`, `microCompactFraction`, `summaryCompactFraction`
- [ ] 13. Sau turn 1, task có title được set (có thể cần turn 8 với TITLE_FORCE)

---

## 5. Track A — Phase 2: Full 5-Agent Dashboard Pipeline

> **Mục tiêu:** Dashboard workflow đầy đủ hoạt động end-to-end: từ yêu cầu ngôn ngữ tự nhiên đến file `page.tsx` deployable. HITL gates cho ask mode. Context compaction để xử lý conversations dài. Artifact buffer production-safe.
>
> **Deliverable cuối phase:** User nói "tạo dashboard doanh thu theo khu vực" → 5 agents chạy tuần tự → spec.md, bindings.md, layout.md, page.tsx, review.md → nếu critic pass thì dashboard sẵn sàng preview.
>
> **Phụ thuộc:** Phase 1 Done hoàn toàn (tất cả 13 checklist items pass).

### 5.1 ③ Memory System (`packages/agents/src/agents/memory/`)

Memory System là bộ não workflow của task — nó lưu trạng thái hiện tại của task (đang ở phase nào) và inject workflow instructions vào payload LLM mỗi turn.

**1.1 FSM state machine (`state_machine.py`):**
`WorkflowFSM` enforce các transitions hợp lệ. Transitions được hardcode trong `ALLOWED_TRANSITIONS` dict: từ empty → `create-chat` hoặc `create-dashboard`; từ `create-chat` → `create-dashboard`; từ `create-dashboard` → `edit-dashboard` hoặc `repair-dashboard`; từ `repair-dashboard` → `create-dashboard` hoặc `edit-dashboard`; từ `edit-dashboard` → `edit-dashboard` hoặc `repair-dashboard`. Khi agent cố chuyển sang phase không hợp lệ (ví dụ từ `edit-dashboard` về `create-chat`) → raise ValueError với message rõ ràng. Transition rules không nằm trong prompt — nằm trong code để không thể bị "convince" bởi LLM.

**1.2 memory.md file handling (`memory_file.py`):**
`read_memory(db, task_id)` đọc file `memory.md` từ workspace, parse YAML frontmatter, trả về `MemoryState(type, phase)`. `write_memory(db, task_id, type, phase, artifact_buffer)` cập nhật memory.md, stage vào ArtifactBuffer (không ghi DB ngay — để main loop thấy thay đổi ngay iteration tiếp theo mà không cần DB round-trip), đồng thời load và trả về workflow content tương ứng từ `prompts/workflows/{type}/{phase}.md`.

**1.3 Context block builder (`context_block.py`):**
`build_context_block(memory_content, user_instructions)` tạo một LLM message đặc biệt inject vào CUỐI payload mỗi turn. Nội dung gồm 3 phần theo cấu trúc markdown: `# MEMORY` (nội dung memory.md hiện tại — type + phase), `# USER` (user preferences/instructions nếu có), `# WORKFLOW` (nội dung file workflow của phase hiện tại). Message này không bao giờ được lưu vào mảng `messages` — được rebuild fresh mỗi iteration để phản ánh state mới nhất. Điều này giữ history prefix ổn định (cache-friendly).

**1.4 set_memory tool (`packages/tools/src/tools/orchestration/set_memory.py`):**
Tool này là gateway duy nhất để thay đổi workflow state. Khi LLM gọi `set_memory(type, phase)`: validate cả hai fields không rỗng, đọc memory.md hiện tại, validate transition qua FSM, write memory.md mới (và stage vào ArtifactBuffer), sync `Task.type` trong DB nếu type thay đổi (conditional UPDATE để không overwrite nếu đã là production type), emit `task_meta` SSE nếu type changed (FE cần update task header), trigger `nameTaskIfUntitled()` fire-and-forget nếu task vẫn chưa có tên. Cuối cùng: load và return workflow file content — LLM nhận workflow instructions trực tiếp như tool result, không cần read_file riêng.

**1.5 Task.type sync:**
Khi memory.md type upgrade từ `chat` → `dashboard`, cần sync column `Task.type` trong DB. Dùng conditional UPDATE: `WHERE id = task_id AND (type IS NULL OR type = 'chat')` — đảm bảo không downgrade type đã là production.

### 5.2 ② Agent Registry — Full 5 Agents

**2.1 5 specialist agent files:**
Tạo 5 file markdown trong `prompts/agents/`:

- `dashboard-planner.md`: Nhận user intent → phân tích và output `spec.md` với danh sách widgets, metrics cần thiết, filters, layout hints. Agent này cần tools: read_file (đọc context), write_file (ghi spec.md). maxTurns: 20. Output phải conform `DashboardSpec` schema.

- `data-binder.md`: Đọc spec.md → map từng metric sang query/API binding → output `bindings.md`. Cần hiểu schema của data source (Phase 1: mock schema hardcoded trong prompt; Phase 2: có thể dùng schema_inspector tool). Agent này validate grounded generation — không được bịa metric không có trong schema.

- `layout-designer.md`: Đọc spec.md + bindings.md → design grid layout responsive → output `layout.md` với positions, sizes, breakpoints cho từng widget. Biết về Recharts component types và sizing constraints.

- `dashboard-builder.md`: Đọc spec.md + bindings.md + layout.md → sinh ra file `page.tsx` (React component) và các widget files. Đây là agent nặng nhất — cần maxTurns cao nhất và có thể maxTokens lớn hơn default.

- `dashboard-critic.md`: Đọc tất cả output files → validate spec compliance, a11y basics, grounded claims (không có widget bind metric không tồn tại trong bindings.md), render sanity check → output `review.md` với status PASS hoặc FAIL kèm list issues cần fix.

**2.2 Workflow files:**
Tạo 4 workflow files trong `prompts/workflows/`:

- `dashboard/create-dashboard.md`: Mô tả spawn sequence cho orchestrator: bước 1 spawn planner, bước 2 spawn binder, bước 3 spawn designer, bước 4 spawn builder, bước 5 spawn critic. Mỗi bước có acceptance criteria — orchestrator check output trước khi spawn bước tiếp theo. Nếu critic FAIL → chuyển sang repair workflow.

- `dashboard/edit-dashboard.md`: Cho phép edit dashboard đã có. Planner đọc spec cũ + user request → output updated spec → pipeline tiếp tục từ binder.

- `dashboard/repair-dashboard.md`: Đọc review.md với danh sách issues → tùy độ nghiêm trọng: repair minor issues tại chỗ (builder chỉnh sửa) hoặc restart từ planner nếu fundamental issues.

- `chat/create-chat.md`: Free-form conversation, thu thập thông tin về dashboard user muốn build trước khi trigger create-dashboard workflow.

### 5.3 ① Orchestration — Full Pipeline

**3.1 Workflow execution engine (`workflow.py`):**
Khi Memory FSM chuyển sang phase `create-dashboard`, thay vì để main loop spawn agent tùy ý, `workflow.py` take over và chạy deterministic pipeline. Workflow engine đọc `create-dashboard.md` workflow file, parse spawn sequence, execute từng bước tuần tự: spawn planner → đợi kết quả → validate acceptance criteria → nếu pass spawn binder → ... → spawn critic → đọc review.md → nếu FAIL chuyển sang repair workflow. Acceptance criteria validation là check đơn giản (file tồn tại? Status là DONE? Summary không chứa lỗi nghiêm trọng?), không dùng LLM để validate (tránh không deterministic).

**3.2 LLM recovery paths (`recovery.py`):**
`append_recovery_messages(messages, text, thinking, ...)` inject một cặp messages (assistant partial + user continuation prompt) vào mảng messages để retry. Mỗi failure mode có recovery message riêng: với max_tokens (bị cắt giữa chừng) → inject "please continue from where you left off"; với empty response → inject "please respond to the request"; với thinking-only → inject "please include your response text". Recovery injection không thay đổi MAX_ITERATIONS counter — chỉ tăng counter riêng của từng path.

**3.3 exec_parallel.py — Full implementation:**
Bổ sung so với Phase 1: xử lý `overflowAgentIds` (đếm spawn_agent calls, những calls vượt MAX_AGENTS_PER_TURN nhận error message thay vì execute), `TOOL_REJECTED_RESULT` sentinel string dùng khi user reject một tool call trong ask mode (main loop detect sentinel này để dừng loop ngay sau flush artifacts).

### 5.4 ④ Tool System — Full Execution Pipeline

**4.1 Full tool execution pipeline (`pipeline.py`):**
Thay vì execute tool trực tiếp như Phase 1, mọi tool call đều phải qua pipeline 6 bước theo thứ tự cố định:

- **Bước 1 — Validate args:** Parse tool arguments theo JSON Schema của tool (mỗi tool khai báo `parameters` JSON Schema). Nếu args invalid → return error envelope ngay, không execute.
- **Bước 2 — Loop detection:** Check LoopDetector. Nếu warn level → inject warning vào result nhưng vẫn execute. Nếu block level → return block error, không execute.
- **Bước 3 — Read cache dedup:** Nếu tool là READ_ONLY và đã có cache hit cho (tool_name, args) → trả cached result, không execute.
- **Bước 4 — Gate (ask mode):** Nếu mode=ask và tool không trong ASK_BYPASS → khởi tạo gate, emit `main_tool` event, block đợi user decision. Nếu rejected → trả TOOL_REJECTED_RESULT sentinel. Nếu approved → tiếp tục.
- **Bước 5 — Execute:** Gọi `tool.execute(args, tool_ctx)`. Wrap trong try/except để bất kỳ exception nào cũng được convert thành error envelope thay vì crash stream.
- **Bước 6 — Truncate result:** Cap kết quả theo `TOOL_RESULT_MAX_CHARS` (per-tool cap) và `HISTORY_CAP_CHARS` (history total cap). Kết quả quá dài sẽ gây context overflow ở turns sau.

**4.2 Bổ sung tool implementations (Phase 2):**
- `file/edit_file.py`: Patch một portion của file workspace thay vì overwrite toàn bộ. Hữu ích khi agent chỉ muốn sửa một widget trong page.tsx mà không rebuild từ đầu.
- `orchestration/set_memory.py`: Đã mô tả ở §5.1.4.
- `orchestration/ask_user.py`: Trigger ask gate — emit `main_ask` SSE với câu hỏi, block đợi user submit answer qua `POST /gates/ask`, trả answer về LLM như tool result.
- `data/schema_inspector.py`: Phase 2 dùng mock schema hardcoded, Phase 3+ thay bằng real DB introspection.
- `data/csv_preview.py`: Parse CSV file từ upload, infer schema, trả preview data.

### 5.5 ⑤ Context System — Full Compaction

**5.1 History builder (`history.py`):**
`build_history(path)` nhận danh sách messages theo tree path (từ root đến leaf), convert thành `list[LLMMessage]` đúng format provider. Xử lý các roles: user message → text content, assistant message với tool calls → tool_calls format, tool result → role=tool content, compact message → được xử lý đặc biệt (không hiện trong history, chỉ boundary marker). `build_compact_summary_message(summary)` tạo một user message với nội dung summary — message này được prepend vào đầu list như "leading user message" (Claude layout — model đọc summary trước khi đọc recent history).

**5.2 Two-tier compaction (`compaction.py`):**
`compact_if_over_budget()` là function được gọi đầu mỗi iteration của main loop. Logic:
- Tính `currentInputTokens()` bằng cách cộng `lastRealPromptTokens` (exact từ provider call gần nhất) với estimated tokens của messages mới append từ đó (dùng calibrated `tokensPerChar` ratio).
- Nếu ≤ `microAtTokens` (60% budget) → không cần compact, return.
- **Tier 1 Microcompact:** Scan messages array, xóa content của old tool result messages (các message có role=tool ở nửa đầu history, chỉ giữ placeholder). Cheap, in-memory, không cần LLM. Có thể giải phóng 20–40% tokens.
- Nếu sau tier 1 vẫn > `compactAtTokens` (80% budget): **Tier 2 Summary compact:** Reload full message path từ DB, xác định split point (keep 40,000 tokens gần nhất), gọi cheap LLM model để summarize phần cũ, persist summary message vào DB với role=compact, rebuild messages array từ kept tail + summary prepended. Đắt hơn (cần LLM call) nhưng giải phóng nhiều hơn.
- `compactionExhausted` flag: Nếu sau compact kept tail vẫn > budget → set flag, không compact thêm trong turn này (tránh thrashing).

**5.3 Token accounting calibration (`accounting.py`):**
`estimate_chars(messages)` tính tổng chars của messages list (text content + tool call JSON + thinking). `calibrate_tokens_per_char(real_prompt_tokens, messages)` tính lại tỉ lệ sau khi có real measurement: `ratio = real_tokens / estimated_chars_at_send`. Ratio mới được dùng cho delta estimation các messages thêm sau đó. Giá trị khởi tạo `INITIAL_TOKENS_PER_CHAR = 0.34` được tune cho Vietnamese (conservative — overestimate để compact sớm hơn overflow).

**5.4 Thinking codec (`thinking_codec.py`):**
Extended thinking blocks (text + signature + redacted) cần được serialize để lưu vào DB column `Message.thinking` (string). `encode_thinking()` convert từ structured object sang JSON string. `decode_thinking()` convert ngược lại. Cần thiết khi load history — messages có thinking phải được reconstruct đúng format provider khi gửi lại trong context.

**5.5 Manual compact API:**
`POST /v1/tasks/{id}/compact` cho phép user manually trigger summary compact bất kỳ lúc nào (không cần đợi 80% threshold). Useful khi user muốn "reset" một conversation dài trước khi tiếp tục. Response trả summary được tạo ra.

### 5.6 ⑦ Gate System — Full HITL (`packages/agents/src/agents/gates/`)

Gate System là cơ chế cho phép user kiểm soát từng tool call của agent trong ask mode. Đây là "human in the loop" mechanism.

**6.1 Gate service (`gate_service.py`):**
Core của hệ thống là Redis-backed polling mechanism. Luồng hoạt động:

- Bước 1 — `init_gate(task_id, call_id)`: SET Redis key `gate:{task_id}:{call_id}` = "pending" với NX flag (không overwrite nếu đã tồn tại). Bước này phải xảy ra TRƯỚC khi emit SSE event về client. Nếu client respond quá nhanh trước khi gate được init, response sẽ bị miss.
- Bước 2 — Emit `main_tool` SSE event về client → FE hiển thị Y/N approval card.
- Bước 3 — `register_gate(task_id, call_id, signal)`: Poll Redis key mỗi 300ms + random jitter (tránh thundering herd). Nếu key = "pending" → tiếp tục poll. Nếu key = "approved"/"rejected" → resolve. Nếu key không tồn tại (expired TTL) → resolve as rejected. Nếu Redis liên tục lỗi 10 lần → fail-safe unblock (không treo stream).
- Bước 4 — User click approve/reject trên FE → `POST /gates/tool` → `resolve_gate(task_id, call_id, decision, feedback)`: Dùng Lua atomic script `SET_IF_PENDING` — chỉ set value nếu current value = "pending". Điều này ngăn double-approve (hai requests concurrent cùng approve một gate).

Feedback mechanism: Khi user reject với feedback text → feedback được inject vào tool result content của LLM (LLM thấy lý do reject và có thể điều chỉnh cách tiếp cận). Khi user approve với feedback → feedback được append vào tool result sau execution.

**6.2 Ask gate (separate namespace):**
Tương tự tool gate nhưng dùng namespace `ask:{task_id}:{call_id}`. `ask_user` tool trigger ask gate — emit `main_ask` SSE với câu hỏi, block đợi user submit text answer. Khi user submit qua `POST /gates/ask` → store answer trong Redis, `register_ask_gate` unblock, trả answer về LLM như tool result.

**6.3 Gate cleanup:**
`unregister_all_gates(task_id)` được gọi trong `finally` block của stream route. Scan Redis tất cả keys matching `gate:{task_id}:*` và `ask:{task_id}:*` → xóa tất cả. Ngăn orphan gate keys khi stream kết thúc đột ngột.

**6.4 In-memory fallback cho dev:**
Khi không có Redis (dev mode không cần cài Redis full), gate service dùng dict singleton trên module global. Cần persist dict vào `globalThis` equivalent trong Python (module-level singleton) để survive hot-reload.

### 5.7 ⑧ Artifact System — Production Buffer

**7.1 ArtifactBuffer nâng cấp:**
Bổ sung method `flush_and_remap(db, task_id, tool_call_msg_ids, final_message_id, run_started_at)`: sau khi main loop kết thúc turn, remap tất cả files được tạo trong turn này về `final_message_id` (assistant message cuối cùng của turn). Điều này đảm bảo files được link đúng về message và hiển thị đúng trong UI (canvas show files linked với assistant message, không phải tool messages).

**7.2 File upload endpoint:**
`POST /v1/tasks/{id}/upload` cho phép user attach files vào task. Validation: whitelist MIME types (text/csv, application/json, image/png, image/jpeg, application/pdf), size cap 10MB. Path traversal prevention: strip `../`, `/`, `\` khỏi filename. Task ownership verification: reject nếu task không thuộc user hiện tại. Uploaded files có `source: upload` để phân biệt với workspace files.

### 5.8 ⑨ Streaming — Full Guards

**8.1 Production resilience guards bổ sung:**
- **Pending message reuse:** Trước khi main loop tạo user message, check xem task có "orphan" user message nào không (user message không có assistant response — do crash trước lần run trước). Nếu có và nội dung giống request hiện tại → reuse message ID, không tạo mới.
- **5-second dedup:** Track recent (task_id, content_hash, timestamp) tuples. Nếu exact same request trong 5s → return 200 OK với `message: "deduplicated"` mà không gọi LLM.
- **Safety-net orphan lock monitor:** Background asyncio task scan periodically cho locks không được refresh (heartbeat stopped) → abort và cleanup.
- **Stop handshake:** `POST /stop` không chỉ set abort signal mà còn: đợi main loop acknowledge abort, flush artifact buffer (giữ lại work đã làm), tạo partial assistant message trong DB, return `partial_message_id` để FE reload.

**8.2 Rate limiting (Redis buckets):**
5 rate limit buckets riêng biệt với token bucket algorithm trong Redis: `task_stream` (100 requests/giờ/user), `task_create` (30 tasks/giờ/user), `upload` (30 uploads/giờ/user), `dashboard_create` (20 dashboards/ngày/user — trigger khi set_memory type=dashboard), `global` (1000 requests/phút toàn hệ thống). Khi bị rate limit: trả 429 với headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

### 5.9 ⑩ Persistence — Message Tree Branching

**9.1 Message tree branching:**
Phase 2 enable full tree structure. Khi user regenerate một assistant message hoặc edit một user message: thay vì overwrite, tạo message mới với cùng `parent_id` — tạo nhánh mới từ điểm đó. FE có thể navigate giữa các nhánh (sibling messages). `GET /messages` trả messages kèm `branch_info` field cho mỗi message có siblings (số nhánh, index nhánh hiện tại). Message role `compact` là boundary — messages trước compact boundary được "ẩn" trong UI (không xóa, chỉ không hiển thị — tránh mất dữ liệu).

**9.2 AgentRun reload cho UI:**
`GET /tasks/{id}/messages` bao gồm, cho mỗi assistant message có tool call spawn_agent, danh sách AgentRun records của message đó. FE dùng `activities` JSON để reconstruct agent activity timeline (xem lại những gì agent đã làm trong một session cũ).

### 5.10 Definition of Done — Phase 2

- [ ] 1. Gửi "tạo dashboard doanh thu theo khu vực" → `set_memory({type: dashboard, phase: create-dashboard})` được gọi → workflow file được inject → 5 agents spawn tuần tự
- [ ] 2. Mỗi agent ghi đúng output file: planner → spec.md, binder → bindings.md, designer → layout.md, builder → page.tsx, critic → review.md
- [ ] 3. dashboard-critic trả FAIL → orchestrator tự động chuyển sang repair-dashboard workflow và retry
- [ ] 4. Bật ask mode → agent gọi `write_file` → `main_tool` event xuất hiện trên UI → user click Approve → file được ghi, stream tiếp tục
- [ ] 5. Agent gọi `ask_user("bạn muốn dùng loại chart nào?")` → `main_ask` event → user submit answer → agent nhận answer và tiếp tục
- [ ] 6. Conversation đủ dài → context tự động microcompact khi vượt 60%; tự động summary compact khi vượt 80%; `POST /compact` hoạt động manually
- [ ] 7. User cancel stream giữa lúc builder đang viết page.tsx → file KHÔNG xuất hiện trong artifacts (phantom file prevention)
- [ ] 8. `POST /stop` → nhận `stream_done` với partial_message_id; `GET /artifacts` trả files đã được flush trước khi stop
- [ ] 9. Rate limit: send >100 stream requests trong 1 giờ → nhận 429 với đúng headers
- [ ] 10. Regenerate assistant message → tạo nhánh mới; `GET /messages` trả branch_info; có thể switch giữa nhánh
- [ ] 11. `GET /messages` của task đã có agent run → trả activities timeline cho mỗi spawn
- [ ] 12. Sub-agent gọi write_file trong ask mode → Y/N card xuất hiện ở cấp task (không phải cấp agent block)
- [ ] 13. Nếu stream lock bị mất (simulate server restart) → partial agent result được persist, task history intact khi reload
- [ ] 14. Loop detection: agent gọi cùng read_file 3 lần → warn; 5 lần → block với message rõ ràng
- [ ] 15. Upload file CSV → xuất hiện trong artifacts với source=upload

---

## 6. Track A — Phase 3: Production Hardening

> **Mục tiêu:** Hardening toàn bộ Agent Core cho production traffic thực. Observability, export, security. **Không có RAG/document** — đó là Track B.
>
> **Phụ thuộc:** Phase 2 Done hoàn toàn.

### 6.1 ⑪ Observability System (`packages/eval/` + infra)

**1.1 Structured logging với structlog:**
Config structlog cho production: JSON renderer (không phải human-readable), processors bao gồm `add_log_level`, `TimeStamper` ISO format, `CallsiteParameterAdder` (ghi file + line vào log). Mọi logger phải bind `task_id` ngay khi bắt đầu xử lý request — tất cả subsequent logs của request đó tự động có correlation. Các log events quan trọng cần có: stream lifecycle (acquire/release lock, start/stop), tool calls (name + args truncated), gate events (init/resolve/timeout), compaction (tier triggered, chars saved), agent runs (start/done/timeout), LLM calls (model, tokens, duration).

**1.2 OpenTelemetry distributed tracing:**
Khởi tạo OTEL tracer trong `apps/api`. Instrument các spans quan trọng: `run_task` (span cho toàn bộ một user turn, attributes: task_id, user_id, mode, iteration_count), `main_loop_iteration` (per-iteration span, attributes: iteration_number, tool_count), `spawn_agent` (per-agent span, attributes: agent_name, tools_used, iterations, timed_out), `tool_execute` (per-tool span, attributes: tool_name), `gate_wait` (span đo thời gian user mất để approve/reject), `compact_history` (span cho tier-2 compaction, attributes: tier, tokens_before, tokens_after). Export sang Jaeger/Tempo cho local dev, OTLP endpoint cho production.

**1.3 Eval golden sets (`packages/eval/`):**
Tập test cases với expected outputs để chạy CI regression. Hai loại:
- **Spec validity tests:** Input các dashboard descriptions khác nhau → chạy qua planner agent → assert output spec.md conform DashboardSpec Pydantic schema, có đủ widgets field, metrics field non-empty.
- **Render success tests:** Input spec.md + bindings.md fixtures → chạy builder agent → assert page.tsx có valid syntax (dùng `ast` module hoặc babel parse), không có undefined imports, widget names khớp spec.
- **Prompt regression tests:** Input fixed prompts → assert agent output có đúng `**Status:** DONE` format, Summary ≤ 2000 chars, không có lỗi "ToolNotFound".
CI gate trong GitHub Actions: fail build nếu bất kỳ test nào fail.

### 6.2 Export System

**2.1 Generated page export:**
Agent builder output là `page.tsx` + widget files trong workspace. Export API đóng gói chúng thành downloadable zip: `GET /v1/tasks/{id}/export/zip` → stream zip file chứa tất cả workspace files của task. Trước khi export: validate DashboardSpec một lần nữa (fail-closed — nếu invalid spec thì reject export). User có thể download zip và deploy independently.

**2.2 Schema validation fail-closed:**
Nếu DashboardSpec Pydantic parse fail → không render, không export, return lỗi rõ ràng. Nếu page.tsx syntax check fail → critic FAIL → repair workflow. Không cho phép invalid output thoát ra ngoài pipeline.

### 6.3 Security Hardening

**3.1 Upload file validation:**
MIME type whitelist: chỉ cho phép text/csv, application/json, image/png, image/jpeg, application/pdf (Phase 3 thêm PDF cho Track B prep). Size cap 10MB. Filename sanitization: strip control characters, null bytes, path separators. Content-Type header từ browser không đáng tin — verify bằng magic bytes (file signature) thay vì chỉ dựa vào MIME.

**3.2 Task ownership enforcement:**
Dependency function `verify_task_ownership(task_id, user_id, db)` phải được gọi ở đầu mọi route handler liên quan đến task: stream, stop, gates, artifacts, upload, export. Nếu task.user_id ≠ current_user.id → 403 Forbidden.

**3.3 Path traversal prevention:**
Function `has_path_separator(value)` check path/filename không chứa `../`, `./`, `/`, `\`. Áp dụng cho: file names trong workspace, agent names, phase names từ set_memory, path parameter trong spawn_agent.

**3.4 Rate limit production tuning:**
Sau khi có production traffic data, review rate limit thresholds. Có thể cần tăng `task_stream` cho power users hoặc giảm `dashboard_create` nếu agent pipeline tốn nhiều compute.

### 6.4 Definition of Done — Phase 3

- [ ] 1. Tất cả logs có correlation `task_id` — có thể search theo task_id trong log aggregator
- [ ] 2. OTEL trace visible cho full create-dashboard workflow: từ `run_task` đến 5 agent spans đến `stream_done`
- [ ] 3. Eval CI fail khi DashboardSpec invalid hoặc page.tsx syntax broken
- [ ] 4. Export zip chứa valid page.tsx có thể import vào React app
- [ ] 5. Upload file với forbidden MIME type → 400 Bad Request
- [ ] 6. User A call `GET /tasks/{id}/artifacts` với task_id của User B → 403 Forbidden
- [ ] 7. Path traversal attack trong file name (`../../etc/passwd`) → sanitized/rejected
- [ ] 8. Eval golden set: planner output spec với 10 different dashboard descriptions → tất cả conform schema

---

## 7. Track B — Phase 4: RAG Foundation

> **Mục tiêu:** Dựng infrastructure RAG để xử lý và index tài liệu do user upload. Phase này là "foundation" — chưa integrate với agent dashboard workflow.
>
> **Điều kiện bắt đầu:** Track A (Phase 1 + 2 + 3) PHẢI hoàn chỉnh và stable. Không bắt đầu Track B khi Track A còn bugs hoặc incomplete features.
>
> **Lý do tách biệt:** Agent Core và Document Intelligence là hai concerns hoàn toàn khác nhau. Track A dạy agent biết tạo dashboard. Track B dạy agent biết đọc tài liệu. Trộn lẫn sẽ làm phức tạp debugging và testing.

### 7.1 Document Ingestion Pipeline

**1.1 Supported document types:**
Phase 4 hỗ trợ các loại tài liệu phổ biến nhất của business users: PDF (báo cáo, analysis), Excel/XLSX (bảng dữ liệu, financial data), CSV (exported data), Word/DOCX (reports với narrative), Markdown. Mỗi loại cần extractor riêng để xử lý structure đặc thù.

**1.2 PDF extractor:**
Dùng `pdfplumber` hoặc `pymupdf` để extract text có cấu trúc từ PDF. Xử lý: text trực tiếp (bao gồm tables as markdown), hình ảnh trong PDF (skip hoặc OCR nếu có pytesseract), headers/footers (detect và loại bỏ hoặc label riêng), multi-column layout (maintain reading order). Output: list of `DocumentChunk(text, page_number, section_header, chunk_index)`.

**1.3 Excel/XLSX extractor:**
Dùng `openpyxl` để đọc workbooks. Với mỗi sheet: detect header row (first row với text labels), convert tabular data thành markdown table format (dễ đọc cho LLM), detect nếu sheet là time series data (date column + numeric columns). Metadata: sheet name, total rows, column names, data types. Mỗi sheet là một chunk riêng, bổ sung context về sheet purpose từ sheet name.

**1.4 Chunking strategy:**
Sau khi extract raw text, chia thành chunks để embed. Chunking rules: chunk size target = 400–600 tokens (đủ để có context, không quá lớn), overlap = 50 tokens giữa chunks liên tiếp (tránh mất context ở boundary), preserve section boundaries (không cắt giữa bảng hoặc heading), table/chart captions giữ nguyên không cắt. Mỗi chunk được annotate với metadata: document_id, page_number, section_header, chunk_index.

**1.5 Upload endpoint bổ sung cho Track B:**
`POST /v1/tasks/{id}/documents` — nhận file tài liệu, validate type và size (limit cao hơn: 50MB cho PDF lớn), trigger async ingestion pipeline. Trả `document_id` ngay lập tức, ingestion chạy background. `GET /v1/tasks/{id}/documents/{doc_id}/status` cho phép FE poll trạng thái ingestion (pending → extracting → embedding → ready → error).

### 7.2 Vector Storage (`packages/rag/`)

**2.1 Vector store setup:**
Bổ sung Qdrant vào Docker Compose. Tạo collection riêng cho document embeddings: `documents` collection với vector dimension theo embedding model (1536 cho OpenAI text-embedding-3-small, 768 cho Ollama nomic-embed-text). Mỗi vector có payload: `{document_id, task_id, chunk_text, chunk_index, page_number, section_header, document_name, document_type}`.

**2.2 Embedding pipeline:**
Embedding service nhận chunks, gọi embedding API (OpenAI text-embedding-3-small cho production, nomic-embed-text qua Ollama cho dev), batch calls để giảm latency và cost (OpenAI cho phép batch 100 texts per call), store vectors vào Qdrant. Idempotent upsert: nếu document đã được embed (detect bằng document_id filter), overwrite existing vectors.

**2.3 Multi-tenant isolation:**
Mỗi vector search phải filter theo `task_id` — user không thể search vào tài liệu của task khác. Qdrant filter: `{task_id: {match: {value: current_task_id}}}`. Không dùng separate collections per task (quá nhiều collections, Qdrant có limit), thay vào đó dùng payload filter.

**2.4 Incremental indexing:**
Khi user upload tài liệu mới vào task đang tồn tại, chỉ index tài liệu mới đó — không re-index toàn bộ. Track ingestion status per document trong DB (`Document` model mới với fields: id, task_id, name, status, vector_count, error_message).

### 7.3 Document Search Tool

**3.1 `search_documents` tool:**
Tool mới trong `packages/tools/src/tools/rag/search_documents.py`. Parameters: `query` (natural language search query), `limit` (số kết quả, default 5, max 20), `document_name` (optional: filter theo tên file cụ thể). Implementation: embed query text → search Qdrant với task_id filter → trả top-k chunks với metadata và similarity score. Agent dùng tool này để tìm kiếm thông tin trong tài liệu đã upload trước khi tạo dashboard.

**3.2 Tool tier assignment:**
`search_documents` là READ_ONLY tool (search không modify state). Được add vào `READ_ONLY_TOOLS` set, `CONCURRENT_SAFE` set, `MAIN_TOOLS` và `AGENT_TOOLS` lists. Agents data-binder và dashboard-planner cần được phép dùng tool này trong frontmatter.

**3.3 Result format:**
Mỗi kết quả search trả về: `chunk_text` (nội dung đoạn tìm được), `document_name` (tên file gốc), `page_number` (hoặc sheet name), `section_header`, `score` (similarity score). Kết quả được format thành markdown để LLM dễ đọc. Total result size bị cap (tổng chunks không vượt quá một limit nhất định để tránh blow-up context).

### 7.4 Definition of Done — Phase 4

- [ ] 1. Upload PDF 10MB → ingestion completes within 60 giây → status = ready
- [ ] 2. Upload Excel với 5 sheets → mỗi sheet được index như separate chunks → search có thể find data từ specific sheet
- [ ] 3. `search_documents("doanh thu quý 3")` trên task có document → trả đúng chunks liên quan
- [ ] 4. User A không thể search documents của User B (task_id isolation verified)
- [ ] 5. Upload cùng file 2 lần → second upload overwrite first (idempotent, không duplicate vectors)
- [ ] 6. Document ingestion pipeline fail (corrupted file) → status = error với message rõ ràng, task vẫn usable

---

## 8. Track B — Phase 5: Document-driven Dashboard

> **Mục tiêu:** Tích hợp RAG system vào dashboard creation workflow — agent có thể đọc tài liệu, extract data thực, bind vào widgets thay vì dùng mock data.
>
> **Phụ thuộc:** Phase 4 Done (RAG Foundation stable và tested).

### 8.1 Updated Agent Prompts

**1.1 dashboard-planner.md update:**
Bổ sung instruction cho planner: khi task có documents uploaded, planner phải gọi `search_documents` để hiểu nội dung trước khi propose widgets. Ví dụ: nếu user upload báo cáo doanh thu, planner search "revenue metrics", "time periods", "regions" để biết data có những gì trước khi decide widget types. Planner không được propose metrics không tồn tại trong documents.

**1.2 data-binder.md update:**
Binder được update để support document-sourced data: thay vì chỉ map tới mock schema, binder giờ có thể: (a) map tới dữ liệu extract từ document (trong trường hợp này binding là "document chunk reference"), (b) map tới actual database query (Phase 3 optional SQL connector), hoặc (c) fallback về mock data nếu không tìm được data. Binder phải document rõ trong bindings.md loại binding cho từng widget.

**1.3 document-analyzer.md — Agent mới (optional):**
Agent chuyên đọc và summarize structure của tài liệu upload. Chạy trước planner trong workflow document-driven. Input: danh sách documents của task. Output: `document-summary.md` mô tả: loại tài liệu, structure chính, data tables available, time periods covered, key metrics tìm thấy. Planner đọc file này thay vì tự search từ đầu.

### 8.2 Updated Workflow

**2.1 create-dashboard-from-document.md:**
Workflow mới song song với `create-dashboard.md`. Trigger khi `set_memory({type: dashboard, phase: create-dashboard-from-document})`. Pipeline: (1) document-analyzer summarize tài liệu, (2) planner đọc summary + search thêm nếu cần → spec.md, (3) binder map tới real document data → bindings.md, (4) designer → layout.md, (5) builder → page.tsx dùng document data, (6) critic validate grounded claims (widget data phải trace về document source).

**2.2 FSM update:**
Thêm transition mới vào ALLOWED_TRANSITIONS: `create-chat` → `create-dashboard-from-document`, `create-dashboard-from-document` → `edit-dashboard` | `repair-dashboard`. Phase mới không require tất cả thay đổi — chỉ thêm vào FSM dict và tạo workflow file tương ứng.

**2.3 Grounded generation enforcement:**
`dashboard-critic.md` được update để verify grounded claims cho document-based dashboards. Mỗi widget trong page.tsx phải có thể trace data về specific document chunk trong bindings.md. Nếu critic tìm thấy widget với data không có trong bindings → FAIL với message cụ thể "Widget X: data source not documented in bindings.md".

### 8.3 UI Changes (FE integration points)

**3.1 Document list trong task sidebar:**
FE cần display danh sách documents của task, status ingestion, có thể delete document. Endpoint: `GET /v1/tasks/{id}/documents`.

**3.2 Upload document button:**
Trong chat input area, thêm "Attach Document" button (khác với current file attach cho image/CSV). Trigger `POST /v1/tasks/{id}/documents`.

**3.3 Dashboard canvas citation:**
Khi dashboard được tạo từ tài liệu, widgets trên canvas có citation indicator — hover để xem data từ document chunk nào. FE đọc `bindings.md` để render citations.

### 8.4 Definition of Done — Phase 5

- [ ] 1. User upload báo cáo doanh thu PDF → chat "tạo dashboard từ báo cáo này" → planner tự động search document và propose widgets phù hợp với data thực trong báo cáo
- [ ] 2. page.tsx generated dùng data từ document (không phải mock data)
- [ ] 3. critic verify grounded claims — nếu widget dùng metric không có trong document → FAIL
- [ ] 4. UI hiển thị danh sách documents với status; có thể delete document
- [ ] 5. Canvas widgets có citation linking về document source
- [ ] 6. Workflow `create-dashboard-from-document` hoạt động end-to-end

---

## 9. Dependency Graph tổng thể

```
TRACK A — PHẢI HOÀN THÀNH TRƯỚC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1 (Foundation)
 ├── ⑥ LLM System (no deps)
 ├── ⑩ Persistence System (no deps)
 ├── ⑨ Streaming System core (Redis)
 ├── ⑧ Artifact System basic (no deps)
 └── ① Orchestration minimal
      ├── ② Registry (1 agent)
      └── ④ Tools basic (file only)

Phase 2 (Full Pipeline)       [phụ thuộc Phase 1 done]
 ├── ③ Memory System (FSM)    ──► ① Orchestration (workflow engine)
 ├── ② Registry full (5 agents + workflows)
 ├── ④ Tool pipeline full     ──► ⑦ Gate System (HITL)
 ├── ⑤ Context System (compaction)
 ├── ⑧ Artifact buffer production
 └── ⑨ Streaming guards + rate limits

Phase 3 (Hardening)           [phụ thuộc Phase 2 done]
 ├── ⑪ Observability (logging + traces + eval)
 ├── Export system
 └── Security hardening

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRACK B — CHỈ SAU KHI TRACK A XONG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 4 (RAG Foundation)      [phụ thuộc Track A done]
 ├── Document extraction pipeline
 ├── Qdrant vector store
 ├── Embedding service
 └── search_documents tool

Phase 5 (Doc-driven Dashboard) [phụ thuộc Phase 4 done]
 ├── Updated agent prompts
 ├── New workflow
 └── UI document integration
```

---

## 10. File Map: Plan → Code

### 10.1 packages/agents/ — Subsystem mapping

| File | Phase | Mô tả ngắn |
|------|-------|-----------|
| `orchestration/constants.py` | 1 | Tất cả production constants từ §3 |
| `orchestration/runtime.py` | 1 | RuntimeContext + run_task() entry point |
| `orchestration/main_loop.py` | 1 | Main orchestrator loop (LeadZen main-run.ts ref) |
| `orchestration/agent_loop.py` | 1 | Sub-agent isolated loop (LeadZen agent-run.ts ref) |
| `orchestration/spawn.py` | 1 | spawn_agent tool + withGate pattern |
| `orchestration/task_title.py` | 1 | Auto-title concurrent generation |
| `orchestration/exec_parallel.py` | 1 | Parallel tool batch execution |
| `orchestration/workflow.py` | 2 | Deterministic 5-agent pipeline |
| `orchestration/recovery.py` | 2 | LLM recovery message injection |
| `registry/schema.py` | 1 | AgentDefinition Pydantic model |
| `registry/loader.py` | 1 | load_agent_registry, load_system_prompt, load_workflow |
| `registry/cache.py` | 1 | File mtime cache + hot-reload |
| `memory/state_machine.py` | 2 | WorkflowFSM + ALLOWED_TRANSITIONS |
| `memory/memory_file.py` | 2 | read/write memory.md + workflow inject |
| `memory/context_block.py` | 2 | Build # MEMORY / # USER context block |
| `tools/registry.py` | 1 | Tool tiers (READ_ONLY, ASK_BYPASS, VISIBLE, etc.) |
| `tools/pipeline.py` | 2 | Full 6-step execution pipeline |
| `tools/loop_detection.py` | 1 | LoopDetector (warn@3, block@5) |
| `tools/read_cache.py` | 1 | Per-run dedup cache |
| `tools/partition.py` | 1 | partition_batches() concurrent/serial |
| `context/history.py` | 2 | build_history + compact summary message |
| `context/compaction.py` | 2 | compact_if_over_budget() 2-tier |
| `context/accounting.py` | 2 | estimate_chars + calibrate_tokens_per_char |
| `context/thinking_codec.py` | 2 | encode/decode thinking blocks |
| `gates/gate_service.py` | 2 | Full gate service (Lua CAS, poll, cleanup) |
| `artifacts/buffer.py` | 1 | ArtifactBuffer stage/flush |
| `artifacts/file_service.py` | 1 | upsert_workspace_file |
| `streaming/events.py` | 1 | Full SSE event schema (single source) |
| `streaming/event_bus.py` | 1 | Internal event queue → SSE |
| `streaming/lock.py` | 1 | Stream lock acquire/release/refresh |
| `streaming/guards.py` | 2 | Resilience guards + rate limiting |

### 10.2 packages/tools/ — Tool implementations

| File | Phase | Mô tả |
|------|-------|-------|
| `file/read_file.py` | 1 | Đọc workspace file |
| `file/write_file.py` | 1 | Ghi + stage vào buffer + emit file_artifact |
| `file/list_file.py` | 1 | List workspace files |
| `file/edit_file.py` | 2 | Patch portion của file |
| `orchestration/spawn_agent.py` | 1 | Full spawn với activities + abort recovery |
| `orchestration/set_memory.py` | 2 | FSM + workflow inject + type sync |
| `orchestration/ask_user.py` | 2 | Ask gate integration |
| `data/schema_inspector.py` | 2 | Mock schema (Phase 3: real introspection) |
| `data/csv_preview.py` | 2 | Parse CSV upload |
| `rag/search_documents.py` | Track B, Phase 4 | Qdrant search cho tài liệu user upload |

### 10.3 packages/agents/prompts/ — Agent definitions

| File | Phase | Mô tả |
|------|-------|-------|
| `system/system-main.md` | 1 | Orchestrator persona + operating contract |
| `system/system-agent.md` | 1 | Sub-agent worker identity + security rules |
| `agents/dashboard-planner.md` | 1 | Phase 1: load ngay; updated Phase 5 |
| `agents/data-binder.md` | 2 | Updated Phase 5 với document support |
| `agents/layout-designer.md` | 2 | Grid/responsive layout design |
| `agents/dashboard-builder.md` | 2 | React/TSX code generation |
| `agents/dashboard-critic.md` | 2 | Validation + review; updated Phase 5 |
| `agents/document-analyzer.md` | Track B, Phase 5 | Document structure extraction |
| `workflows/chat/create-chat.md` | 2 | Free-form conversation flow |
| `workflows/dashboard/create-dashboard.md` | 2 | 5-agent spawn sequence |
| `workflows/dashboard/edit-dashboard.md` | 2 | Edit existing dashboard |
| `workflows/dashboard/repair-dashboard.md` | 2 | Critic fail repair flow |
| `workflows/dashboard/create-dashboard-from-document.md` | Track B, Phase 5 | Document-based creation |
