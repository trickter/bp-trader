#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"
BACKEND_LOG="$RUNTIME_DIR/backend.log"
FRONTEND_LOG="$RUNTIME_DIR/frontend.log"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"

mkdir -p "$RUNTIME_DIR"

cd "$ROOT_DIR"

npm run build >/tmp/trader-build.log

if [[ -f "$BACKEND_PID_FILE" ]] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
  kill "$(cat "$BACKEND_PID_FILE")" || true
fi

if [[ -f "$FRONTEND_PID_FILE" ]] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
  kill "$(cat "$FRONTEND_PID_FILE")" || true
fi

nohup env \
  PYTHONPATH="$ROOT_DIR/backend" \
  APP_ENV=development \
  ALLOW_INSECURE_DEV_DEFAULTS=true \
  ADMIN_API_TOKEN=dev-admin-token \
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trader \
  /tmp/trader-backend-venv/bin/uvicorn backend.app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
  >"$BACKEND_LOG" 2>&1 &
echo $! >"$BACKEND_PID_FILE"

nohup npm run preview -- --host 127.0.0.1 --port 4173 >"$FRONTEND_LOG" 2>&1 &
echo $! >"$FRONTEND_PID_FILE"

echo "backend_pid=$(cat "$BACKEND_PID_FILE")"
echo "frontend_pid=$(cat "$FRONTEND_PID_FILE")"
