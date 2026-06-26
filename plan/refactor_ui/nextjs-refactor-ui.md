# Hướng Dẫn Refactor UI — Dashzen Studio

> **Mục tiêu:** Refactor có kiểm soát `apps/studio` — audit trước, thay đổi incremental, đo lường được kết quả. Không "refactor cho vui".

**Phạm vi:** `apps/studio/` (Next.js 15 App Router, Tailwind v4, shadcn/ui, TanStack Query, Zustand)

---

## Mục Lục

1. [Hiện Trạng Studio](#hiện-trạng-studio)
2. [Phase 0 — Audit](#phase-0--audit--hiểu-hiện-trạng)
3. [Phase 1 — Xác Định Hướng](#phase-1--xác-định-hướng-refactor)
4. [Phase 2 — Kiến Trúc Thư Mục](#phase-2--kiến-trúc-thư-mục)
5. [Phase 3 — Refactor Components](#phase-3--refactor-components)
6. [Phase 4 — Styling & Design System](#phase-4--styling--design-system)
7. [Phase 5 — State Management](#phase-5--state-management)
8. [Phase 6 — Data Fetching & Server Components](#phase-6--data-fetching--server-components)
9. [Phase 7 — Performance](#phase-7--performance--optimization)
10. [Phase 8 — Testing](#phase-8--testing--validation)
11. [Roadmap Ưu Tiên](#roadmap-ưu-tiên-dashzen)
12. [Chiến Lược Incremental](#chiến-lược-thực-thi-incremental)
13. [Checklist Tổng Hợp](#checklist-tổng-hợp)

---

## Hiện Trạng Studio

### Cấu trúc thực tế

```
apps/studio/
├── app/                    # Routes (không có src/ wrapper)
│   ├── (auth)/             # /login, /register, /verify-email
│   └── app/                # Protected /app/* (AuthGuard + AppShell)
├── components/             # Shared UI (~15 files)
│   ├── ui/                 # shadcn primitives (button.tsx, dialog.tsx…)
│   ├── brand/              # Logo, icon
│   └── providers.tsx       # React Query + Sonner
├── lib/
│   ├── api/                # client.ts + domain APIs (tasks, auth…)
│   ├── stores/             # Zustand (auth, sidebar, canvas…)
│   └── utils.ts            # cn()
└── modules/                # Feature code (~93 files — phần lớn app)
    ├── task/               # ← lớn nhất: chat, streaming, canvas
    ├── auth/, project/, artifacts/, chats/, layout/, settings/
    └── Mỗi module: components/, hooks/, lib/, types/ (không đồng đều)
```

### Quy ước đang dùng

| Khía cạnh | Quy ước | Ví dụ |
|---|---|---|
| Feature components | PascalCase `.tsx` | `ChatWorkspace.tsx`, `TaskPageClient.tsx` |
| shadcn primitives | lowercase `.tsx` | `button.tsx`, `dialog.tsx` |
| Utils / lib | kebab-case `.ts` | `query-keys.ts`, `normalize-messages.ts` |
| Stores | camelCase + `Store` | `authStore.ts`, `sidebarStore.ts` |
| Hooks | `use` + PascalCase | `useTask.ts`, `useArtifacts.ts` |
| Pages | Server `page.tsx` → Client `*PageClient.tsx` | `task/[taskId]/page.tsx` → `TaskPageClient` |
| Imports | `@/*` alias | `@/modules/task/hooks/useTask` |

### State đã phân lớp đúng hướng

| Loại | Công cụ | Vị trí |
|---|---|---|
| Server state | TanStack Query v5 | `modules/*/hooks/`, `lib/api/` |
| Shared UI state | Zustand | `lib/stores/` |
| Task runtime (stream) | Context + useReducer | `modules/task/contexts/` |
| Local UI | useState | Trong component |

### Nợ kỹ thuật đã xác định

| Mức | Vấn đề | File / vị trí |
|---|---|---|
| **Critical** | God components (>300 dòng) | `ChatInput.tsx` (457), `ChatMessageList.tsx` (316), `task-context.tsx` (306), `TaskTitleMenu.tsx` (302), `task-reducer.ts` (348) |
| **High** | Module không đồng đều | `task` đầy đủ; `chats`/`layout`/`settings` thiếu hooks/types |
| **High** | Import path lẫn lộn | ~55 file dùng `../../../` thay vì `@/` |
| **Medium** | Thư mục placeholder | `types/`, `components/auth/`, `components/shared/` (chỉ `.gitkeep`) |
| **Medium** | Alias `@/hooks` không tồn tại | `components.json` khai báo nhưng không có folder |
| **Medium** | Không có barrel exports | Import path dài, khó refactor |
| **Low** | `app/app/` naming gây nhầm | URL `/app` nhưng folder lồng `app/app/` |
| **Low** | Chưa có test UI | Phase 8 chưa bắt đầu |

---

## Phase 0 — Audit & Hiểu Hiện Trạng

Chạy từ repo root hoặc `apps/studio/`:

```bash
cd apps/studio

# Đếm file theo vùng
find modules components lib app -name "*.tsx" -o -name "*.ts" | grep -v node_modules | wc -l

# File lớn nhất (>200 dòng) — ưu tiên refactor
find modules components -name "*.tsx" -exec wc -l {} + 2>/dev/null | sort -rn | head -20

# God components (>300 dòng)
find modules components -name "*.tsx" -exec sh -c 'wc -l "$1" | awk "\$1>300{print}"' _ {} \;

# Relative imports (nên chuyển sang @/)
rg "from ['\"]\.\./" --glob "*.{ts,tsx}" -c | sort -t: -k2 -rn | head -15

# Dead code — components không được import
# (cần review thủ công sau khi chạy knip hoặc ts-prune)
npx knip --workspace apps/studio 2>/dev/null || echo "Cài knip nếu cần: npm i -D knip"
```

### Dấu hiệu cần refactor

| Vấn đề | Dấu hiệu |
|---|---|
| God Component | >300 dòng, fetch + render + logic cùng file |
| Prop Drilling | Props qua 3+ cấp (trừ khi intentional) |
| Mixed Concerns | API call + JSX + business logic trong 1 component |
| Inconsistent imports | `@/` và `../../../` xen kẽ |
| Missing types | `any`, props không typed |
| Dead structure | Folder `.gitkeep` nhưng không dùng |

### Technical Debt Registry

Tạo `plan/refactor_ui/DEBT.md` (hoặc issue tracker) và cập nhật sau mỗi sprint:

```markdown
## Critical — block velocity
- [ ] Tách ChatInput.tsx (457 dòng)

## High — ảnh hưởng DX
- [ ] Chuẩn hóa imports sang @/

## Medium — sprint tới
- [ ] Xóa placeholder dirs hoặc populate

## Low — backlog
- [ ] Đổi tên app/app/ → route group rõ hơn
```

---

## Phase 1 — Xác Định Hướng Refactor

Chọn **1–2 hướng** theo pain point thực tế — không làm cả 4 cùng lúc.

| Hướng | Mục tiêu | Phù hợp khi |
|---|---|---|
| **A — Maintainability** | Tách god components, chuẩn hóa imports, xóa dead code | Team mất thời gian navigate code |
| **B — Performance** | Server Components, lazy load, bundle size | Lighthouse / bundle analyzer báo đỏ |
| **C — DX** | Module shape đồng đều, barrel exports, Storybook | Onboard dev mới chậm |
| **D — UI Consistency** | Token system, pattern thống nhất | UI lệch giữa các màn |

**Dashzen hiện tại:** Ưu tiên **A** (task module quá lớn) → **C** (module không đồng đều).

### Scope — không refactor toàn bộ

```
1. modules/task/     — dùng nhiều nhất, god components tập trung ở đây
2. modules/auth/     — nhiều relative imports, form phức tạp
3. modules/chats/    — module mỏng, dễ chuẩn hóa làm mẫu
4. components/ui/    — ổn định, chỉ mở rộng khi cần primitive mới
```

---

## Phase 2 — Kiến Trúc Thư Mục

### Nguyên tắc: co-location theo feature

Studio **đã đúng hướng** với `modules/` — không cần migrate sang `components/features/`.

```
# ✅ Hiện tại — giữ pattern này
modules/task/
  components/chat/ChatWorkspace.tsx
  hooks/useTask.ts
  lib/query-keys.ts
  types/api.ts
  contexts/task-context.tsx

# ❌ Tránh — phân tán theo loại file
components/ChatWorkspace.tsx
hooks/useTask.ts
types/task.ts
```

### Module shape chuẩn (target)

Mọi module feature nên có cấu trúc tối thiểu:

```
modules/<feature>/
├── components/       # UI, *PageClient.tsx
├── hooks/            # React Query wrappers + facade hooks
├── lib/              # query-keys, formatters, pure utils
├── types/            # API DTOs, local types
└── schemas/          # (optional) Zod — như auth/
```

| Module | Hiện tại | Target |
|---|---|---|
| `task` | Đầy đủ + contexts | Giữ, tách god components |
| `auth` | Đầy đủ | Chuẩn hóa imports |
| `project`, `artifacts` | Đủ hooks/types | Giữ |
| `chats`, `layout`, `settings` | Thiếu hooks/types | Bổ sung khi thêm logic |
| `components/ui/` | shadcn only | Không đặt business logic |
| `lib/` | api + stores + utils | Cross-cutting only |

### Dọn placeholder

| Thư mục | Hành động |
|---|---|
| `types/` (root) | Xóa — types thuộc `modules/*/types/` |
| `components/auth/`, `components/shared/` | Xóa hoặc chuyển code vào `modules/auth/` |
| `@/hooks` alias | Xóa khỏi `components.json` hoặc tạo folder nếu cần shared hooks |

### Barrel exports (tùy chọn, làm từng module)

```typescript
// modules/task/index.ts — chỉ export public API
export { TaskPageClient } from './components/TaskPageClient';
export { useTask } from './hooks/useTask';
// Không export internals (reducer, lib helpers)
```

---

## Phase 3 — Refactor Components

### 3.1 Tách God Component — pattern Studio

**Ví dụ thực tế: `ChatInput.tsx` (457 dòng)**

Tách theo trách nhiệm:

```
ChatInput.tsx              → orchestrator mỏng (~80 dòng)
ChatInputToolbar.tsx       → actions (attach, project picker)
ChatInputTextarea.tsx      → input + keyboard shortcuts
ChatUploadPreview.tsx      → đã tách — giữ
useChatInput.ts            → state: draft, attachments, submit
```

**Quy trình:**

1. Extract presentational sub-components (không đổi behavior)
2. Extract hook cho state + handlers
3. Giữ orchestrator compose các phần
4. Test manual trên `/app/task/[id]` trước khi xóa code cũ

### 3.2 Phân loại component

| Loại | Đặc điểm | Studio ví dụ |
|---|---|---|
| UI Primitive | Không business logic | `components/ui/button.tsx` |
| Composite UI | Kết hợp primitives | `DataTable`, `Card` (shadcn) |
| Feature Component | Gắn domain | `ChatMessage.tsx`, `ArtifactCard.tsx` |
| Page Client | Orchestrate data + layout | `TaskPageClient.tsx`, `*PageClient.tsx` |

### 3.3 Props interface

```tsx
interface ChatInputProps {
  onSubmit: (message: string, files?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSubmit,
  disabled = false,
  placeholder = 'Ask anything…',
  className,
}: ChatInputProps) { /* … */ }
```

- Extend HTML attributes khi wrap native element
- `className` luôn cho phép override (dùng `cn()`)
- Variant dùng CVA — xem `components/ui/button.tsx`

### 3.4 Compound Components — khi nào dùng

Dùng khi prop explosion (>6 props layout-related). Ví dụ phù hợp: `Card`, `Dialog` (shadcn đã có). Không over-apply cho mọi component.

---

## Phase 4 — Styling & Design System

Studio **đã setup** Tailwind v4 + shadcn + CSS variables trong `app/globals.css`.

### Đã có — không cần làm lại

- `cn()` trong `lib/utils.ts` (clsx + tailwind-merge)
- Design tokens qua `@theme inline` / CSS variables (oklch)
- CVA cho variants (`components/ui/button.tsx`)
- Không dùng CSS modules

### Cần tuân thủ khi refactor

```tsx
// ✅ Dùng token / semantic classes
<div className="bg-background text-foreground border-border" />

// ❌ Magic numbers
<div style={{ marginTop: 13 }} />
<div className="mt-[13px]" />  // trừ khi design system có token
```

### Thêm primitive mới

```bash
cd apps/studio
npx shadcn@latest add <component>
```

Chỉ customize trong `components/ui/` — không fork logic vào `modules/`.

---

## Phase 5 — State Management

### Decision tree — chọn đúng công cụ

```
Cần cache API + refetch?
  └─ YES → TanStack Query (modules/*/hooks/)

Chỉ UI shared across routes? (sidebar, theme)
  └─ YES → Zustand (lib/stores/)

Runtime phức tạp trong 1 feature? (streaming, reducer)
  └─ YES → Context + useReducer (modules/task/contexts/)

Chỉ 1 component?
  └─ YES → useState / useReducer local

Cần share qua URL? (filter, tab, pagination)
  └─ YES → useSearchParams (chưa dùng nhiều — cơ hội cải thiện)
```

### Patterns Studio đang dùng tốt — giữ nguyên

```tsx
// React Query + query key factory
// modules/task/hooks/useTaskMessages.ts
export function useTaskMessages(taskId: string) {
  return useQuery({
    queryKey: taskKeys.messages(taskId),
    queryFn: () => getMessages(taskId),
    staleTime: 30_000,
  });
}

// Facade hook che context
// modules/task/hooks/useTask.ts
export function useTask() {
  return useTaskContext(); // stable API cho components
}
```

### Tránh

- Fetch trong `useEffect` khi đã có React Query hook
- Context cho data có thể cache bằng Query
- Zustand cho state chỉ dùng trong 1 component

---

## Phase 6 — Data Fetching & Server Components

### Pattern hiện tại (giữ)

```tsx
// app/app/task/[taskId]/page.tsx — Server Component mỏng
export default async function TaskPage({ params }: PageProps) {
  const { taskId } = await params;
  return <TaskPageClient taskId={taskId} />;
}

// TaskPageClient.tsx — Client, fetch qua React Query
'use client';
export function TaskPageClient({ taskId }: { taskId: string }) {
  const { data } = useTaskMeta(taskId);
  // …
}
```

### Cơ hội mở rộng Server Components

| Trang | Hiện tại | Có thể cải thiện |
|---|---|---|
| `artifacts/[id]` | Client fetch | Prefetch metadata server-side |
| `projects/[id]` | Client fetch | Initial data qua `HydrationBoundary` |
| `chats` | Client list | Server render shell + stream list |

```tsx
// Pattern: prefetch + hydrate (khi cần SEO hoặc faster FCP)
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query';

export default async function ProjectPage({ params }) {
  const { projectId } = await params;
  const qc = new QueryClient();
  await qc.prefetchQuery({ queryKey: projectKeys.detail(projectId), queryFn: … });
  return (
    <HydrationBoundary state={dehydrate(qc)}>
      <ProjectDetailClient projectId={projectId} />
    </HydrationBoundary>
  );
}
```

### Streaming với Suspense

```tsx
<Suspense fallback={<StatsSkeleton />}>
  <UserStats />
</Suspense>
```

Áp dụng cho các section độc lập trên dashboard/artifacts — không block cả page.

---

## Phase 7 — Performance & Optimization

### Đo trước khi tối ưu

```bash
cd apps/studio
ANALYZE=true npm run build   # cần @next/bundle-analyzer

# React DevTools Profiler — đo re-render trên /app/task/*
```

### Ưu tiên cho Studio

| Kỹ thuật | Áp dụng |
|---|---|
| `dynamic()` lazy load | `ArtifactCanvasPanel`, chart libs, PDF viewer |
| `next/image` | Mọi image ngoài markdown content |
| `memo` / `useMemo` | Chỉ sau khi Profiler chứng minh cần — đặc biệt `ChatMessageList` |
| Server Components | Prefetch static metadata, giảm client JS |
| Virtualization | `ChatMessageList` nếu message count >100 |

```tsx
// Lazy load canvas — chỉ khi user mở panel
const ArtifactCanvasPanel = dynamic(
  () => import('./canvas/ArtifactCanvasPanel'),
  { loading: () => <CanvasSkeleton />, ssr: false }
);
```

### Không làm sớm

- `memo()` mọi component
- Tách micro-components <20 dòng
- Premature Server Component migration cho task streaming (cần client)

---

## Phase 8 — Testing & Validation

Studio **chưa có test** — bắt đầu từ module ổn định, không từ task streaming.

### Thứ tự triển khai

```
1. lib/utils.ts, lib/api/errors.ts     — unit tests (dễ, pure)
2. modules/*/lib/query-keys.ts         — unit tests
3. components/ui/button.tsx            — component tests (Testing Library)
4. modules/auth/schemas/*.schema.ts    — Zod validation tests
5. E2E login → create task             — Playwright (1 happy path)
```

```tsx
// Ví dụ: components/ui/button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from './button';

it('disables when loading', () => {
  render(<Button disabled>Submit</Button>);
  expect(screen.getByRole('button')).toBeDisabled();
});
```

### Setup đề xuất

```bash
npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom
npm i -D @playwright/test
```

---

## Roadmap Ưu Tiên (Dashzen)

Thực hiện theo thứ tự — mỗi bước là PR riêng, không gộp feature mới.

### Sprint 1 — Quick wins (Low risk, High impact)

- [ ] Chuẩn hóa imports: `../../../` → `@/` (auth module trước)
- [ ] Xóa placeholder dirs (`types/`, `components/auth/`, `components/shared/`)
- [ ] Sửa `components.json` — bỏ alias `@/hooks` hoặc tạo folder
- [ ] Tạo `plan/refactor_ui/DEBT.md` và track god components

### Sprint 2 — Task module decomposition

- [ ] Tách `ChatInput.tsx` → sub-components + `useChatInput`
- [ ] Tách `TaskTitleMenu.tsx` → menu actions riêng
- [ ] Review `ChatMessageList.tsx` — extract scroll logic (`useStreamScroll` đã có)

### Sprint 3 — Module consistency

- [ ] Chuẩn hóa `modules/chats/` làm template (hooks/, types/, lib/)
- [ ] Áp dụng shape tương tự cho `layout/`, `settings/`
- [ ] (Optional) Barrel `index.ts` cho `task`, `auth`

### Sprint 4 — Performance & Server data

- [ ] Lazy load `ArtifactCanvasPanel`
- [ ] Prefetch project/artifact metadata server-side
- [ ] Bundle analyzer baseline + budget

### Sprint 5 — Testing foundation

- [ ] Vitest setup + tests cho `lib/` utils
- [ ] Component tests cho `components/ui/`
- [ ] 1 Playwright E2E: auth → task page loads

---

## Chiến Lược Thực Thi Incremental

### Nguyên tắc vàng

```
KHÔNG refactor + feature mới trong cùng 1 PR.
```

### Quy trình 4 bước

```
1. Tạo file mới cạnh file cũ
   ChatInput.tsx          ← production
   ChatInputToolbar.tsx   ← extract mới

2. Wire dần — orchestrator gọi sub-components mới

3. Verify trên /app/task/[id] — streaming, upload, project picker

4. Xóa code dead khi sub-components cover hết behavior
```

### Ma trận rủi ro

| Impact | Risk | Ví dụ | Cách làm |
|---|---|---|---|
| High | Low | Đổi imports, xóa dead code | PR nhỏ, merge nhanh |
| High | High | Tách task-context, đổi reducer | Feature flag hoặc branch dài, test kỹ stream |
| Low | Low | Rename biến, format | Batch hoặc bỏ qua |
| Low | High | — | Hiếm, tránh |

---

## Checklist Tổng Hợp

### Trước khi bắt đầu

- [x] Audit hiện trạng (doc này)
- [ ] DEBT.md tạo và assign owner
- [ ] Branch strategy: `refactor/<module>-<mô-tả>`
- [ ] Baseline: `npm run build` pass, manual smoke test `/app`

### Architecture

- [x] Module co-location (`modules/`)
- [x] Path alias `@/*` configured
- [ ] Imports 100% `@/` (hiện ~55 file relative)
- [ ] Xóa placeholder dirs
- [ ] Module shape đồng đều

### Components

- [ ] Không god component >300 dòng trong `modules/task/`
- [ ] Business logic trong hooks/lib, không trong JSX file
- [ ] Props typed đầy đủ
- [x] Page pattern: server `page.tsx` → `*PageClient`

### Styling

- [x] Tailwind v4 + shadcn + `cn()`
- [x] CSS variables / design tokens
- [ ] Không thêm magic numbers khi refactor

### State

- [x] Query cho server state
- [x] Zustand cho shared UI
- [x] Context+reducer cho task streaming
- [ ] URL state cho filters/tabs (future)

### Performance

- [ ] Bundle baseline recorded
- [ ] Lazy load heavy panels
- [ ] Profiler check trên ChatMessageList

### Testing

- [ ] Vitest configured
- [ ] Unit tests cho `lib/`
- [ ] E2E happy path

---

## Tổng Kết

Refactor hiệu quả = **cải thiện có kiểm soát**, không viết lại từ đầu.

1. **Hiểu trước — code sau:** Studio đã có nền tảng tốt (`modules/`, Query, Zustand). Nợ tập trung ở `task/`.
2. **Incremental > Big Bang:** Mỗi PR một mục tiêu, dễ review, dễ rollback.
3. **Đo lường:** God component count, relative import count, bundle size — trước và sau.

> _"Make it work → Make it right → Make it fast"_ — Kent Beck

### Tham chiếu nhanh

| Cần làm gì | Xem |
|---|---|
| Thêm UI primitive | `npx shadcn add` → `components/ui/` |
| Thêm API call | `lib/api/<domain>.ts` + hook trong `modules/*/hooks/` |
| Thêm shared UI state | `lib/stores/<name>Store.ts` |
| Thêm feature | `modules/<feature>/` theo module shape |
| Page mới | `app/.../page.tsx` + `modules/.../XPageClient.tsx` |
