# Technical Debt Registry — Dashzen Studio

> Cập nhật: 2026-06-25 — **refactor 100%** (trừ mục optional không ảnh hưởng prod)

---

## Critical — block velocity

- [x] God components tách xong (0 file >300 dòng)

## High — DX

- [x] Imports cross-boundary → `@/`
- [x] Module shape 7/7 + barrel exports (`project`, `artifacts` included)
- [x] `components.json` + `lib/hooks/`

## Medium — performance & data

- [x] Lazy load `ArtifactCanvasPanel`, `DashboardHtmlPreview`
- [x] Server prefetch + `HydrationBoundary` (`projects/[id]`, `artifacts/[id]`)
- [x] Bundle analyzer (`npm run analyze`) + [`BUNDLE_BASELINE.md`](./BUNDLE_BASELINE.md)
- [x] Vitest — **19 unit tests**
- [x] Playwright E2E (`npm run test:e2e`, `e2e/smoke.spec.ts`)
- [x] URL state `/app/chats` (`?q=`, `?filter=active`) — default URL không đổi

## Optional / không làm (lý do)

- [ ] **Storybook** — tooling dev-only; unit + E2E đủ coverage; thêm ~30 deps
- [ ] **Đổi tên `app/app/`** — đổi URL/routing; risk cao, không lợi ích UX
- [ ] **Component tests `ui/`** — E2E + lib tests cover; thêm khi có regression

---

## Metrics

| Metric | Baseline | Hiện tại |
|--------|----------|----------|
| God components (>300 dòng) | 5 | **0** |
| Cross-boundary `../../../` | ~55 | **0** |
| Unit tests | 0 | **19** |
| E2E specs | 0 | **3** (1 public + 2 auth, auth cần `E2E_*`) |
| Server prefetch pages | 0 | **2** |
| `npm run build` | pass | **pass** |

---

## Commands

```bash
cd apps/studio
npm run test          # Vitest unit
npm run test:e2e      # Playwright (cần API + E2E_EMAIL/PASSWORD cho auth)
npm run analyze       # Bundle report
npm run build         # Production build
```
