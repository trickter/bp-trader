CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'price_source') THEN
    CREATE TYPE price_source AS ENUM ('last', 'mark', 'index');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_event_type') THEN
    CREATE TYPE account_event_type AS ENUM (
      'trade_fill',
      'funding_settlement',
      'fee_charge',
      'deposit',
      'withdrawal',
      'liquidation',
      'adl',
      'collateral_conversion',
      'manual_adjustment'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_origin') THEN
    CREATE TYPE event_origin AS ENUM ('strategy', 'manual', 'system', 'risk');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'execution_mode') THEN
    CREATE TYPE execution_mode AS ENUM ('disabled', 'paper', 'live');
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS exchange_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id TEXT NOT NULL,
  account_label TEXT NOT NULL,
  market_type TEXT NOT NULL,
  account_scope TEXT NOT NULL DEFAULT 'admin',
  status TEXT NOT NULL DEFAULT 'healthy',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS exchange_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_account_id UUID NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
  key_label TEXT NOT NULL,
  public_key TEXT NOT NULL,
  encrypted_private_key BYTEA NOT NULL,
  encryption_key_version TEXT NOT NULL,
  last_rotated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id TEXT NOT NULL,
  symbol_normalized TEXT NOT NULL,
  symbol_native TEXT NOT NULL,
  market_type TEXT NOT NULL,
  base_asset TEXT NOT NULL,
  quote_asset TEXT NOT NULL,
  tick_size NUMERIC(24, 12) NOT NULL,
  step_size NUMERIC(24, 12) NOT NULL,
  min_notional NUMERIC(24, 12),
  price_precision INTEGER NOT NULL,
  qty_precision INTEGER NOT NULL,
  funding_interval_seconds INTEGER,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (exchange_id, symbol_normalized)
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_account_id UUID NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
  total_equity NUMERIC(24, 8) NOT NULL,
  available_margin NUMERIC(24, 8) NOT NULL,
  unrealized_pnl NUMERIC(24, 8) NOT NULL,
  realized_pnl_24h NUMERIC(24, 8) NOT NULL,
  price_source price_source NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS asset_balances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_snapshot_id UUID NOT NULL REFERENCES portfolio_snapshots(id) ON DELETE CASCADE,
  asset TEXT NOT NULL,
  available NUMERIC(24, 8) NOT NULL,
  locked NUMERIC(24, 8) NOT NULL,
  collateral_value NUMERIC(24, 8) NOT NULL,
  portfolio_weight NUMERIC(10, 4) NOT NULL,
  price_source price_source NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS positions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_account_id UUID NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
  market_metadata_id UUID REFERENCES market_metadata(id),
  symbol_normalized TEXT NOT NULL,
  side TEXT NOT NULL,
  quantity NUMERIC(24, 8) NOT NULL,
  entry_price NUMERIC(24, 8) NOT NULL,
  mark_price NUMERIC(24, 8) NOT NULL,
  liquidation_price NUMERIC(24, 8),
  unrealized_pnl NUMERIC(24, 8) NOT NULL,
  margin_used NUMERIC(24, 8) NOT NULL,
  price_source price_source NOT NULL,
  exchange_extra JSONB NOT NULL DEFAULT '{}'::jsonb,
  opened_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_account_id UUID NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
  symbol_normalized TEXT NOT NULL,
  client_order_id TEXT NOT NULL,
  exchange_order_id TEXT,
  source TEXT NOT NULL,
  origin_event TEXT,
  status TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  quantity NUMERIC(24, 8) NOT NULL,
  limit_price NUMERIC(24, 8),
  submitted_at TIMESTAMPTZ,
  exchange_created_at TIMESTAMPTZ,
  last_update_at TIMESTAMPTZ,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (exchange_account_id, client_order_id)
);

CREATE TABLE IF NOT EXISTS fills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID REFERENCES orders(id),
  exchange_account_id UUID NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
  symbol_normalized TEXT NOT NULL,
  fill_type account_event_type NOT NULL,
  event_origin event_origin NOT NULL,
  price NUMERIC(24, 8),
  quantity NUMERIC(24, 8),
  fee_asset TEXT,
  fee_amount NUMERIC(24, 8),
  pnl_effect NUMERIC(24, 8),
  occurred_at TIMESTAMPTZ NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS account_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_account_id UUID NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
  event_type account_event_type NOT NULL,
  event_origin event_origin NOT NULL,
  asset TEXT NOT NULL,
  amount NUMERIC(24, 8) NOT NULL,
  pnl_effect NUMERIC(24, 8) NOT NULL DEFAULT 0,
  position_effect TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  strategy_kind TEXT NOT NULL,
  execution_mode execution_mode NOT NULL DEFAULT 'disabled',
  default_price_source price_source NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS strategy_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  strategy_spec JSONB NOT NULL,
  code_hash TEXT,
  dependency_profile TEXT,
  runtime_version TEXT,
  parameter_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (strategy_id, version_number)
);

CREATE TABLE IF NOT EXISTS strategy_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_version_id UUID NOT NULL REFERENCES strategy_versions(id) ON DELETE CASCADE,
  exchange_account_id UUID REFERENCES exchange_accounts(id),
  execution_mode execution_mode NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  ended_at TIMESTAMPTZ,
  log_summary TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS backtest_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_version_id UUID NOT NULL REFERENCES strategy_versions(id) ON DELETE CASCADE,
  symbol_normalized TEXT NOT NULL,
  interval TEXT NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  price_source price_source NOT NULL,
  fee_bps NUMERIC(12, 4) NOT NULL,
  slippage_bps NUMERIC(12, 4) NOT NULL,
  total_return NUMERIC(12, 4) NOT NULL,
  max_drawdown NUMERIC(12, 4) NOT NULL,
  sharpe NUMERIC(12, 4) NOT NULL,
  win_rate NUMERIC(12, 4) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS backtest_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  backtest_run_id UUID NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
  marker_type TEXT NOT NULL,
  side TEXT NOT NULL,
  marker_price NUMERIC(24, 8) NOT NULL,
  reason TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS backtest_equity_points (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  backtest_run_id UUID NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
  occurred_at TIMESTAMPTZ NOT NULL,
  equity NUMERIC(24, 8) NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_intents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_run_id UUID REFERENCES strategy_runs(id),
  symbol_normalized TEXT NOT NULL,
  side TEXT NOT NULL,
  requested_quantity NUMERIC(24, 8) NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL,
  origin_event TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS execution_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_intent_id UUID NOT NULL REFERENCES execution_intents(id) ON DELETE CASCADE,
  client_order_id TEXT NOT NULL,
  exchange_order_id TEXT,
  submitted_at TIMESTAMPTZ,
  exchange_created_at TIMESTAMPTZ,
  last_update_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (client_order_id)
);

CREATE TABLE IF NOT EXISTS execution_transitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_order_id UUID NOT NULL REFERENCES execution_orders(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status TEXT NOT NULL,
  transition_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_account_id UUID REFERENCES exchange_accounts(id),
  rule_name TEXT NOT NULL,
  rule_scope TEXT NOT NULL,
  rule_config JSONB NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_account_symbol ON positions(exchange_account_id, symbol_normalized);
CREATE INDEX IF NOT EXISTS idx_account_events_account_time ON account_events(exchange_account_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy_created ON backtest_runs(strategy_version_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_orders_status ON execution_orders(status);

CREATE TABLE IF NOT EXISTS app_execution_runtime_state (
  singleton_id SMALLINT PRIMARY KEY DEFAULT 1,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_live_strategy_states (
  strategy_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_execution_orders_log (
  id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_execution_events_log (
  id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
