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

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.env"
  set +a
fi

npm run build >/tmp/trader-build.log

if [[ -f "$BACKEND_PID_FILE" ]] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
  kill "$(cat "$BACKEND_PID_FILE")" || true
fi

if [[ -f "$FRONTEND_PID_FILE" ]] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
  kill "$(cat "$FRONTEND_PID_FILE")" || true
fi

nohup env \
  PYTHONPATH="$ROOT_DIR/backend" \
  APP_ENV="${APP_ENV:-production}" \
  ALLOW_INSECURE_DEV_DEFAULTS="${ALLOW_INSECURE_DEV_DEFAULTS:-false}" \
  ADMIN_API_TOKEN="${ADMIN_API_TOKEN:?ADMIN_API_TOKEN is required}" \
  DATABASE_URL="${DATABASE_URL:?DATABASE_URL is required}" \
  BACKPACK_MODE="${BACKPACK_MODE:-mock}" \
  BACKPACK_API_BASE_URL="${BACKPACK_API_BASE_URL:-https://api.backpack.exchange}" \
  BACKPACK_API_KEY="${BACKPACK_API_KEY:-}" \
  BACKPACK_PRIVATE_KEY="${BACKPACK_PRIVATE_KEY:-}" \
  BACKPACK_WINDOW_MS="${BACKPACK_WINDOW_MS:-5000}" \
  BACKPACK_DEFAULT_SYMBOL="${BACKPACK_DEFAULT_SYMBOL:-BTC_USDC_PERP}" \
  BACKPACK_DEFAULT_INTERVAL="${BACKPACK_DEFAULT_INTERVAL:-1h}" \
  BACKPACK_DEFAULT_PRICE_SOURCE="${BACKPACK_DEFAULT_PRICE_SOURCE:-mark}" \
  BACKPACK_DEFAULT_MARKET_TYPE="${BACKPACK_DEFAULT_MARKET_TYPE:-perp}" \
  BACKPACK_ACCOUNT_LABEL="${BACKPACK_ACCOUNT_LABEL:-backpack-primary}" \
  /tmp/trader-backend-venv/bin/uvicorn backend.app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
  >"$BACKEND_LOG" 2>&1 &
echo $! >"$BACKEND_PID_FILE"

nohup npm run preview -- --host 127.0.0.1 --port 4173 >"$FRONTEND_LOG" 2>&1 &
echo $! >"$FRONTEND_PID_FILE"

echo "backend_pid=$(cat "$BACKEND_PID_FILE")"
echo "frontend_pid=$(cat "$FRONTEND_PID_FILE")"
