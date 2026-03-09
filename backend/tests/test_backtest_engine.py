from __future__ import annotations

from app.backtest_engine import build_backtest_result
from app.schemas import BacktestRequest, Candle, PriceSource, RiskControls, StrategySummary


def build_strategy() -> StrategySummary:
    return StrategySummary(
        id="strat_test",
        name="Momentum Test",
        kind="template",
        description="",
        market="BTC_USDC_PERP",
        account_id="acct_001",
        runtime="paper",
        status="healthy",
        last_backtest="",
        sharpe=0.0,
        price_source=PriceSource.LAST,
        parameters={},
    )


def build_risk_controls(**overrides) -> RiskControls:
    payload = {
        "max_open_positions": 3,
        "max_consecutive_loss": 3,
        "max_symbol_exposure": 300.0,
        "stop_loss_percent": 10.0,
        "max_trade_risk": 10.0,
        "max_slippage_percent": 0.4,
        "max_spread_percent": 5.0,
        "volatility_filter_percent": 20.0,
        "max_position_notional": 300.0,
        "daily_loss_limit": 15.0,
        "max_leverage": 3.0,
        "allowed_symbols": ["BTC_USDC_PERP"],
        "trading_window_start": "00:00",
        "trading_window_end": "23:59",
        "kill_switch_enabled": False,
        "require_mark_price": True,
        "updated_at": "2026-03-08T00:00:00Z",
    }
    payload.update(overrides)
    return RiskControls(**payload)


def build_request() -> BacktestRequest:
    return BacktestRequest(
        symbol="BTC_USDC_PERP",
        interval="1h",
        start_time=1740787200,
        end_time=1740812400,
        price_source=PriceSource.LAST,
        fee_bps=2,
        slippage_bps=4,
    )


def test_backtest_respects_symbol_allowlist() -> None:
    result = build_backtest_result(
        backtest_id="bt-allowlist",
        strategy=build_strategy(),
        request=build_request(),
        risk_controls=build_risk_controls(allowed_symbols=["ETH_USDC_PERP"]),
        candles=[
            Candle(timestamp="2026-03-01T00:00:00Z", open=100.0, high=101.0, low=99.0, close=100.5, volume=1000),
            Candle(timestamp="2026-03-01T01:00:00Z", open=100.5, high=102.0, low=100.0, close=101.5, volume=1000),
            Candle(timestamp="2026-03-01T02:00:00Z", open=101.5, high=103.0, low=101.0, close=102.5, volume=1000),
        ],
        created_at="2026-03-08T00:00:00Z",
        exchange_id="mock",
        market_type="perp",
    )

    assert result.trade_markers == []
    assert any("outside the allowed risk universe" in item for item in result.chart_warnings)


def test_backtest_halts_new_entries_after_consecutive_loss_limit() -> None:
    result = build_backtest_result(
        backtest_id="bt-loss-limit",
        strategy=build_strategy(),
        request=build_request(),
        risk_controls=build_risk_controls(max_consecutive_loss=1),
        candles=[
            Candle(timestamp="2026-03-01T00:00:00Z", open=100.0, high=101.0, low=99.0, close=100.5, volume=1000),
            Candle(timestamp="2026-03-01T01:00:00Z", open=100.5, high=101.0, low=100.0, close=100.8, volume=1000),
            Candle(timestamp="2026-03-01T02:00:00Z", open=100.8, high=101.2, low=100.5, close=101.0, volume=1000),
            Candle(timestamp="2026-03-01T03:00:00Z", open=101.0, high=101.1, low=88.0, close=89.0, volume=1000),
            Candle(timestamp="2026-03-01T04:00:00Z", open=89.0, high=92.0, low=88.5, close=91.5, volume=1000),
            Candle(timestamp="2026-03-01T05:00:00Z", open=91.5, high=95.0, low=91.0, close=94.0, volume=1000),
            Candle(timestamp="2026-03-01T06:00:00Z", open=94.0, high=98.0, low=93.5, close=97.5, volume=1000),
        ],
        created_at="2026-03-08T00:00:00Z",
        exchange_id="mock",
        market_type="perp",
    )

    actions = [marker.action for marker in result.trade_markers]
    assert actions.count("open") == 1
    assert "stop" in actions
    assert all(action in {"open", "stop"} for action in actions)
    assert any("consecutive losing cycles" in item for item in result.chart_warnings)
