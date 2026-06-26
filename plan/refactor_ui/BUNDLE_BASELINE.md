# Bundle baseline — Dashzen Studio

Recorded: 2026-06-25 (after refactor phase 2)

## How to analyze

```bash
cd apps/studio
npm run analyze   # opens bundle report in browser
```

Requires `@next/bundle-analyzer` (devDependency).

## Production build snapshot (`npm run build`)

| Route | First Load JS | Notes |
|-------|---------------|-------|
| `/app` (home) | ~174 kB | Chat home |
| `/app/task/[taskId]` | ~238 kB | Largest — chat + stream |
| `/app/chats` | ~145 kB | |
| `/app/projects` | ~157 kB | |
| `/app/artifacts` | ~133 kB | |
| Shared chunks | ~102 kB | All routes |

## Budget (guardrails)

| Metric | Budget | Action if exceeded |
|--------|--------|------------------|
| `/app/task/[taskId]` First Load | < 260 kB | Lazy-load more task panels |
| Shared First Load JS | < 110 kB | Audit shared imports |
| Any new route | +15 kB max vs peer | Split or dynamic import |

## Optimizations applied

- `ArtifactCanvasPanel` — `next/dynamic` (ssr: false)
- `projects/[id]`, `artifacts/[id]` — server prefetch + `HydrationBoundary`

Re-run `npm run analyze` after major feature work and update this table.
