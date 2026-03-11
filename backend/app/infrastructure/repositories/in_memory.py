from __future__ import annotations

from dataclasses import dataclass

from ...application.ports.repositories import BacktestRunRepository, ExecutionRuntimeRepository, RiskControlsRepository, StrategyRepository
from ...domain.strategy.entities import Strategy
from ...schemas import BacktestResult, ExecutionEvent, ExecutionOrder, ExecutionRuntimeStatus, LiveStrategyExecution, RiskControls, StrategySummary
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


@dataclass(slots=True)
class InMemoryExecutionRuntimeRepository(ExecutionRuntimeRepository):
    state: RuntimeState

    def list_live_strategies(self) -> list[LiveStrategyExecution]:
        return list(self.state.get("execution_live_strategies", []))

    def get_live_strategy(self, strategy_id: str) -> LiveStrategyExecution | None:
        for item in self.list_live_strategies():
            if item.strategy_id == strategy_id:
                return item
        return None

    def save_live_strategy(self, item: LiveStrategyExecution) -> LiveStrategyExecution:
        strategies = self.list_live_strategies()
        for index, current in enumerate(strategies):
            if current.strategy_id == item.strategy_id:
                strategies[index] = item
                break
        else:
            strategies.append(item)
        self.state.set("execution_live_strategies", strategies)
        return item

    def append_order(self, order: ExecutionOrder) -> ExecutionOrder:
        orders = list(self.state.get("execution_orders", []))
        orders.insert(0, order)
        self.state.set("execution_orders", orders[:100])
        return order

    def list_orders(self) -> list[ExecutionOrder]:
        return list(self.state.get("execution_orders", []))

    def append_event(self, event: ExecutionEvent) -> ExecutionEvent:
        events = list(self.state.get("execution_events", []))
        events.insert(0, event)
        self.state.set("execution_events", events[:200])
        return event

    def list_events(self) -> list[ExecutionEvent]:
        return list(self.state.get("execution_events", []))

    def get_runtime_status(self) -> ExecutionRuntimeStatus:
        current = self.state.get("execution_runtime_status")
        if isinstance(current, ExecutionRuntimeStatus):
            return current
        status = ExecutionRuntimeStatus(
            mode="live",
            running=False,
            max_concurrent_strategies=2,
            active_strategy_count=0,
            enabled_strategy_count=len(self.list_live_strategies()),
        )
        self.state.set("execution_runtime_status", status)
        return status

    def save_runtime_status(self, status: ExecutionRuntimeStatus) -> ExecutionRuntimeStatus:
        self.state.set("execution_runtime_status", status)
        return status

    def get_background_task(self):
        return self.state.get("execution_runtime_task")

    def set_background_task(self, task) -> None:
        self.state.set("execution_runtime_task", task)
