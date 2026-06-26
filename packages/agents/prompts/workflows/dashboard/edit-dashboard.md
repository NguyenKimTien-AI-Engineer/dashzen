# Workflow: Edit Dashboard

The dashboard is built. Understand the user's request, pick the right agent, delegate.

---

## Agent Roster

| Agent | Responsibility |
|-------|---------------|
| `dashboard-planner` | Change metrics, widgets, filters, or dashboard scope → updates `spec.md` |
| `data-binder` | Change data mapping, add columns, fix query/mock bindings → updates `bindings.md` |
| `layout-designer` | Change grid, widget order, responsive layout → updates `layout.md` |
| `dashboard-builder` | Apply spec/layout/binding changes to `dashboard.html`; also handles visual redesign (theme, color, typography changes) |
| `dashboard-critic` | Re-validate after substantive changes → updates `review.md` |

---

## Intent → Agent

| User intent | Agent(s) | Order |
|-------------|----------|-------|
| Add/remove KPI or chart | `dashboard-planner` → `data-binder` → `layout-designer` → `dashboard-builder` | Sequential |
| Change metric definition only | `dashboard-planner` → `data-binder` → `dashboard-builder` | Sequential |
| Change data source / column mapping | `data-binder` → `dashboard-builder` | Sequential |
| Move widgets, resize, reorder | `layout-designer` → `dashboard-builder` | Sequential |
| Change colors, theme, font, or visual style | `dashboard-planner` (update visualTheme/colorScheme) → `dashboard-builder` | Sequential |
| Change chart type only | `dashboard-planner` (update widget type) → `dashboard-builder` | Sequential |
| Change labels or copy only | `dashboard-builder` only | Single |
| Fix validation / a11y issues | `dashboard-critic` identifies → targeted agent | Per review |

**Multi-step edits** (e.g. "add revenue chart + move KPIs to top"):
1. Planner (update spec)
2. Data binder (if new metric needs binding)
3. Layout designer (if layout changes)
4. Builder (apply all)
5. Critic (if spec or bindings changed)

Do NOT run planner and builder in parallel — builder depends on spec.

Genuinely ambiguous → `ask_user` once. Clear intent → do NOT ask.

---

## Dispatch

Self-contained task descriptions — agents cannot see your conversation:

```
spawn_agent("dashboard-planner", "Update spec.md: <what to add/change/remove>. Read current spec.md first. Language: <lang>.")
spawn_agent("data-binder", "Update bindings.md for changed metrics in spec.md. Read spec.md + bindings.md. Data: <csv or mock>.")
spawn_agent("layout-designer", "Update layout.md: <layout change>. Read spec.md + layout.md.")
spawn_agent("dashboard-builder", "Update dashboard.html: <change>. Read spec.md, bindings.md, layout.md, dashboard.html. Preserve <!-- builder --> marker.")
spawn_agent("dashboard-critic", "Re-review dashboard after edits. Read all workspace files → update review.md.")
```

After substantive edits (spec, bindings, or layout changed), always run critic before telling the user the dashboard is ready.

**If user message contains `<ide_selection>`:**
Include the full `<ide_selection>` block verbatim in the task description passed to `dashboard-builder`.
The agent uses it as the exact edit target.

Example:
```
spawn_agent("dashboard-builder", """
<ide_selection>
Lines 42-68 from dashboard.html:
<Card>...</Card>
</ide_selection>

Change this KPI card to show percentage instead of absolute value.
""")
```

---

## Scope guard

- Small copy/label tweaks → builder only
- New widget → planner → binder → layout → builder → critic
- Full redesign → ask_user whether to edit in place or start fresh (`create-dashboard`)
