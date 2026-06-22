# 00 — Docker PostgreSQL (Auth prerequisite)

> Auth Slice **bắt buộc** PostgreSQL chạy qua Docker Compose — không dùng SQLite, không cài Postgres native cho dev.
>
> **File:** [`infra/compose/docker-compose.yml`](../../../../infra/compose/docker-compose.yml)

---

## 1. Tại sao Docker Postgres cho Auth

| Lý do | Chi tiết |
|-------|----------|
| Align plan 01 | App DB = PostgreSQL |
| Parity prod/dev | Cùng engine với staging/prod |
| User persistence | Bảng `users` + Alembic migrations |
| Task ownership | `tasks.user_id` FK → `users.id` (Slice 1b) |
| Reproducible | `docker compose up` là đủ cho mọi dev |

**Auth Slice chỉ cần Postgres** — Redis/MinIO/Qdrant thêm ở Phase 1 foundation sau.

---

## 2. Docker Compose service

```yaml
# infra/compose/docker-compose.yml

services:
  postgres:
    image: postgres:16-alpine
    container_name: dashzen-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: dashzen
      POSTGRES_PASSWORD: dashzen
      POSTGRES_DB: dashzen
    volumes:
      - dashzen_pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dashzen -d dashzen"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  dashzen_pg_data:
```

| Setting | Giá trị |
|---------|---------|
| Image | `postgres:16-alpine` |
| Host port | `5432` |
| User / Password / DB | `dashzen` / `dashzen` / `dashzen` |
| Volume | `dashzen_pg_data` — persist data giữa restart |

---

## 3. Environment alignment

`.env` (copy từ `.env.example`) phải khớp Docker:

```env
DATABASE_URL=postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen
```

| Component | Connection |
|-----------|------------|
| FastAPI (host) | `localhost:5432` — port publish từ container |
| pytest integration | Cùng `DATABASE_URL` |
| Alembic | `packages/db/alembic.ini` → env `DATABASE_URL` |

> API chạy **trên host** (uvicorn), DB **trong container** — pattern chuẩn dev.

---

## 4. Quick start

```bash
# 1. Từ repo root
cp .env.example .env
# Đổi JWT_SECRET_KEY — không dùng default

# 2. Start Postgres
docker compose -f infra/compose/docker-compose.yml up -d

# 3. Verify healthy
docker compose -f infra/compose/docker-compose.yml ps
docker compose -f infra/compose/docker-compose.yml logs postgres

# 4. Test connection (optional)
docker exec -it dashzen-postgres psql -U dashzen -d dashzen -c '\dt'
```

**Stop / reset:**

```bash
# Stop giữ data
docker compose -f infra/compose/docker-compose.yml down

# Stop + xóa volume (reset DB)
docker compose -f infra/compose/docker-compose.yml down -v
```

---

## 5. Migrations (sau khi có User model)

```bash
# Từ repo root — sau khi implement packages/db
uv run alembic -c packages/db/alembic.ini upgrade head
```

Thứ tự Auth backend:

1. Docker Postgres up + healthy
2. `User` model + migration `001_create_users`
3. Auth routes

---

## 6. Dev seed user (optional)

```env
# .env
DEV_USER_EMAIL=dev@dashzen.local
DEV_USER_PASSWORD=devpass123
```

CLI seed chạy **một lần** sau migration — tạo user dev để test login không cần register UI.

---

## 7. Troubleshooting

| Vấn đề | Cách xử lý |
|--------|------------|
| Port 5432 đã dùng | Đổi `"5433:5432"` + `DATABASE_URL` port 5433 |
| `connection refused` | Chờ healthcheck; `docker compose ps` |
| Migration fail | Check `DATABASE_URL`; Postgres có chạy không |
| Data cũ / schema lỗi | `docker compose down -v` + migrate lại |

---

## 8. Phase 1 foundation (mở rộng sau)

Khi sang Phase 1 full, thêm vào cùng `docker-compose.yml`:

```yaml
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

Auth Slice **không phụ thuộc** Redis.

---

## 9. Checklist Docker (trước khi code Auth)

- [ ] `infra/compose/docker-compose.yml` tồn tại
- [ ] `.env` có `DATABASE_URL` khớp compose
- [ ] `docker compose up -d` → postgres **healthy**
- [ ] `psql` hoặc API connect thành công
