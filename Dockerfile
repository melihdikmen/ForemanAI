# syntax=docker/dockerfile:1
# Production image: FastAPI API + the built React UI, served from one container.
#
#   docker build -t foremanai .
#   docker run --env-file .env -p 8080:8080 foremanai
#
# Stage 1 builds the UI with Node; stage 2 is the Python runtime. Node never ends
# up in the final image, only the static files under ui/dist.

# ---------- Stage 1: build the React UI ----------
FROM node:22-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
# API and UI share one origin inside the image, so the UI calls /ask directly
# instead of the /api prefix that the Vite dev proxy rewrites.
ENV VITE_API_BASE=""
RUN npm run build

# ---------- Stage 2: Python API ----------
FROM python:3.12-slim AS api

# uv binary, copied from the official image (pinned so builds stay reproducible).
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Install dependencies first so this layer is cached until the lock file changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Download the embedding model into the image. Cloud Run has no persistent disk,
# so without this every cold start would fetch the model from the network.
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
ENV FASTEMBED_CACHE_PATH=/app/.fastembed_cache
RUN /app/.venv/bin/python -c "from fastembed import TextEmbedding; TextEmbedding('${EMBEDDING_MODEL}')"

# Application code, migrations and the synthetic manuals (needed to build the index).
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY data ./data
COPY --from=ui /ui/dist ./ui/dist
COPY docker/entrypoint.sh ./entrypoint.sh

# Run as a non-root user; nothing in the container needs root at runtime.
RUN useradd --system --create-home app && chown -R app:app /app
USER app

ENV PATH="/app/.venv/bin:$PATH" \
    PORT=8080
EXPOSE 8080

# Applies migrations, then starts uvicorn on $PORT (Cloud Run sets PORT).
CMD ["./entrypoint.sh"]
