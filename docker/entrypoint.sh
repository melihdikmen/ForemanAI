#!/bin/sh
# Container entrypoint: apply pending migrations, then serve the API.
# Seeding and index building are one-off commands, run separately:
#   docker compose run --rm api python -m app.seed
#   docker compose run --rm api python -m app.rag.index
set -e

alembic upgrade head
exec uvicorn app.api.main:app --host 0.0.0.0 --port "${PORT:-8080}"
