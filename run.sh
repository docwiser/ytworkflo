#!/usr/bin/env bash
# ytworkflo — development server launcher

set -e

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
RELOAD=${RELOAD:-true}

echo "🎬 Starting ytworkflo on http://$HOST:$PORT"
echo "📖 Swagger UI  → http://localhost:$PORT/docs"
echo "📘 ReDoc       → http://localhost:$PORT/redoc"
echo "🔌 OpenAPI JSON→ http://localhost:$PORT/openapi.json"
echo ""

uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  ${RELOAD:+--reload} \
  --log-level info
