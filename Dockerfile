# syntax=docker/dockerfile:1
# DashZen API — uv monorepo image for Render / Fly.io
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY apps/api apps/api
COPY packages packages
COPY scripts scripts

RUN uv sync --frozen --all-packages --no-dev


FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

COPY --from=builder --chown=app:app /app /app

RUN mkdir -p /app/data/avatars \
    && chown -R app:app /app/data \
    && chmod +x /app/scripts/start-api.sh /app/scripts/migrate.sh

USER app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["./scripts/start-api.sh"]
