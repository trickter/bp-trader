from __future__ import annotations

from dataclasses import dataclass

from ...application.ports.repositories import BacktestRunRepository, RiskControlsRepository, StrategyRepository
from ...domain.strategy.entities import Strategy
from ...schemas import BacktestResult, RiskControls, StrategySummary
from ..state import RuntimeState


def _strategy_from_summary(item: StrategySummary) -> Strategy:
    return Strategy(
        id=item.id,
        name=item.name,
        kind=item.kind,
        description=item.description,
        market=item.market,
        account_id=item.account_id,
        runtime=item.runtime,
        status=item.status,
        last_backtest=item.last_backtest,
        sharpe=item.sharpe,
        price_source=item.price_source,
        parameters=dict(item.parameters),
    )


@dataclass(slots=True)
class InMemoryStrategyRepository(StrategyRepository):
    storage: list[StrategySummary]

    def list(self) -> list[Strategy]:
        return [_strategy_from_summary(item) for item in self.storage]

    def get(self, strategy_id: str) -> Strategy | None:
        for item in self.storage:
            if item.id == strategy_id:
                return _strategy_from_summary(item)
        return None

    def save(self, strategy: Strategy) -> Strategy:
        summary = StrategySummary(
            id=strategy.id,
            name=strategy.name,
            kind=strategy.kind,
            description=strategy.description,
            market=strategy.market,
            account_id=strategy.account_id,
            runtime=strategy.runtime,
            status=strategy.status,
            last_backtest=strategy.last_backtest,
            sharpe=strategy.sharpe,
            price_source=strategy.price_source,
            parameters=strategy.parameters,
        )
        for index, item in enumerate(self.storage):
            if item.id == strategy.id:
                self.storage[index] = summary
                break
        else:
            self.storage.append(summary)
        return strategy


@dataclass(slots=True)
class InMemoryBacktestRunRepository(BacktestRunRepository):
    storage: dict[str, BacktestResult]

    def get(self, backtest_id: str) -> BacktestResult | None:
        return self.storage.get(backtest_id)

    def save_result(self, result: BacktestResult) -> BacktestResult:
        self.storage[result.id] = result
        return result


@dataclass(slots=True)
class InMemoryRiskControlsRepository(RiskControlsRepository):
    state: RuntimeState
    default_controls: RiskControls

    def get(self) -> RiskControls:
        current = self.state.get("risk_controls", self.default_controls)
        if isinstance(current, RiskControls):
            payload = current.model_dump()
        elif isinstance(current, dict):
            payload = current
        else:
            payload = {}
        normalized = self.default_controls.model_copy(update=payload)
        self.state.set("risk_controls", normalized)
        return normalized

    def save(self, controls: RiskControls) -> RiskControls:
        updated = self.default_controls.model_copy(update=controls.model_dump())
        self.state.set("risk_controls", updated)
        return updated
