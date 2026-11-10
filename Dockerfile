FROM node:24-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS application
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ ./
COPY --from=frontend /build/frontend/dist /app/frontend/dist
ENV PATH="/app/backend/.venv/bin:$PATH"
RUN useradd --create-home --uid 10001 inheria && chown -R inheria:inheria /app
USER inheria
EXPOSE 8010
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8010} --workers 1"]
