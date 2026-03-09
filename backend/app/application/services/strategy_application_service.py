from __future__ import annotations

from uuid import uuid4

from ...domain.shared.errors import NotFoundError
from ...domain.strategy.entities import Strategy
from ...schemas import StrategySummary, StrategyUpsertRequest
from ..ports.repositories import StrategyRepository


class StrategyApplicationService:
    def __init__(self, strategy_repository: StrategyRepository) -> None:
        self._strategy_repository = strategy_repository

    def list_strategies(self) -> list[StrategySummary]:
        return [self._to_summary(item) for item in self._strategy_repository.list()]

    def get_strategy(self, strategy_id: str) -> StrategySummary:
        return self._to_summary(self._require_strategy(strategy_id))

    def create_strategy(self, payload: StrategyUpsertRequest) -> StrategySummary:
        strategy = Strategy.create(
            strategy_id=f"strat_{uuid4().hex[:8]}",
            name=payload.name,
            kind=payload.kind,
            description=payload.description,
            market=payload.market,
            account_id=payload.account_id,
            runtime=payload.runtime,
            status=payload.status,
            price_source=payload.price_source,
            parameters=payload.parameters,
        )
        return self._to_summary(self._strategy_repository.save(strategy))

    def update_strategy(self, strategy_id: str, payload: StrategyUpsertRequest) -> StrategySummary:
        strategy = self._require_strategy(strategy_id)
        updated = strategy.update(
            name=payload.name,
            kind=payload.kind,
            description=payload.description,
            market=payload.market,
            account_id=payload.account_id,
            runtime=payload.runtime,
            status=payload.status,
            price_source=payload.price_source,
            parameters=payload.parameters,
        )
        return self._to_summary(self._strategy_repository.save(updated))

    def ensure_exists(self, strategy_id: str) -> Strategy:
        return self._require_strategy(strategy_id)

    def _require_strategy(self, strategy_id: str) -> Strategy:
        strategy = self._strategy_repository.get(strategy_id)
        if strategy is None:
            raise NotFoundError(code="strategy_not_found", message="Strategy does not exist.")
        return strategy

    @staticmethod
    def _to_summary(strategy: Strategy) -> StrategySummary:
        return StrategySummary(
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
