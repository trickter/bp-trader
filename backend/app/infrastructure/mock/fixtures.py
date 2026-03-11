from __future__ import annotations

from ...schemas import (
    AccountEvent,
    AlertEvent,
    AssetBalance,
    BacktestResult,
    Candle,
    EquityPoint,
    EventOrigin,
    EventType,
    ExchangeAccount,
    MarketMetric,
    Position,
    PriceSource,
    ProfileSummary,
    RiskControls,
    StrategySummary,
    TradeMarker,
)


PROFILE_SUMMARY = ProfileSummary(
    total_equity=182430.77,
    available_margin=120230.34,
    unrealized_pnl=1982.41,
    realized_pnl_24h=6240.92,
    win_rate=71.4,
    risk_level="disciplined",
    price_source=PriceSource.MARK,
    synced_at="2026-03-08T11:35:20Z",
)

ASSET_BALANCES = [
    AssetBalance(asset="USDC", available=102340.12, locked=12000.0, collateral_value=114340.12, portfolio_weight=62.7, change_24h=0.0),
    AssetBalance(asset="BTC", available=1.82, locked=0.4, collateral_value=61140.48, portfolio_weight=33.5, change_24h=1.8),
    AssetBalance(asset="SOL", available=94.0, locked=12.0, collateral_value=5110.17, portfolio_weight=2.8, change_24h=-0.9),
]

POSITIONS = [
    Position(symbol="BTC_USDC_PERP", side="long", quantity=0.95, entry_price=61520, mark_price=62880, liquidation_price=55210, unrealized_pnl=1292, margin_used=13420, opened_at="2026-03-08T01:10:00Z", price_source=PriceSource.MARK, exchange_extra={"native_symbol": "BTC_USDC_PERP", "funding_interval_hours": 8}),
    Position(symbol="SOL_USDC_PERP", side="short", quantity=180, entry_price=172.8, mark_price=168.1, liquidation_price=213.5, unrealized_pnl=846, margin_used=4220, opened_at="2026-03-08T03:42:00Z", price_source=PriceSource.MARK, exchange_extra={"native_symbol": "SOL_USDC_PERP", "funding_interval_hours": 8}),
    Position(symbol="ETH_USDC_PERP", side="long", quantity=6.5, entry_price=3212, mark_price=3188, liquidation_price=2802, unrealized_pnl=-156, margin_used=2950, opened_at="2026-03-07T23:22:00Z", price_source=PriceSource.MARK, exchange_extra={"native_symbol": "ETH_USDC_PERP", "funding_interval_hours": 8}),
]

ACCOUNT_EVENTS = [
    AccountEvent(id="evt_001", event_type=EventType.TRADE_FILL, origin=EventOrigin.STRATEGY, asset="BTC", amount=0.3, pnl_effect=421.8, position_effect="Opened additional long exposure", occurred_at="2026-03-08T04:20:00Z"),
    AccountEvent(id="evt_002", event_type=EventType.FUNDING_SETTLEMENT, origin=EventOrigin.SYSTEM, asset="USDC", amount=42.14, pnl_effect=42.14, position_effect="Funding credit on BTC perp", occurred_at="2026-03-08T04:00:00Z"),
    AccountEvent(id="evt_003", event_type=EventType.FEE_CHARGE, origin=EventOrigin.SYSTEM, asset="USDC", amount=-18.77, pnl_effect=-18.77, position_effect="Taker fee on SOL short add", occurred_at="2026-03-08T03:42:05Z"),
    AccountEvent(id="evt_004", event_type=EventType.COLLATERAL_CONVERSION, origin=EventOrigin.RISK, asset="BTC", amount=-0.08, pnl_effect=0.0, position_effect="Converted BTC collateral to USDC margin", occurred_at="2026-03-08T02:15:00Z"),
]

STRATEGIES = [
    StrategySummary(id="strat_001", name="Momentum Burst", kind="template", description="Breakout continuation system with ATR volatility filter.", market="BTC_USDC_PERP", account_id="acct_001", runtime="paper", status="healthy", last_backtest="2026-03-08T10:12:00Z", sharpe=2.14, price_source=PriceSource.LAST, parameters={"fast_ema": 21, "slow_ema": 55, "atr_stop": 2.5, "live_enabled": True, "execution_weight": 0.6, "poll_interval_seconds": 30}),
    StrategySummary(id="strat_002", name="Funding Carry Stack", kind="script", description="Bias-adjusted carry harvesting with inventory clamp.", market="SOL_USDC_PERP", account_id="acct_001", runtime="paper", status="healthy", last_backtest="2026-03-08T09:48:00Z", sharpe=1.76, price_source=PriceSource.MARK, parameters={"carry_threshold": 0.0002, "inventory_cap": 180}),
    StrategySummary(id="strat_003", name="Mean Reversion Net", kind="template", description="Index-referenced fade with session gating.", market="ETH_USDC_PERP", account_id="acct_002", runtime="disabled", status="idle", last_backtest="", sharpe=0.0, price_source=PriceSource.INDEX, parameters={"z_entry": 2.1, "z_exit": 0.7}),
]

CANDLES = [
    Candle(timestamp="2026-03-01T00:00:00Z", open=60020, high=60640, low=59600, close=60320, volume=1240),
    Candle(timestamp="2026-03-02T00:00:00Z", open=60320, high=61100, low=60110, close=60980, volume=1580),
    Candle(timestamp="2026-03-03T00:00:00Z", open=60980, high=61840, low=60720, close=61720, volume=1640),
    Candle(timestamp="2026-03-04T00:00:00Z", open=61720, high=62010, low=61040, close=61250, volume=1490),
    Candle(timestamp="2026-03-05T00:00:00Z", open=61250, high=62510, low=61180, close=62180, volume=1770),
    Candle(timestamp="2026-03-06T00:00:00Z", open=62180, high=63110, low=61970, close=62940, volume=1810),
    Candle(timestamp="2026-03-07T00:00:00Z", open=62940, high=63300, low=62460, close=62820, volume=1680),
]

