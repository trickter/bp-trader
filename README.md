# Backpack Quant Console

Admin-only crypto quant trading scaffold built for a Backpack-first integration model.

## Stack

- Frontend: React + TypeScript + Vite + Tailwind
- Backend: FastAPI + Python
- Database: PostgreSQL
- Runtime: local commands or `docker compose`

## Backpack Adapter Mode

The backend is prepared for two data modes:

- `BACKPACK_MODE=mock`: local fixture data for UI development
- `BACKPACK_MODE=live`: real REST calls to Backpack Exchange

When `live` is enabled, set:

- `BACKPACK_API_BASE_URL`
- `BACKPACK_API_KEY`
- `BACKPACK_PRIVATE_KEY`
- `BACKPACK_WINDOW_MS`
- `BACKPACK_DEFAULT_SYMBOL`
- `BACKPACK_DEFAULT_INTERVAL`
- `BACKPACK_DEFAULT_PRICE_SOURCE`
- `BACKPACK_DEFAULT_MARKET_TYPE`
- `BACKPACK_ACCOUNT_LABEL`

## V1 Surfaces

- `Profile`: summary, asset balances, open positions, account event ledger
- `Strategy Lab`: template and script strategies under one normalized contract
- `Backtests`: K-line backtests with open/close markers
- `Market Pulse`: feed freshness and market semantics
- `Execution`: future live-ready order lifecycle skeleton
- `Risk Controls`, `Alerts`, `Settings`

## Core Constraints

- Explicit `priceSource = last | mark | index`
- Database time standard is `timestamptz`
- Account activity is modeled as an event ledger
- Execution identity is split between `clientOrderId` and `exchangeOrderId`
- Strategy scripts are expected to run inside a deterministic restricted Python runtime

## Repo Layout

- `src/`: frontend admin console
- `backend/app/`: FastAPI app and typed response schemas
- `backend/sql/001_initial_schema.sql`: normalized PostgreSQL schema
- `docker-compose.yml`: local frontend + backend + postgres stack

## API Surface

- `GET /api/profile/summary`
- `GET /api/profile/assets`
- `GET /api/profile/positions`
- `GET /api/profile/account-events`
- `GET /api/strategies`
- `GET /api/backtests/:id`
- `GET /api/markets/:symbol/klines`
- `GET /api/markets/pulse`
- `GET /api/alerts`
- `GET /api/settings/accounts`
- `POST /api/strategies/templates/:template_id/backtests`
- `POST /api/strategies/scripts/:strategy_id/backtests`

## Local Run

```bash
cp .env.example .env
npm install
npm run dev
```

Backend:

```bash
python3 -m venv .venv
. .venv/bin/activate
PIP_INDEX_URL=https://pypi.org/simple pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

To switch from mock data to Backpack live mode:

```bash
cp .env.example .env
# fill BACKPACK_API_KEY and BACKPACK_PRIVATE_KEY
BACKPACK_MODE=live uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Compose:

```bash
docker compose up --build
```

Frontend: `http://localhost:5173`  
Backend docs: `http://localhost:8000/docs`

## Notes

- PostgreSQL remains the source of truth for balances, positions, backtests, execution state, risk rules, and audits.
- Backpack signing uses ED25519 credentials from environment variables; do not commit real keys.
- `BACKPACK_PRIVATE_KEY` should be provided only through local env or secret injection, never hardcoded.
- Secrets are intended to be encrypted at rest and never re-shown after write.
