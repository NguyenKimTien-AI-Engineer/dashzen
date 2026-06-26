# 🔧 Hướng Dẫn Refactor UI Codebase với Next.js

> **Mục tiêu:** Hệ thống hóa toàn bộ quy trình refactor — từ kiểm tra hiện trạng, lập kế hoạch, đến thực thi và kiểm thử — theo từng phase rõ ràng, tránh "refactor cho vui" mà không có định hướng.

---

## Mục Lục

1. [Phase 0 — Audit & Hiểu Hiện Trạng](#phase-0--audit--hiểu-hiện-trạng)
2. [Phase 1 — Xác Định Hướng Refactor](#phase-1--xác-định-hướng-refactor)
3. [Phase 2 — Kiến Trúc Thư Mục](#phase-2--kiến-trúc-thư-mục)
4. [Phase 3 — Refactor Components](#phase-3--refactor-components)
5. [Phase 4 — Styling & Design System](#phase-4--styling--design-system)
6. [Phase 5 — State Management](#phase-5--state-management)
7. [Phase 6 — Data Fetching & Server Components](#phase-6--data-fetching--server-components)
8. [Phase 7 — Performance & Optimization](#phase-7--performance--optimization)
9. [Phase 8 — Testing & Validation](#phase-8--testing--validation)
10. [Chiến Lược Thực Thi Incremental](#chiến-lược-thực-thi-incremental)
11. [Checklist Tổng Hợp](#checklist-tổng-hợp)

---

## Phase 0 — Audit & Hiểu Hiện Trạng

Trước khi viết một dòng code mới, phải hiểu rõ codebase đang ở trạng thái nào.

### 0.1 Inventory Toàn Bộ Codebase

```bash
# Đếm số components
find ./components -name "*.tsx" | wc -l

# Đếm số pages / app routes
find ./app -name "page.tsx" | wc -l
find ./pages -name "*.tsx" | wc -l

# Tìm các file lớn bất thường (>200 dòng)
find ./src -name "*.tsx" -exec wc -l {} + | sort -rn | head -20
```

### 0.2 Các Vấn Đề Cần Tìm

| Vấn đề | Dấu hiệu nhận biết |
|---|---|
| **God Component** | File >300 dòng, làm quá nhiều việc |
| **Prop Drilling** | Props truyền qua 3+ cấp component |
| **Duplicated Logic** | Copy-paste code giữa các component |
| **Inconsistent Styling** | Màu sắc, spacing viết cứng (hardcoded) |
| **Mixed Concerns** | Fetch data + render UI + xử lý logic trong cùng 1 component |
| **Missing Types** | `any`, thiếu interface, thiếu Props type |
| **Dead Code** | Components không được import ở đâu |
| **Naming Inconsistency** | `UserCard`, `user-card`, `usercard` tồn tại cùng lúc |

### 0.3 Đánh Giá Kỹ Thuật Nợ (Technical Debt)

Tạo một file `REFACTOR_NOTES.md` ghi lại:

```markdown
## Technical Debt Registry

### Critical (block production)
- [ ] ...

### High (ảnh hưởng developer experience)
- [ ] ...

### Medium (cần làm trong sprint tới)
- [ ] ...

### Low (backlog)
- [ ] ...
```

---

## Phase 1 — Xác Định Hướng Refactor

Refactor không phải là "viết lại cho đẹp hơn". Cần xác định rõ **mục tiêu cụ thể**:

### 1.1 Các Hướng Refactor Chính

#### Hướng A — Cải thiện Maintainability
- Tách components quá lớn
- Chuẩn hóa naming convention
- Xóa dead code
- Thêm TypeScript types đầy đủ

#### Hướng B — Cải thiện Performance
- Chuyển sang Server Components (Next.js App Router)
- Lazy loading & code splitting
- Tối ưu images, fonts
- Giảm bundle size

#### Hướng C — Cải thiện Developer Experience
- Thiết lập Design System / Component Library
- Chuẩn hóa folder structure
- Thêm Storybook cho components
- Cải thiện DevTools & error boundaries

#### Hướng D — Cải thiện UI/UX Consistency
- Tạo token system (colors, spacing, typography)
- Thống nhất pattern giữa các màn hình
- Responsive design nhất quán

> **Lưu ý:** Không nên chọn tất cả 4 hướng cùng lúc. Chọn 1–2 hướng ưu tiên theo pain point thực tế của team.

### 1.2 Xác Định Scope

```
KHÔNG nên refactor toàn bộ cùng lúc.
Ưu tiên theo:
  1. Modules được dùng nhiều nhất
  2. Modules có bug/issue nhiều nhất
  3. Modules team sẽ phát triển tiếp trong tương lai gần
```

---

## Phase 2 — Kiến Trúc Thư Mục

### 2.1 Cấu Trúc Được Khuyến Nghị (App Router)

```
src/
├── app/                          # Next.js App Router
│   ├── (marketing)/              # Route group — không ảnh hưởng URL
│   │   ├── about/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── settings/page.tsx
│   │   └── layout.tsx
│   ├── api/                      # API Routes
│   └── layout.tsx
│
├── components/                   # Shared UI components
│   ├── ui/                       # Primitive, headless components
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts
│   │   ├── Input/
│   │   └── Modal/
│   │
│   ├── features/                 # Feature-specific components
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── AuthProvider.tsx
│   │   ├── dashboard/
│   │   └── profile/
│   │
│   └── layouts/                  # Layout components
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
│
├── hooks/                        # Custom hooks
│   ├── useAuth.ts
│   ├── useDebounce.ts
│   └── useLocalStorage.ts
│
├── lib/                          # Utilities & external integrations
│   ├── utils.ts
│   ├── api.ts
│   └── validators.ts
│
├── stores/                       # State management (Zustand, Jotai...)
│   ├── authStore.ts
│   └── uiStore.ts
│
├── types/                        # Global TypeScript types
│   ├── api.ts
│   └── models.ts
│
└── styles/                       # Global styles & design tokens
    ├── globals.css
    └── tokens.css
```

### 2.2 Nguyên Tắc Tổ Chức

**Co-location**: Code liên quan đến nhau thì đặt cạnh nhau.

```
# ✅ Tốt — feature module tự chứa
features/
  user-profile/
    UserProfile.tsx
    UserProfile.test.tsx
    useUserProfile.ts
    userProfileApi.ts
    types.ts

# ❌ Tránh — phân tán theo loại file
components/UserProfile.tsx
hooks/useUserProfile.ts
types/userProfile.ts
tests/UserProfile.test.tsx
```

**Barrel exports** — Tránh import path dài:

```typescript
// components/ui/index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Modal } from './Modal';

// Sử dụng
import { Button, Input } from '@/components/ui';
```

---

## Phase 3 — Refactor Components

### 3.1 Tách God Component

**Trước khi refactor:**

```tsx
// ❌ UserDashboard.tsx — 400 dòng, làm quá nhiều việc
export function UserDashboard() {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/user').then(r => r.json()).then(setUser);
    fetch('/api/posts').then(r => r.json()).then(setPosts);
    setLoading(false);
  }, []);

  // 300 dòng JSX trộn lẫn mọi thứ...
}
```

**Sau khi refactor:**

```tsx
// ✅ Tách thành các đơn vị rõ ràng

// hooks/useUserDashboard.ts — Data logic
export function useUserDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchUser(),
      fetchPosts(),
    ]).finally(() => setLoading(false));
  }, []);

  return { user, posts, loading };
}

// components/features/dashboard/UserStats.tsx — Presentational
export function UserStats({ user }: { user: User }) {
  return <div>...</div>;
}

// components/features/dashboard/PostList.tsx — Presentational
export function PostList({ posts }: { posts: Post[] }) {
  return <ul>...</ul>;
}

// app/dashboard/page.tsx — Orchestrator
export default function DashboardPage() {
  const { user, posts, loading } = useUserDashboard();

  if (loading) return <DashboardSkeleton />;

  return (
    <DashboardLayout>
      <UserStats user={user} />
      <PostList posts={posts} />
    </DashboardLayout>
  );
}
```

### 3.2 Nguyên Tắc Phân Loại Component

| Loại | Đặc điểm | Ví dụ |
|---|---|---|
| **UI Primitive** | Không có business logic, reusable tuyệt đối | `Button`, `Input`, `Badge` |
| **Composite UI** | Kết hợp primitives, vẫn generic | `SearchBar`, `DataTable`, `Card` |
| **Feature Component** | Gắn với domain cụ thể | `UserProfileCard`, `OrderSummary` |
| **Page Component** | Orchestrate data + layout | `CheckoutPage`, `DashboardPage` |

### 3.3 Chuẩn Hóa Props Interface

```tsx
// ✅ Props rõ ràng, có JSDoc, có default values
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Kiểu visual của button */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  /** Kích thước */
  size?: 'sm' | 'md' | 'lg';
  /** Hiển thị loading spinner */
  isLoading?: boolean;
  /** Icon hiển thị bên trái */
  leftIcon?: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      data-variant={variant}
      data-size={size}
      {...rest}
    >
      {isLoading && <Spinner />}
      {children}
    </button>
  );
}
```

### 3.4 Compound Components Pattern

Thay vì truyền quá nhiều props, dùng Compound Components:

```tsx
// ❌ Prop explosion
<Card
  title="Hello"
  subtitle="World"
  image="/img.png"
  actions={[...]}
  footer="..."
  headerVariant="dark"
/>

// ✅ Compound pattern — linh hoạt, dễ đọc
<Card>
  <Card.Header variant="dark">
    <Card.Title>Hello</Card.Title>
    <Card.Subtitle>World</Card.Subtitle>
  </Card.Header>
  <Card.Image src="/img.png" />
  <Card.Footer>
    <Card.Actions>...</Card.Actions>
  </Card.Footer>
</Card>
```

---

## Phase 4 — Styling & Design System

### 4.1 Thiết Lập Design Tokens

```css
/* styles/tokens.css */
:root {
  /* Colors */
  --color-brand-50: #eff6ff;
  --color-brand-500: #3b82f6;
  --color-brand-900: #1e3a5f;

  --color-neutral-0: #ffffff;
  --color-neutral-100: #f5f5f5;
  --color-neutral-900: #111111;

  --color-danger: #ef4444;
  --color-success: #22c55e;
  --color-warning: #f59e0b;

  /* Spacing scale */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-4xl: 2.25rem;

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
}
```

### 4.2 Nếu Dùng Tailwind CSS

```typescript
// tailwind.config.ts — Map tokens vào Tailwind
import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: 'var(--color-brand-50)',
          500: 'var(--color-brand-500)',
          900: 'var(--color-brand-900)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
    },
  },
} satisfies Config;
```

### 4.3 Chuẩn Hóa Class Merging

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Dùng cn() thay vì template literals thủ công
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Sử dụng
<div className={cn(
  'base-class',
  isActive && 'active-class',
  variant === 'ghost' && 'ghost-class',
  className, // cho phép override từ bên ngoài
)} />
```

### 4.4 Variant Management với CVA

```typescript
// Dùng class-variance-authority (cva) cho component variants
import { cva } from 'class-variance-authority';

const buttonVariants = cva(
  // Base classes
  'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none',
  {
    variants: {
      variant: {
        primary: 'bg-brand-500 text-white hover:bg-brand-600',
        secondary: 'border border-neutral-300 hover:bg-neutral-100',
        ghost: 'hover:bg-neutral-100',
        danger: 'bg-danger text-white hover:bg-red-600',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);
```

---

## Phase 5 — State Management

### 5.1 Phân Loại State

```
State trong ứng dụng gồm 4 loại — mỗi loại có giải pháp khác nhau:

1. LOCAL UI STATE    → useState, useReducer
   (modal open, form input, tab active)

2. SHARED UI STATE  → Context API hoặc Zustand/Jotai
   (theme, sidebar collapsed, notifications)

3. SERVER STATE     → TanStack Query / SWR
   (API data, cache, refetching)

4. URL STATE        → useSearchParams, useRouter (Next.js)
   (filters, pagination, selected tab từ URL)
```

### 5.2 Loại Bỏ Prop Drilling

```tsx
// ❌ Prop drilling qua 4 cấp
<Page user={user}>
  <Layout user={user}>
    <Sidebar user={user}>
      <UserMenu user={user} />
    </Sidebar>
  </Layout>
</Page>

// ✅ Dùng Context cho shared state
const UserContext = createContext<User | null>(null);

export function useUser() {
  const user = useContext(UserContext);
  if (!user) throw new Error('useUser must be used within UserProvider');
  return user;
}

// Chỉ truyền một lần ở root
<UserContext.Provider value={user}>
  <Page />
</UserContext.Provider>

// Dùng ở bất kỳ đâu mà không cần prop
function UserMenu() {
  const user = useUser(); // ✅
  return <div>{user.name}</div>;
}
```

### 5.3 Server State với TanStack Query

```tsx
// hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => fetch('/api/users').then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 phút
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateUserInput) =>
      fetch('/api/users', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
```

---

## Phase 6 — Data Fetching & Server Components

### 6.1 Server vs Client Components

```tsx
// ✅ Server Component — Fetch data trực tiếp, không cần useState/useEffect
// app/dashboard/page.tsx
export default async function DashboardPage() {
  // Chạy ở server, không gửi JS xuống client
  const data = await fetchDashboardData();

  return (
    <div>
      <UserStats stats={data.stats} />
      {/* Client component chỉ ở nơi cần interactivity */}
      <InteractiveChart data={data.chartData} />
    </div>
  );
}

// ✅ Client Component — Chỉ khi thực sự cần
// components/features/dashboard/InteractiveChart.tsx
'use client';

import { useState } from 'react';

export function InteractiveChart({ data }: { data: ChartData }) {
  const [filter, setFilter] = useState('all');
  // ...
}
```

### 6.2 Streaming & Suspense

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';

export default function DashboardPage() {
  return (
    <div>
      {/* Hiển thị ngay, không chờ */}
      <DashboardHeader />

      {/* Stream từng phần, có skeleton riêng */}
      <Suspense fallback={<StatsSkeleton />}>
        <UserStats />
      </Suspense>

      <Suspense fallback={<TableSkeleton />}>
        <RecentOrders />
      </Suspense>
    </div>
  );
}
```

### 6.3 Patterns Nên Tránh

```tsx
// ❌ Fetch trong useEffect — waterfalls, no caching
useEffect(() => {
  fetch('/api/data').then(setData);
}, []);

// ❌ Fetch toàn bộ data ở root rồi pass xuống
const [allData, setAllData] = useState({});
<Child data={allData.part} />

// ✅ Fetch gần nơi sử dụng, dùng Server Components
async function UserStats() {
  const stats = await getStats(); // fetch ở đây
  return <div>{stats.total}</div>;
}
```

---

## Phase 7 — Performance & Optimization

### 7.1 Bundle Analysis

```bash
# Cài đặt và chạy bundle analyzer
npm install @next/bundle-analyzer

# next.config.ts
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

ANALYZE=true npm run build
```

### 7.2 Code Splitting & Lazy Loading

```tsx
import dynamic from 'next/dynamic';

// Lazy load component nặng
const HeavyChartLibrary = dynamic(
  () => import('@/components/features/HeavyChart'),
  {
    loading: () => <ChartSkeleton />,
    ssr: false, // Nếu chỉ chạy ở client
  }
);

// Lazy load theo điều kiện
const AdminPanel = dynamic(() => import('@/components/AdminPanel'));

function Dashboard({ isAdmin }: { isAdmin: boolean }) {
  return (
    <div>
      {isAdmin && <AdminPanel />} {/* Chỉ load khi cần */}
    </div>
  );
}
```

### 7.3 Memoization Đúng Chỗ

```tsx
// ✅ memo() — chỉ khi component thực sự re-render tốn kém
const ExpensiveList = memo(function ExpensiveList({ items }: Props) {
  return <ul>{items.map(renderItem)}</ul>;
});

// ✅ useMemo — tính toán nặng
const sortedItems = useMemo(
  () => items.sort(complexSortFn),
  [items]
);

// ✅ useCallback — khi pass function xuống memo component
const handleSubmit = useCallback((data: FormData) => {
  submitForm(data);
}, [submitForm]);

// ❌ Tránh dùng memo/useMemo/useCallback mọi nơi
// Chúng có overhead riêng, chỉ dùng khi đo lường thấy vấn đề
```

### 7.4 Image & Font Optimization

```tsx
import Image from 'next/image';

// ✅ Luôn dùng next/image thay vì <img>
<Image
  src="/hero.jpg"
  alt="Hero image"
  width={1200}
  height={600}
  priority   // cho above-the-fold images
  placeholder="blur"
  blurDataURL={blurDataUrl}
/>

// next.config.ts — font optimization
import { Inter } from 'next/font/google';

export const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
});
```

---

## Phase 8 — Testing & Validation

### 8.1 Testing Pyramid cho UI

```
        E2E Tests (Playwright / Cypress)
           Ít nhất, tốn nhất, giá trị cao
                  ▲
           Integration Tests
           (Testing Library)
          ▲            ▲
      Unit Tests    Visual Tests
   (components,    (Storybook /
     utils, hooks)  Chromatic)
```

### 8.2 Component Testing

```tsx
// components/ui/Button/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### 8.3 Visual Regression Testing

```typescript
// playwright/visual.spec.ts
import { test, expect } from '@playwright/test';

test('Button variants look correct', async ({ page }) => {
  await page.goto('/storybook/button');
  await expect(page).toHaveScreenshot('button-variants.png');
});
```

---

## Chiến Lược Thực Thi Incremental

### Refactor Không Phá Vỡ Production

```
NGUYÊN TẮC: Không bao giờ refactor + thêm feature cùng lúc.
```

**Quy trình từng bước:**

```
Step 1: Tạo file mới bên cạnh file cũ
  components/
    UserCard.tsx          ← file cũ (vẫn hoạt động)
    UserCard.new.tsx      ← file mới đang refactor

Step 2: Test file mới trong môi trường dev

Step 3: Swap — thay thế import dần dần
  // Từng page/component một
  import UserCard from './UserCard.new';

Step 4: Khi tất cả đã chuyển sang, xóa file cũ
  rm UserCard.tsx
  mv UserCard.new.tsx UserCard.tsx
```

### Ưu Tiên Refactor Theo Impact

```
High Impact, Low Risk → Làm trước
  - Đổi tên file/folder
  - Tách utility functions
  - Thêm TypeScript types
  - Xóa dead code

High Impact, High Risk → Lên kế hoạch kỹ
  - Thay đổi state management
  - Refactor data fetching strategy
  - Migrate sang Server Components

Low Impact → Để sau
  - Code style cosmetics
  - Rename variables nhỏ
```

---

## Checklist Tổng Hợp

### ✅ Trước Khi Bắt Đầu

- [ ] Audit hiện trạng codebase, document lại
- [ ] Xác định hướng refactor và mục tiêu đo lường được
- [ ] Set up branch strategy (feature branch per module)
- [ ] Đảm bảo có test coverage cơ bản trước khi refactor

### ✅ Architecture

- [ ] Folder structure rõ ràng, team đồng ý
- [ ] Barrel exports (`index.ts`) cho các module
- [ ] Path aliases (`@/components`, `@/lib`) cấu hình đúng
- [ ] Không có circular dependencies

### ✅ Components

- [ ] Không có God Component (>300 dòng)
- [ ] Tách business logic ra khỏi presentational components
- [ ] Props interface đầy đủ TypeScript, có JSDoc
- [ ] Không có prop drilling quá 2 cấp

### ✅ Styling

- [ ] Design tokens định nghĩa tập trung
- [ ] Không có magic numbers (hardcoded `margin: 13px`)
- [ ] Responsive design nhất quán
- [ ] Dark mode (nếu có) dùng CSS variables

### ✅ State Management

- [ ] Phân loại state rõ ràng (local/shared/server/URL)
- [ ] Server state dùng TanStack Query hoặc SWR
- [ ] Không fetch data trong `useEffect` trừ khi bắt buộc

### ✅ Performance

- [ ] Bundle size không tăng sau refactor
- [ ] Lazy loading cho components nặng
- [ ] `next/image` cho tất cả images
- [ ] Server Components cho data fetching

### ✅ Testing

- [ ] Unit test cho utility functions & hooks
- [ ] Component test cho UI primitives
- [ ] Không có test nào fail sau refactor

---

## Tổng Kết

Refactor hiệu quả không phải là viết lại từ đầu — mà là **cải thiện có kiểm soát**, từng bước, không làm gián đoạn sản phẩm đang chạy. Ba điều cốt lõi:

1. **Hiểu trước — Code sau**: Audit kỹ trước khi chạm vào code
2. **Incremental > Big Bang**: Thay đổi từng phần nhỏ, dễ review, dễ rollback
3. **Đo lường**: Biết mình đang cải thiện cái gì và cải thiện được bao nhiêu

> _"Make it work → Make it right → Make it fast"_
> — Kent Beck