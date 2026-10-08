#!/bin/sh
# Production start: apply database migrations, then serve. PORT is provided by the host (Render).
set -e
alembic upgrade head
exec uvicorn rivalry.api:app --host 0.0.0.0 --port "${PORT:-8000}"
