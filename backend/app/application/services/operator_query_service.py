from __future__ import annotations

from datetime import UTC, datetime

from ...domain.shared.enums import PriceSource
from ...schemas import AgentCapability, AgentContext, RiskControls
from ..ports.repositories import QuantOperatorGateway, RiskControlsRepository


class OperatorQueryService:
    def __init__(
        self,
        *,
        gateway: QuantOperatorGateway,
        risk_controls_repository: RiskControlsRepository,
        settings_obj,
        default_symbol: str,
    ) -> None:
        self._gateway = gateway
        self._risk_controls_repository = risk_controls_repository
        self._settings = settings_obj
        self._default_symbol = default_symbol

    async def profile_summary(self) -> dict[str, object]:
        snapshot = await self._gateway.fetch_profile_snapshot(PriceSource.MARK)
        return snapshot.summary.data.model_dump(by_alias=True)

    async def profile_assets(self) -> list[dict[str, object]]:
        snapshot = await self._gateway.fetch_profile_snapshot(PriceSource.MARK)
        return [item.data.model_dump(by_alias=True) for item in snapshot.assets.items]

    async def profile_positions(self) -> list[dict[str, object]]:
        snapshot = await self._gateway.fetch_profile_snapshot(PriceSource.MARK)
        return [item.data.model_dump(by_alias=True) for item in snapshot.positions.items]

    async def profile_account_events(self) -> list[dict[str, object]]:
        events = await self._gateway.fetch_account_events(symbol=None, limit=50)
        return [item.data.model_dump(by_alias=True) for item in events.items]

    async def market_pulse(self, symbol: str) -> list[dict[str, object]]:
        metrics = await self._gateway.fetch_market_pulse(symbol)
        return [item.data.model_dump(by_alias=True) for item in metrics.items]

    async def default_market_pulse(self) -> list[dict[str, object]]:
        return await self.market_pulse(self._default_symbol)

    def market_symbols(self) -> list[str]:
        return self._gateway.market_symbols()

    async def klines(
        self,
        *,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> dict[str, object]:
        payload = await self._gateway.fetch_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            price_source=price_source,
        )
        return payload.data.model_dump(by_alias=True)

    async def exchange_accounts(self) -> list[dict[str, object]]:
        accounts = await self._gateway.fetch_exchange_accounts()
        return [item.data.model_dump(by_alias=True) for item in accounts.items]

    def risk_controls(self) -> dict[str, object]:
        return self._risk_controls_repository.get().model_dump(by_alias=True)

    def update_risk_controls(self, payload: RiskControls) -> dict[str, object]:
        updated = payload.model_copy(
            update={"updated_at": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")}
        )
        return self._risk_controls_repository.save(updated).model_dump(by_alias=True)

    @staticmethod
    def alerts(alerts: list) -> list[dict[str, object]]:
        return [item.model_dump(by_alias=True) for item in alerts]

    @staticmethod
    def capabilities() -> list[AgentCapability]:
        return [
            AgentCapability(id="profile.summary.read", label="Read profile summary", description="Read normalized equity, margin, pnl, and sync state.", route="/api/profile/summary", entity="profile_summary"),
            AgentCapability(id="profile.assets.read", label="Read asset balances", description="Read normalized asset balances with collateral value and weight.", route="/api/profile/assets", entity="asset_balance"),
            AgentCapability(id="profile.positions.read", label="Read open positions", description="Read normalized positions with mark price and pnl.", route="/api/profile/positions", entity="position"),
            AgentCapability(id="profile.events.read", label="Read account ledger", description="Read normalized account events for fills, funding, fees, and system actions.", route="/api/profile/account-events", entity="account_event"),
            AgentCapability(id="strategies.read", label="Read strategies", description="Read strategy registry metadata and last backtest context.", route="/api/strategies", entity="strategy"),
            AgentCapability(id="strategies.write", label="Write strategies", description="Create or update strategy definitions and parameters.", read_only=False, route="/api/strategies", entity="strategy"),
            AgentCapability(id="backtests.create", label="Create backtest run", description="Create a backtest run using the same request contract as the admin UI.", route="/api/strategies/{template_or_script}/backtests", entity="backtest_run"),
            AgentCapability(id="backtests.read", label="Read backtest result", description="Read a normalized backtest result by id.", route="/api/backtests/{id}", entity="backtest_result"),
            AgentCapability(id="markets.pulse.read", label="Read market pulse", description="Read operator-facing market pulse metrics with freshness semantics.", route="/api/markets/pulse", entity="market_metric"),
            AgentCapability(id="markets.symbols.read", label="Read market symbols", description="Read the supported market symbols for UI selectors and agents.", route="/api/markets/symbols", entity="market_symbol"),
            AgentCapability(id="markets.klines.read", label="Read klines", description="Read normalized klines by symbol, interval, time range, and price source.", route="/api/markets/{symbol}/klines", entity="kline"),
            AgentCapability(id="risk_controls.read", label="Read risk controls", description="Read the explicit operator risk envelope.", route="/api/risk-controls", entity="risk_controls"),
            AgentCapability(id="risk_controls.write", label="Write risk controls", description="Update the explicit operator risk envelope.", read_only=False, route="/api/risk-controls", entity="risk_controls"),
            AgentCapability(id="settings.exchange_accounts.read", label="Read exchange accounts", description="Read normalized exchange-account metadata and credential rotation state.", route="/api/settings/accounts", entity="exchange_account"),
        ]

    async def agent_context(self) -> dict[str, object]:
        await self._gateway.fetch_exchange_accounts()
        payload = AgentContext(
            mode="admin",
            account_mode="live" if self._settings.backpack_mode == "live" else "mock",
            available_capabilities=[item.id for item in self.capabilities()],
            capabilities=self.capabilities(),
            domain_vocabulary=[
                "price_source",
                "account_event",
                "strategy_spec",
                "execution_intent",
                "backtest_run",
                "market_pulse",
                "exchange_account",
            ],
            resources={
                "profileSummary": "/api/profile/summary",
                "profileAssets": "/api/profile/assets",
                "profilePositions": "/api/profile/positions",
                "profileAccountEvents": "/api/profile/account-events",
                "strategies": "/api/strategies",
                "marketPulse": "/api/markets/pulse",
                "marketSymbols": "/api/markets/symbols",
                "riskControls": "/api/risk-controls",
                "exchangeAccounts": "/api/settings/accounts",
                "alerts": "/api/alerts",
                "backtests": "/api/backtests/{id}",
            },
        )
        return payload.model_dump(by_alias=True)