BACKTEST_RESULT = BacktestResult(
    id="demo",
    strategy_id="strat_001",
    strategy_kind="template",
    strategy_name="BTC Momentum Burst",
    exchange_id="backpack",
    market_type="perp",
    symbol="BTC_USDC_PERP",
    interval="1d",
    start_time=1740787200,
    end_time=1741305600,
    price_source=PriceSource.LAST,
    chart_price_source=PriceSource.LAST,
    fee_bps=2.0,
    slippage_bps=4.0,
    status="completed",
    created_at="2026-03-08T10:12:00Z",
    completed_at="2026-03-08T10:12:02Z",
    total_return=28.4,
    max_drawdown=-7.9,
    sharpe=2.47,
    win_rate=68.3,
    candles=CANDLES,
    trade_markers=[
        TradeMarker(id="tm_001", timestamp="2026-03-01T06:00:00Z", candle_timestamp="2026-03-01T00:00:00Z", action="open", type="open", side="long", price=60320, qty=0.25, reason="Breakout above prior day high", related_trade_id="trade_001", related_order_id="order_001"),
        TradeMarker(id="tm_002", timestamp="2026-03-03T12:00:00Z", candle_timestamp="2026-03-03T00:00:00Z", action="close", type="close", side="long", price=61720, qty=0.25, reason="Trailing stop tightened after expansion", related_trade_id="trade_002", related_order_id="order_002"),
        TradeMarker(id="tm_003", timestamp="2026-03-04T07:00:00Z", candle_timestamp="2026-03-04T00:00:00Z", action="open", type="open", side="long", price=61250, qty=0.25, reason="Momentum reset confirmed on 1h bar", related_trade_id="trade_003", related_order_id="order_003"),
        TradeMarker(id="tm_004", timestamp="2026-03-06T16:00:00Z", candle_timestamp="2026-03-06T00:00:00Z", action="close", type="close", side="long", price=62940, qty=0.25, reason="Target reached with funding filter intact", related_trade_id="trade_004", related_order_id="order_004"),
    ],
    equity_curve=[
        EquityPoint(timestamp="2026-03-01T00:00:00Z", equity=100.0),
        EquityPoint(timestamp="2026-03-02T00:00:00Z", equity=103.0),
        EquityPoint(timestamp="2026-03-03T00:00:00Z", equity=109.0),
        EquityPoint(timestamp="2026-03-04T00:00:00Z", equity=106.0),
        EquityPoint(timestamp="2026-03-05T00:00:00Z", equity=114.0),
        EquityPoint(timestamp="2026-03-06T00:00:00Z", equity=123.0),
        EquityPoint(timestamp="2026-03-07T00:00:00Z", equity=128.4),
    ],
    chart_warnings=[],
)

MARKET_PULSE = [
    MarketMetric(label="BTC depth", value="WS realtime", freshness="sub-second", tone="positive"),
    MarketMetric(label="Open interest", value="1.42B", freshness="60s cadence", tone="neutral"),
    MarketMetric(label="Funding", value="+0.010%", freshness="polled", tone="neutral"),
    MarketMetric(label="Mark price", value="$62,880", freshness="realtime", tone="positive"),
    MarketMetric(label="Index price", value="$62,842", freshness="realtime", tone="neutral"),
    MarketMetric(label="Latency budget", value="84ms", freshness="observed", tone="positive"),
]

EXCHANGE_ACCOUNTS = [
    ExchangeAccount(id="acct_001", exchange="backpack", label="prod-perp-main", market_type="perp", last_credential_rotation="2026-03-04T09:30:00Z", status="healthy"),
    ExchangeAccount(id="acct_002", exchange="paper", label="paper-sim", market_type="perp", last_credential_rotation="2026-03-01T00:00:00Z", status="attention"),
]

MARKET_SYMBOLS = [
    "BTC_USDC_PERP",
    "ETH_USDC_PERP",
    "SOL_USDC_PERP",
    "DOGE_USDC_PERP",
    "BNB_USDC_PERP",
]

RISK_CONTROLS = RiskControls(
    max_open_positions=3,
    max_consecutive_loss=3,
    max_symbol_exposure=150,
    stop_loss_percent=10,
    max_trade_risk=10,
    max_slippage_percent=0.4,
    max_spread_percent=0.3,
    volatility_filter_percent=8,
    max_position_notional=300,
    daily_loss_limit=15,
    max_leverage=3,
    allowed_symbols=MARKET_SYMBOLS,
    trading_window_start="00:00",
    trading_window_end="23:59",
    kill_switch_enabled=False,
    require_mark_price=True,
    updated_at="2026-03-08T11:40:00Z",
)

ALERTS = [
    AlertEvent(id="alert_001", level="info", title="Backtest completed", detail="BTC Momentum Burst finished in 18.4s with deterministic seed 42.", occurred_at="2026-03-08T11:12:00Z"),
    AlertEvent(id="alert_002", level="warning", title="Market data freshness degraded", detail="SOL open interest is 73s behind expected cadence.", occurred_at="2026-03-08T11:06:00Z"),
    AlertEvent(id="alert_003", level="critical", title="Credential rotated", detail="Backpack prod key was replaced and old signing material invalidated.", occurred_at="2026-03-08T10:40:00Z"),
]
