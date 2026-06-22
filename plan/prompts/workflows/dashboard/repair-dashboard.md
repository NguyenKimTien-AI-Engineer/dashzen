# Workflow: Repair Dashboard

The critic returned **FAIL** in `review.md`. Fix issues systematically — do not rebuild from scratch unless the user asks.

---

## Step 1 — Triage

Read `review.md` and classify each issue:

| Category | Typical issues | Primary agent |
|----------|----------------|---------------|
| **Spec** | Missing widget, wrong metric, ungrounded KPI | `dashboard-planner` |
| **Data** | Column not found, mock mismatch, invalid binding | `data-binder` |
| **Layout** | Overlap, missing responsive rule, wrong order | `layout-designer` |
| **Code** | Render error, wrong chart type, broken import | `dashboard-builder` |
| **A11y / UX** | Missing labels, poor contrast, no empty state | `dashboard-builder` or `layout-designer` |

Group issues by agent. Fix upstream first (spec → bindings → layout → code).

---

## Step 2 — Repair sequence

For each issue group, spawn the responsible agent with the exact fix from `review.md`:

```
spawn_agent("dashboard-planner", "Fix spec issues from review.md: <list>. Read spec.md + review.md.")
spawn_agent("data-binder", "Fix binding issues from review.md: <list>. Read spec.md, bindings.md, review.md.")
spawn_agent("layout-designer", "Fix layout issues from review.md: <list>. Read layout.md + review.md.")
spawn_agent("dashboard-builder", "Fix code issues from review.md: <list>. Read all files. Preserve <!-- builder -->.")
```

After repairs, always re-run critic:

```
spawn_agent("dashboard-critic", "Re-review after repair. Read all workspace files. Update review.md.")
```

---

## Step 3 — Exit conditions

| Result | Action |
|--------|--------|
| Critic **PASS** | `set_memory({ phase: "edit-dashboard" })` — inform user dashboard is fixed |
| Critic **FAIL** again (same issues) | Stop. `ask_user` — offer to simplify scope or start fresh |
| Critic **FAIL** (new issues) | One more repair cycle; then stop if still failing |

Maximum **2 repair cycles** per user turn unless the user explicitly asks to continue.

---

## Rules

- Do not spawn all five agents blindly — fix only what `review.md` flags
- Pass the exact issue text from `review.md` in each brief
- Do not delete working artifacts — patch in place
- If failure is due to missing user data (column not in CSV), `ask_user` for upload or metric change — do not invent data
