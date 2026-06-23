# 00 — Prerequisites (Studio + Backend)

> Điều kiện tiên quyết trước khi implement Auth UI.
>
> Tương đương [Backend 00-docker-postgres.md](../../Backend/auth/00-docker-postgres.md) — nhưng góc nhìn **frontend developer**.

---

## 1. Backend & infra phải chạy

Auth UI **không mock** — gọi API thật trong dev.

```bash
# Từ repo root
docker compose -f infra/compose/docker-compose.yml up -d   # postgres + mailpit
alembic -c packages/db/alembic.ini upgrade head
uvicorn api.main:app --reload --app-dir apps/api/src --port 8000
```

| Service | URL | Dùng cho |
|---------|-----|----------|
| FastAPI | `http://localhost:8000` | Auth endpoints |
| Swagger | `http://localhost:8000/docs` | Contract reference |
| Mailpit UI | `http://localhost:8025` | Đọc OTP email khi dev |
| PostgreSQL | `localhost:5432` | (BE only) |

Copy `.env` từ `.env.example` (root) — đảm bảo `CORS_ORIGINS` có `http://localhost:3000`.

---

## 2. Studio app hiện trạng

```
apps/studio/
├── app/
│   ├── layout.tsx          # Root layout — cần providers
│   ├── globals.css
│   └── page.tsx            # Default create-next-app — sẽ refactor
├── package.json            # Next.js 15
├── .env.local.example      # NEXT_PUBLIC_API_URL
└── (chưa có) modules/, lib/api/, middleware.ts
```

**Cần scaffold thêm** (thứ tự):

1. `middleware.ts` — route guard skeleton
2. `lib/api/` — API client
3. `modules/auth/` — auth module (forms, hooks)
4. `components/ui/` — shadcn components
5. `app/(auth)/` + `app/(app)/` — route groups

---

## 3. Dependencies cần cài (studio)

```bash
cd apps/studio
npm install @tanstack/react-query zustand react-hook-form @hookform/resolvers zod
npx shadcn@latest init    # Tailwind 4 + components path
npx shadcn@latest add button input label card form toast
```

| Package | Vai trò Auth slice |
|---------|------------------|
| `react-hook-form` + `zod` | Form validation login/register/verify |
| `@tanstack/react-query` | `useMe()`, cache user profile |
| `zustand` | `authStore` ephemeral (optional), `toastStore` |
| `shadcn/ui` | Form primitives, Card layout auth pages |

> **Không** cài thư viện JWT client-side — token chỉ trong httpOnly cookies.

---

## 4. Environment

```env
# apps/studio/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

| Biến | Bắt buộc | Ghi chú |
|------|----------|---------|
| `NEXT_PUBLIC_API_URL` | ✓ | Base URL API — **không** trailing slash |

Production: set trên Vercel/hosting tương ứng staging/prod API URL.

---

## 5. CORS & cookies (dev checklist)

| Kiểm tra | Expected |
|----------|----------|
| Studio origin | `http://localhost:3000` |
| API `allow_credentials` | `true` |
| Cookie `SameSite` | `Lax` — OK same-site cross-port localhost |
| Cookie names | `dashzen_access_token`, `dashzen_refresh_token` |

Nếu login thành công nhưng `/app` redirect về login → kiểm tra CORS + `credentials: 'include'`.

---

## 6. Git branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/auth-ui    # đã tạo
```

Mọi commit Auth UI trên `feature/auth-ui` → PR vào `develop`.

---

## 7. Definition of ready

Bắt đầu code Auth UI khi:

- [ ] `POST /v1/auth/login` trả 200 + Set-Cookie (test Swagger/curl)
- [ ] `POST /v1/auth/register` trả 201 + `requires_verification: true`
- [ ] Mailpit nhận email OTP sau register
- [ ] `apps/studio` chạy `npm run dev` trên port 3000
- [ ] shadcn/ui init xong
- [ ] `.env.local` có `NEXT_PUBLIC_API_URL`
