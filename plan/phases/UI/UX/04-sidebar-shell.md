# 04 — Sidebar Shell (Claude-inspired)

> Thiết kế **app sidebar** — layout shell trước khi Task module (recents, New Dashboard API) ship.
>
> **Tham chiếu UI:** Claude.ai sidebar (3 mockup user cung cấp, 2026-06)  
> **Nguồn planner:** [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §4 | [Phase 1 §3.2](./phase-1-mvp-foundation.md)

---

## 1. Phân tích mẫu Claude (reference)

### 1.1 Cấu trúc tổng thể

```
┌─ Sidebar ─────────────────────┐
│ [Logo]          [🔍] [◧]     │  ← Header: brand + actions
├───────────────────────────────┤
│ + New chat                    │
│ 💬 Chats                      │  ← Primary nav (icon + label)
│ 📁 Projects                   │
│ 🧪 Artifacts                  │
│ ...                           │  ← Recents / sections (Phase 1 sau)
│                               │
│         (scroll)              │
├───────────────────────────────┤
│ (T) TienKim        [↓]        │  ← Footer: avatar + user + menu
└───────────────────────────────┘
```

| Vùng | Claude | DashZen (as-designed) |
|------|--------|------------------------|
| Header trái | Wordmark serif "Claude" | `DashZenLogo` (+ Studio khi mở rộng) |
| Header phải | Search + collapse sidebar | Search + collapse sidebar |
| Nav chính | New chat, Chats, Projects, Artifacts, … | **Cùng 4 mục** (placeholder routes) |
| Giữa | Starred, Recents | **Defer** — Task module Phase 1 |
| Footer | Avatar initial + tên + plan + menu popover | Avatar initial + display name + **Settings popover** |

### 1.2 Collapsed (icon-only) — Claude pattern

| Vùng | Thu gọn |
|------|---------|
| Header | **Chỉ logo icon** (không search/collapse text) |
| Nav | **Chỉ icon** — tooltip on hover |
| Footer | **Avatar tròn** — click mở menu |

### 1.3 User menu popover (Claude → DashZen)

Claude popover: email header, Settings, Language, Help, Upgrade, Log out…

**DashZen Phase shell (yêu cầu user):**

| Item | Route | Ghi chú |
|------|-------|---------|
| Profile | `/app/profile` | CRUD display name |
| Settings | `/app/settings` | Security, logout, delete |

> Log out **không** trong popover — giữ trên trang Settings (đã có). Phase sau có thể thêm.

---

## 2. Yêu cầu đã chốt (user 2026-06-23)

### 2.1 Header

| Trạng thái | Trái | Phải |
|------------|------|------|
| **Expanded** | `DashZen` + `Studio` logo link `/app` | `Search` button + `Collapse` button |
| **Collapsed** | **Chỉ** `DashZenIcon` (click → expand) | *(ẩn)* |

### 2.2 Primary navigation

Thay `Home / Profile / Settings` links cũ bằng:

| Label | Icon (lucide) | Route MVP | Phase sau |
|-------|---------------|-----------|-----------|
| New chat | `Plus` trong vòng `bg-muted` | `/app` | `POST /tasks` → task mới |
| Chats | `MessagesSquare` | `/app/chats` | Danh sách conversations |
| Projects | `Archive` | `/app/projects` | Nhóm task/project |
| Artifacts | `Shapes` | `/app/artifacts` | Outputs / dashboards |

- Expanded: icon + label, active state `bg-muted` rounded-lg
- Collapsed: icon centered, `Tooltip` hiện label

### 2.3 Footer — user account

| Trạng thái | UI |
|------------|-----|
| **Expanded** | Avatar tròn (chữ cái đầu `display_name`) + tên + nút mở popover |
| **Collapsed** | Avatar tròn — click mở popover |

**Popover** (`SidebarUserMenu`):

```
┌─────────────────────────┐
│ user@example.com        │
├─────────────────────────┤
│ 👤 Profile              │  → mở SettingsPanel tab General
│ ⚙️ Settings             │  → mở SettingsPanel tab Account
└─────────────────────────┘
```

**SettingsPanel** (modal Claude-style) — `modules/settings/components/SettingsPanel.tsx`:

```
┌─ Settings modal ─────────────────────────────────────────┐
│ [Search]     │  Profile / Account / Privacy content     │
│ Settings     │                                          │
│  General  ◀  │  (right panel scroll)                    │
│  Account     │                                          │
│  Privacy     │                                    [X]   │
└──────────────┴──────────────────────────────────────────┘
```

| Tab | Nội dung |
|-----|----------|
| **General** | Avatar, display name, member since |
| **Account** | Email, change password, sign out, delete |
| **Privacy** | Data usage, cookies, export (placeholder) |

Routes `/app/profile` và `/app/settings` vẫn hoạt động — auto-mở panel tương ứng.

### 2.4 Không đặt ở sidebar

| Hành động | Vị trí đúng (plan Auth) |
|-----------|-------------------------|
| Edit profile | `/app/profile` |
| Change password | `/app/settings` → Security |
| Delete account | `/app/settings` → Danger zone |
| Sign out | `/app/settings` → Session |

---

## 3. Kích thước & tokens

| Token | Expanded | Collapsed |
|-------|----------|-----------|
| Width | `16rem` (256px) | `4rem` (64px) |
| Header height | `3rem` | `3rem` |
| Nav item height | `2.25rem` | `2.25rem` |
| Avatar | `2rem` circle | `2rem` circle |
| Transition | `width 200ms ease` | — |

---

## 4. State management

```typescript
// lib/stores/sidebarStore.ts
type SidebarStore = {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  toggle: () => void;
};
```

- Persist `collapsed` → `localStorage` key `dashzen:sidebar-collapsed`
- Zustand — align Phase 1 `sidebarStore`

---

## 5. Component tree

```
apps/studio/
├── app/app/layout.tsx              # AuthGuard + flex shell
├── modules/layout/
│   └── components/
│       ├── AppSidebar.tsx          # Shell container
│       ├── SidebarHeader.tsx       # Logo + search + collapse
│       ├── SidebarNav.tsx          # 4 nav items
│       ├── SidebarNavItem.tsx      # Link + icon + tooltip
│       └── SidebarUserMenu.tsx     # Footer avatar + popover
├── lib/stores/sidebarStore.ts
└── components/ui/
    ├── popover.tsx
    └── tooltip.tsx
```

---

## 6. Search button (MVP)

| Phase | Hành vi |
|-------|---------|
| **Shell MVP** | Button visible; `onClick` → toast "Search coming soon" hoặc no-op |
| Phase 2 | `Cmd+K` command palette — filter recents |

---

## 7. Placeholder pages

Routes nav chưa có backend → placeholder tối thiểu:

| Route | Page |
|-------|------|
| `/app/chats` | "Chats — coming soon" |
| `/app/projects` | "Projects — coming soon" |
| `/app/artifacts` | "Artifacts — coming soon" |

`/app` giữ welcome home hiện tại.

---

## 8. Responsive

| Breakpoint | Hành vi |
|------------|---------|
| `< sm` | Sidebar ẩn (giữ `hidden sm:flex` như hiện tại) |
| `≥ sm` | Sidebar expanded/collapsed theo store |
| Phase sau | Mobile drawer + hamburger |

---

## 9. Implementation checklist

- [x] Plan doc (file này)
- [x] `sidebarStore` + persist
- [x] `AppSidebar` + subcomponents
- [x] `popover` + `tooltip` shadcn
- [x] Wire `app/app/layout.tsx`
- [x] Placeholder pages chats/projects/artifacts
- [x] Active route highlight (`usePathname`)
- [x] Remove old Home/Profile/Settings text links

---

## 10. Phase tiếp theo (không block shell)

| Item | Phase |
|------|-------|
| Recents list `GET /tasks` | UX Phase 1 §3.2 |
| New chat → `POST /tasks` | UX Phase 1 |
| Search filter recents | Phase 2 |
| Starred / Products sections | Phase 2–3 |
| Mobile drawer | Phase 1 responsive polish |

---

## 11. Cross-references

| Doc | Liên quan |
|-----|-----------|
| [10-account-management.md](../Auth/10-account-management.md) | Profile/Settings **không** trên sidebar nav |
| [phase-1-mvp-foundation.md](./phase-1-mvp-foundation.md) | §3.2 App shell |
| `apps/studio/app/app/layout.tsx` | Integration point |
