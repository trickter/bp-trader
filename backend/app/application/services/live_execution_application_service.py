from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from ...domain.shared.enums import PriceSource
from ...domain.shared.errors import NotFoundError
from ...domain.strategy.entities import Strategy
from ...schemas import (
    ExecutionBudgetAllocation,
    ExecutionEvent,
    ExecutionOrder,
    ExecutionRuntimeCommand,
    ExecutionRuntimeStatus,
    LiveStrategyEnableRequest,
    LiveStrategyExecution,
    Position,
    RiskControls,
)
from ..errors import ApplicationError
from ..ports.repositories import (
    ExecutionGateway,
    ExecutionRuntimeRepository,
    QuantOperatorGateway,
    RiskControlsRepository,
    StrategyRepository,
)


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _to_epoch_seconds(timestamp: str | None) -> int:
    if not timestamp:
        return 0
    value = timestamp.replace("Z", "+00:00")
    return int(datetime.fromisoformat(value).timestamp())


def _interval_seconds(interval: str) -> int:
    mapping = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400,
    }
    return mapping.get(interval, 3600)


def _float_param(parameters: dict[str, object], key: str, default: float) -> float:
    value = _param(parameters, key, _camel_or_snake(key), default=default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_param(parameters: dict[str, object], key: str, default: int) -> int:
    value = _param(parameters, key, _camel_or_snake(key), default=default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool_param(parameters: dict[str, object], key: str, default: bool = False) -> bool:
    value = _param(parameters, key, _camel_or_snake(key))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _param_value(parameters: dict[str, object], camel_key: str, snake_key: str, default=None):
    if camel_key in parameters:
        return parameters[camel_key]
    if snake_key in parameters:
        return parameters[snake_key]
    return default


def _string_param(parameters: dict[str, object], key: str, default: str = "") -> str:
    value = _param(parameters, key, _camel_or_snake(key))
    if value in (None, ""):
        return default
    return str(value)


def _camel_or_snake(key: str) -> str:
    if "_" in key:
        first, *rest = key.split("_")
        return first + "".join(part.capitalize() for part in rest)
    converted = []
    for char in key:
        if char.isupper():
            converted.extend(["_", char.lower()])
        else:
            converted.append(char)
    return "".join(converted)


def _param(parameters: dict[str, object], *keys: str, default: object | None = None) -> object | None:
    for key in keys:
        if key in parameters:
            return parameters[key]
    return default


@dataclass(slots=True)
class LiveExecutionApplicationService:
    strategy_repository: StrategyRepository
    risk_controls_repository: RiskControlsRepository
    operator_gateway: QuantOperatorGateway
    execution_gateway: ExecutionGateway
    runtime_repository: ExecutionRuntimeRepository
    settings_obj: object
    max_parallel_strategies: int = 2

    def list_live_strategies(self) -> list[LiveStrategyExecution]:
        current = {
            item.strategy_id: item
            for item in self.runtime_repository.list_live_strategies()
        }
        hydrated: list[LiveStrategyExecution] = []
        for strategy in self.strategy_repository.list():
            state = self._build_live_state(strategy, current.get(strategy.id))
            self.runtime_repository.save_live_strategy(state)
            hydrated.append(state)
        return hydrated

    def list_orders(self) -> list[ExecutionOrder]:
        return self.runtime_repository.list_orders()

    def list_events(self) -> list[ExecutionEvent]:
        return self.runtime_repository.list_events()

    def runtime_status(self) -> ExecutionRuntimeStatus:
        status = self.runtime_repository.get_runtime_status()
        live_strategies = self.list_live_strategies()
        budgets = self._compute_budgets(
            live_strategies=[item for item in live_strategies if item.live_enabled and item.confirmed_at],
            max_position_notional=self.risk_controls_repository.get().max_position_notional,
        )
        return self.runtime_repository.save_runtime_status(
            status.model_copy(
                update={
                    "enabled_strategy_count": len([item for item in live_strategies if item.live_enabled and item.confirmed_at]),
                    "active_strategy_count": len(
                        [item for item in live_strategies if item.live_enabled and item.confirmed_at and item.runtime_status == "live_active"]
                    ),
                    "max_concurrent_strategies": self.max_parallel_strategies,
                    "budgets": budgets,
                }
            )
        )

    def enable_strategy(
        self,
        strategy_id: str,
        payload: LiveStrategyEnableRequest,
    ) -> LiveStrategyExecution:
        if not payload.confirmed:
            raise ApplicationError(
                code="execution_confirmation_required",
                message="Live enable requires explicit confirmation.",
                status_code=400,
            )

        strategy = self._require_strategy(strategy_id)
        params = dict(strategy.parameters)
        already_whitelisted = _bool_param(params, "liveEnabled", _bool_param(params, "live_enabled", False))
        if not already_whitelisted:
            raise ApplicationError(
                code="strategy_not_whitelisted",
                message="Strategy is not enabled for live trading.",
                status_code=400,
            )
        params["liveEnabled"] = True
        params["live_enabled"] = True
        params["liveConfirmedAt"] = _utc_now()
        params["live_confirmed_at"] = params["liveConfirmedAt"]
        params.setdefault("executionWeight", _float_param(params, "execution_weight", 1.0))
        params.setdefault(
            "pollIntervalSeconds",
            max(_interval_seconds(_string_param(params, "timeframe", "1h")), 60),
        )
        updated = strategy.update(
            name=strategy.name,
            kind=strategy.kind,
            description=strategy.description,
            market=strategy.market,
            account_id=strategy.account_id,
            runtime="live-ready",
            status=strategy.status,
            price_source=strategy.price_source,
            parameters=params,
        )
        self.strategy_repository.save(updated)
        state = self._build_live_state(updated)
        state = state.model_copy(update={"runtime_status": "live_ready"})
        self.runtime_repository.save_live_strategy(state)
        self.runtime_repository.append_event(
            self._make_event(
                strategy_id=updated.id,
                strategy_name=updated.name,
                level="info",
                event_type="strategy_enabled",
                message="Strategy added to the live whitelist.",
                details={"market": updated.market},
            )
        )
        return state

    def enable_live_strategy(
        self,
        strategy_id: str,
        payload: LiveStrategyEnableRequest,
    ) -> LiveStrategyExecution:
        return self.enable_strategy(strategy_id, payload)

    def disable_strategy(self, strategy_id: str) -> LiveStrategyExecution:
        strategy = self._require_strategy(strategy_id)
        params = dict(strategy.parameters)
        params["liveEnabled"] = False
        params["liveConfirmedAt"] = ""
        params["live_enabled"] = False
        params["live_confirmed_at"] = ""
        updated = strategy.update(
            name=strategy.name,
            kind=strategy.kind,
            description=strategy.description,
            market=strategy.market,
            account_id=strategy.account_id,
            runtime="paper",
            status=strategy.status,
            price_source=strategy.price_source,
            parameters=params,
        )
        self.strategy_repository.save(updated)
        state = self._build_live_state(updated)
        state = state.model_copy(update={"runtime_status": "disabled"})
        self.runtime_repository.save_live_strategy(state)
        self.runtime_repository.append_event(
            self._make_event(
                strategy_id=updated.id,
                strategy_name=updated.name,
                level="warning",
                event_type="strategy_disabled",
                message="Strategy removed from live execution.",
                details={"market": updated.market},
            )
        )
        return state

    def disable_live_strategy(self, strategy_id: str) -> LiveStrategyExecution:
        return self.disable_strategy(strategy_id)

    async def execute_cycle(self) -> ExecutionRuntimeStatus:
        await self._run_cycle()
        return self.runtime_status()

    async def flatten_live_strategy(
        self,
        strategy_id: str,
        payload: ExecutionRuntimeCommand,
    ) -> LiveStrategyExecution:
        if not payload.confirmed:
            raise ApplicationError(
                code="execution_confirmation_required",
                message="Manual flatten requires explicit confirmation.",
                status_code=400,
            )
        strategy = self._require_strategy(strategy_id)
        state = self._build_live_state(strategy, self.runtime_repository.get_live_strategy(strategy_id))
        snapshot = await self.operator_gateway.fetch_profile_snapshot(PriceSource.MARK)
        current_position = self._find_position([item.data for item in snapshot.positions.items], strategy.market)
        if current_position is None:
            self.runtime_repository.append_event(
                self._make_event(
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    level="warning",
                    event_type="manual_flatten_skipped",
                    message="No open position was found for this strategy market.",
                    details={"market": strategy.market},
                )
            )
            return self.runtime_repository.save_live_strategy(
                state.model_copy(update={"last_error": "No open position found for manual flatten."})
            )

        client_order_id = f"{strategy.id}-manual-close-{uuid4().hex[:8]}"
        order = await self.execution_gateway.submit_market_order(
            symbol=strategy.market,
            side=current_position.side,
            quantity=abs(current_position.quantity),
            reduce_only=True,
            client_order_id=client_order_id,
        )
        order = order.model_copy(
            update={
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "action": "manual_close",
            }
        )
        self.runtime_repository.append_order(order)
        self.runtime_repository.append_event(
            self._make_event(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                level="info",
                event_type="manual_flatten_submitted",
                message=f"Manual reduce-only close submitted for {strategy.market}.",
                details={
                    "quantity": abs(current_position.quantity),
                    "clientOrderId": client_order_id,
                },
            )
        )
        return self.runtime_repository.save_live_strategy(
            state.model_copy(
                update={
                    "last_order_id": order.exchange_order_id or order.id,
                    "last_signal": "manual_close",
                    "last_error": "",
                    "last_cycle_at": _utc_now(),
                }
            )
        )

    async def disable_and_flatten_live_strategy(
        self,
        strategy_id: str,
        payload: ExecutionRuntimeCommand,
    ) -> LiveStrategyExecution:
        flattened = await self.flatten_live_strategy(strategy_id, payload)
        disabled = self.disable_strategy(strategy_id)
        return disabled.model_copy(
            update={
                "last_order_id": flattened.last_order_id,
                "last_signal": "manual_close",
            }
        )

    async def start_runtime(self, payload: ExecutionRuntimeCommand) -> ExecutionRuntimeStatus:
        status = self.runtime_repository.get_runtime_status()
        if status.running:
            return self.runtime_status()

        live_strategies = [item for item in self.list_live_strategies() if item.live_enabled and item.confirmed_at]
        if not live_strategies:
            raise ApplicationError(
                code="execution_no_live_strategies",
                message="No confirmed live strategies are enabled.",
                status_code=400,
            )

        if not payload.confirmed:
            raise ApplicationError(
                code="execution_confirmation_required",
                message="Starting live runtime requires explicit confirmation.",
                status_code=400,
            )

        next_status = status.model_copy(
            update={
                "running": True,
                "mode": "live",
                "started_at": _utc_now(),
                "stopped_at": None,
                "last_error": "",
            }
        )
        self.runtime_repository.save_runtime_status(next_status)
        task = asyncio.create_task(self._execution_loop(), name="live-execution-loop")
        self.runtime_repository.set_background_task(task)
        return self.runtime_status()

    async def stop_runtime(self, payload: ExecutionRuntimeCommand) -> ExecutionRuntimeStatus:
        task = self.runtime_repository.get_background_task()
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.runtime_repository.set_background_task(None)
        status = self.runtime_repository.get_runtime_status()
        self.runtime_repository.save_runtime_status(
            status.model_copy(
                update={
                    "running": False,
                    "stopped_at": _utc_now(),
                    "last_error": payload.reason,
                }
            )
        )
        for state in self.runtime_repository.list_live_strategies():
            if state.live_enabled:
                self.runtime_repository.save_live_strategy(
                    state.model_copy(update={"runtime_status": "live_ready"})
                )
        return self.runtime_status()

    async def _execution_loop(self) -> None:
        try:
            while True:
                await self._run_cycle()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - runtime guard
            status = self.runtime_repository.get_runtime_status()
            self.runtime_repository.save_runtime_status(
                status.model_copy(update={"running": False, "last_error": str(exc), "stopped_at": _utc_now()})
            )
            self.runtime_repository.append_event(
                self._make_event(
                    strategy_id="runtime",
                    strategy_name="runtime",
                    level="critical",
                    event_type="runtime_error",
                    message=str(exc),
                    details={},
                )
            )
            self.runtime_repository.set_background_task(None)

    async def _run_cycle(self) -> None:
        controls = self.risk_controls_repository.get()
        status = self.runtime_repository.get_runtime_status()
        live_states = [item for item in self.list_live_strategies() if item.live_enabled and item.confirmed_at]
        eligible = self._select_active_states(live_states)
        snapshot = await self.operator_gateway.fetch_profile_snapshot(PriceSource.MARK)
        budgets = self._compute_budgets(eligible, controls.max_position_notional)
        budget_map = {item.strategy_id: item.budget_notional for item in budgets}

        for state in self.runtime_repository.list_live_strategies():
            next_runtime = "live_active" if state.strategy_id in budget_map else ("live_ready" if state.live_enabled else "disabled")
            self.runtime_repository.save_live_strategy(state.model_copy(update={"runtime_status": next_runtime}))

        for state in eligible:
            if not self._due_for_cycle(state):
                continue
            strategy = self._require_strategy(state.strategy_id)
            await self._run_strategy_cycle(
                strategy=strategy,
                state=state,
                controls=controls,
                budget_notional=budget_map.get(state.strategy_id, 0.0),
                snapshot_positions=[item.data for item in snapshot.positions.items],
                total_equity=snapshot.summary.data.total_equity,
                realized_pnl_24h=snapshot.summary.data.realized_pnl_24h,
            )

        self.runtime_repository.save_runtime_status(
            status.model_copy(
                update={
                    "running": True,
                    "last_cycle_at": _utc_now(),
                    "enabled_strategy_count": len([item for item in live_states if item.live_enabled]),
                    "active_strategy_count": len(eligible),
                    "budgets": budgets,
                }
            )
        )

    async def _run_strategy_cycle(
        self,
        *,
        strategy: Strategy,
        state: LiveStrategyExecution,
        controls: RiskControls,
        budget_notional: float,
        snapshot_positions: list[Position],
        total_equity: float,
        realized_pnl_24h: float,
    ) -> None:
        readiness = self._readiness_checks(strategy)
        if readiness:
            next_state = state.model_copy(update={"last_error": "; ".join(readiness), "last_cycle_at": _utc_now(), "readiness_checks": readiness})
            self.runtime_repository.save_live_strategy(next_state)
            return

        risk_error = self._pre_trade_risk_error(
            controls=controls,
            strategy=strategy,
            snapshot_positions=snapshot_positions,
            total_equity=total_equity,
            realized_pnl_24h=realized_pnl_24h,
        )
        if risk_error:
            self.runtime_repository.append_event(
                self._make_event(
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    level="warning",
                    event_type="risk_block",
                    message=risk_error,
                    details={"market": strategy.market},
                )
            )
            self.runtime_repository.save_live_strategy(state.model_copy(update={"last_error": risk_error, "last_cycle_at": _utc_now()}))
            return

        signal = await self._generate_signal(strategy, snapshot_positions)
        if signal is None:
            self.runtime_repository.save_live_strategy(state.model_copy(update={"last_cycle_at": _utc_now(), "last_error": ""}))
            return

        current_position = self._find_position(snapshot_positions, strategy.market)
        action = signal["action"]
        side = signal["side"]
        latest_price = float(signal["price"])
        quantity = self._resolve_quantity(
            action=action,
            budget_notional=budget_notional,
            latest_price=latest_price,
            current_position=current_position,
        )
        if quantity <= 0:
            self.runtime_repository.save_live_strategy(state.model_copy(update={"last_cycle_at": _utc_now(), "last_error": "Order quantity resolved to zero."}))
            return

        client_order_id = f"{strategy.id}-{uuid4().hex[:12]}"
        try:
            order = await self.execution_gateway.submit_market_order(
                symbol=strategy.market,
                side=side,
                quantity=quantity,
                reduce_only=action.startswith("close"),
                client_order_id=client_order_id,
            )
        except ApplicationError as exc:
            self.runtime_repository.append_event(
                self._make_event(
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    level="critical",
                    event_type="order_rejected",
                    message=exc.message,
                    details={"code": exc.code, "market": strategy.market, **{k: v for k, v in exc.metadata.items() if isinstance(v, (str, float, int, bool))}},
                )
            )
            self.runtime_repository.save_live_strategy(state.model_copy(update={"last_error": exc.message, "last_cycle_at": _utc_now()}))
            return

        order = order.model_copy(
            update={
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "action": action,
            }
        )
        self.runtime_repository.append_order(order)
        self.runtime_repository.append_event(
            self._make_event(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                level="info",
                event_type="order_submitted",
                message=f"{action} submitted for {strategy.market}.",
                details={
                    "quantity": quantity,
                    "price": latest_price,
                    "clientOrderId": client_order_id,
                },
            )
        )
        self.runtime_repository.save_live_strategy(
            state.model_copy(
                update={
                    "last_cycle_at": _utc_now(),
                    "last_signal": action,
                    "last_order_id": order.exchange_order_id or order.id,
                    "last_error": "",
                }
            )
        )

    async def _generate_signal(
        self,
        strategy: Strategy,
        snapshot_positions: list[Position],
    ) -> dict[str, object] | None:
        if strategy.kind != "template":
            return None

        interval = _string_param(strategy.parameters, "timeframe", "1h")
        end_time = int(datetime.now(tz=UTC).timestamp())
        start_time = end_time - (_interval_seconds(interval) * 320)
        klines = await self.operator_gateway.fetch_klines(
            symbol=strategy.market,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            price_source=strategy.price_source,
        )
        candles = klines.data.candles
        if len(candles) < 50:
            return None

        closes = [item.close for item in candles]
        highs = [item.high for item in candles]
        lows = [item.low for item in candles]
        volumes = [item.volume for item in candles]
        current_position = self._find_position(snapshot_positions, strategy.market)
        direction = _string_param(strategy.parameters, "direction", "long_only")
        preset = str(_param_value(strategy.parameters, "templatePresetId", "template_preset_id", "ema_dual_trend"))
        bullish_entry, bullish_exit, bearish_entry, bearish_exit = _evaluate_preset(
            preset=preset,
            closes=closes,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
        latest_price = closes[-1]

        if current_position is None:
            if direction in ("long_only", "bi_directional") and bullish_entry:
                return {"action": "open_long", "side": "long", "price": latest_price}
            if direction in ("short_only", "bi_directional") and bearish_entry:
                return {"action": "open_short", "side": "short", "price": latest_price}
            return None

        if current_position.side == "long" and bullish_exit:
            return {"action": "close_long", "side": "long", "price": latest_price}
        if current_position.side == "short" and bearish_exit:
            return {"action": "close_short", "side": "short", "price": latest_price}
        return None

    def _pre_trade_risk_error(
        self,
        *,
        controls: RiskControls,
        strategy: Strategy,
        snapshot_positions: list[Position],
        total_equity: float,
        realized_pnl_24h: float,
    ) -> str | None:
        if controls.kill_switch_enabled:
            return "Kill switch is enabled."
        if strategy.market not in controls.allowed_symbols:
            return "Market is not in allowed symbols."
        if realized_pnl_24h <= -abs(controls.daily_loss_limit):
            return "Daily loss limit has been breached."
        if len(snapshot_positions) >= controls.max_open_positions:
            return "Max open positions reached."
        if controls.max_position_notional > (total_equity * controls.max_leverage):
            return "Risk envelope exceeds account leverage budget."
        duplicate_markets = [
            item.market
            for item in self.list_live_strategies()
            if item.live_enabled and item.strategy_id != strategy.id
        ]
        if strategy.market in duplicate_markets:
            return "Another live strategy already owns this market."
        return None

    def _build_live_state(
        self,
        strategy: Strategy,
        current: LiveStrategyExecution | None = None,
    ) -> LiveStrategyExecution:
        parameters = dict(strategy.parameters)
        confirmed_at = _param_value(parameters, "liveConfirmedAt", "live_confirmed_at", None)
        if not confirmed_at and current is not None:
            confirmed_at = current.confirmed_at
        readiness = self._readiness_checks(strategy)
        if confirmed_at and "Live trading has not been explicitly confirmed." in readiness:
            readiness = [item for item in readiness if item != "Live trading has not been explicitly confirmed."]
        execution_weight = None
        if "executionWeight" in parameters or "execution_weight" in parameters:
            execution_weight = max(
                _float_param(
                    parameters,
                    "executionWeight",
                    _float_param(parameters, "execution_weight", 1.0),
                ),
                0.1,
            )
        elif current is not None:
            execution_weight = current.execution_weight
        else:
            execution_weight = 1.0

        poll_interval_seconds = None
        if "pollIntervalSeconds" in parameters or "poll_interval_seconds" in parameters:
            poll_interval_seconds = max(
                _int_param(
                    parameters,
                    "pollIntervalSeconds",
                    _int_param(parameters, "poll_interval_seconds", _interval_seconds(_string_param(parameters, "timeframe", "1h"))),
                ),
                60,
            )
        elif current is not None:
            poll_interval_seconds = current.poll_interval_seconds
        else:
            poll_interval_seconds = max(_interval_seconds(_string_param(parameters, "timeframe", "1h")), 60)

        return LiveStrategyExecution(
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            strategy_kind=strategy.kind,
            market=strategy.market,
            account_id=strategy.account_id,
            price_source=strategy.price_source,
            runtime_status=current.runtime_status if current else strategy.runtime,
            live_enabled=_bool_param(parameters, "liveEnabled", _bool_param(parameters, "live_enabled", False)),
            is_whitelisted=_bool_param(parameters, "liveEnabled", _bool_param(parameters, "live_enabled", False)),
            execution_weight=execution_weight,
            poll_interval_seconds=poll_interval_seconds,
            confirmed_at=str(confirmed_at) if confirmed_at not in (None, "") else None,
            last_cycle_at=current.last_cycle_at if current else None,
            last_signal=current.last_signal if current else None,
            last_error=current.last_error if current else None,
            last_order_id=current.last_order_id if current else None,
            readiness_checks=readiness,
        )

    def _readiness_checks(self, strategy: Strategy) -> list[str]:
        issues: list[str] = []
        if not strategy.account_id:
            issues.append("Execution account is missing.")
        if strategy.kind != "template":
            issues.append("Script strategies are not live-enabled in this v1 runtime.")
        if not _bool_param(strategy.parameters, "liveEnabled", _bool_param(strategy.parameters, "live_enabled", False)):
            issues.append("Strategy is not in the live whitelist.")
        confirmed_at = _param_value(strategy.parameters, "liveConfirmedAt", "live_confirmed_at", "")
        if not confirmed_at:
            issues.append("Live trading has not been explicitly confirmed.")
        return issues

    def _select_active_states(self, live_states: list[LiveStrategyExecution]) -> list[LiveStrategyExecution]:
        ordered = sorted(live_states, key=lambda item: (-item.execution_weight, item.strategy_id))
        return ordered[: self.max_parallel_strategies]

    def _compute_budgets(
        self,
        live_strategies: list[LiveStrategyExecution],
        max_position_notional: float,
    ) -> list[ExecutionBudgetAllocation]:
        if not live_strategies:
            return []
        total_weight = sum(max(item.execution_weight, 0.1) for item in live_strategies)
        return [
            ExecutionBudgetAllocation(
                strategy_id=item.strategy_id,
                strategy_name=item.strategy_name,
                weight=item.execution_weight,
                budget_notional=round(max_position_notional * (item.execution_weight / total_weight), 4),
            )
            for item in live_strategies
        ]

    def _resolve_quantity(
        self,
        *,
        action: str,
        budget_notional: float,
        latest_price: float,
        current_position: Position | None,
    ) -> float:
        if action.startswith("close") and current_position is not None:
            return round(abs(current_position.quantity), 6)
        if latest_price <= 0:
            return 0.0
        return round(budget_notional / latest_price, 6)

    def _due_for_cycle(self, state: LiveStrategyExecution) -> bool:
        if not state.last_cycle_at:
            return True
        elapsed = int(datetime.now(tz=UTC).timestamp()) - _to_epoch_seconds(state.last_cycle_at)
        return elapsed >= state.poll_interval_seconds

    @staticmethod
    def _find_position(positions: list[Position], symbol: str) -> Position | None:
        for item in positions:
            if item.symbol == symbol and item.quantity > 0:
                return item
        return None

    @staticmethod
    def _make_event(
        *,
        strategy_id: str,
        strategy_name: str,
        level: str,
        event_type: str,
        message: str,
        details: dict[str, str | float | int | bool],
    ) -> ExecutionEvent:
        return ExecutionEvent(
            id=f"evt_{uuid4().hex[:10]}",
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            level=level,
            event_type=event_type,
            message=message,
            created_at=_utc_now(),
            metadata=details,
        )

    def _require_strategy(self, strategy_id: str) -> Strategy:
        strategy = self.strategy_repository.get(strategy_id)
        if strategy is None:
            raise NotFoundError(code="strategy_not_found", message="Strategy does not exist.")
        return strategy


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append((value * alpha) + (result[-1] * (1 - alpha)))
    return result


def _sma(values: list[float], period: int) -> list[float]:
    result: list[float] = []
    for index in range(len(values)):
        start = max(0, index + 1 - period)
        window = values[start : index + 1]
        result.append(sum(window) / len(window))
    return result


def _rsi(values: list[float], period: int = 14) -> list[float]:
    if len(values) < 2:
        return [50.0 for _ in values]
    gains = [0.0]
    losses = [0.0]
    for prev, current in zip(values, values[1:]):
        delta = current - prev
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = _sma(gains, period)
    avg_loss = _sma(losses, period)
    result: list[float] = []
    for gain, loss in zip(avg_gain, avg_loss):
        if loss == 0:
            result.append(100.0)
            continue
        rs = gain / loss
        result.append(100 - (100 / (1 + rs)))
    return result


def _macd(values: list[float]) -> tuple[list[float], list[float]]:
    fast = _ema(values, 12)
    slow = _ema(values, 26)
    macd_line = [f - s for f, s in zip(fast, slow)]
    signal = _ema(macd_line, 9)
    return macd_line, signal


def _stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _bollinger(values: list[float], period: int = 20, deviation: float = 2.0) -> tuple[list[float], list[float], list[float]]:
    basis = _sma(values, period)
    upper: list[float] = []
    lower: list[float] = []
    for index, center in enumerate(basis):
        start = max(0, index + 1 - period)
        window = values[start : index + 1]
        std = _stddev(window)
        upper.append(center + (std * deviation))
        lower.append(center - (std * deviation))
    return basis, upper, lower


def _atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float]:
    if not closes:
        return []
    true_ranges = [highs[0] - lows[0]]
    for index in range(1, len(closes)):
        true_ranges.append(
            max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
        )
    return _sma(true_ranges, period)


def _supertrend(highs: list[float], lows: list[float], closes: list[float], period: int = 10, multiplier: float = 3.0) -> list[int]:
    atr = _atr(highs, lows, closes, period)
    trend: list[int] = []
    final_upper = 0.0
    final_lower = 0.0
    current_trend = 1
    for index in range(len(closes)):
        hl2 = (highs[index] + lows[index]) / 2
        basic_upper = hl2 + multiplier * atr[index]
        basic_lower = hl2 - multiplier * atr[index]
        if index == 0:
            final_upper = basic_upper
            final_lower = basic_lower
        else:
            final_upper = basic_upper if basic_upper < final_upper or closes[index - 1] > final_upper else final_upper
            final_lower = basic_lower if basic_lower > final_lower or closes[index - 1] < final_lower else final_lower
            if current_trend == -1 and closes[index] > final_upper:
                current_trend = 1
            elif current_trend == 1 and closes[index] < final_lower:
                current_trend = -1
        trend.append(current_trend)
    return trend


def _crosses_above(left: list[float], right: list[float]) -> bool:
    return len(left) >= 2 and len(right) >= 2 and left[-2] <= right[-2] and left[-1] > right[-1]


def _crosses_below(left: list[float], right: list[float]) -> bool:
    return len(left) >= 2 and len(right) >= 2 and left[-2] >= right[-2] and left[-1] < right[-1]


def _evaluate_preset(
    *,
    preset: str,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    volumes: list[float],
) -> tuple[bool, bool, bool, bool]:
    ema9 = _ema(closes, 9)
    ema21 = _ema(closes, 21)
    ema55 = _ema(closes, 55)
    ema200 = _ema(closes, 200)
    rsi14 = _rsi(closes, 14)
    macd_line, macd_signal = _macd(closes)
    volume_ma20 = _sma(volumes, 20)
    basis, upper, lower = _bollinger(closes, 20, 2.0)
    breakout_high = max(highs[-21:-1]) if len(highs) > 20 else max(highs)
    breakout_low = min(lows[-21:-1]) if len(lows) > 20 else min(lows)
    vwap_value = sum(price * volume for price, volume in zip(closes[-20:], volumes[-20:])) / max(sum(volumes[-20:]), 1)
    supertrend_state = _supertrend(highs, lows, closes)

    if preset == "ema_dual_trend":
        return (
            _crosses_above(ema9, ema21) or ema9[-1] > ema21[-1],
            _crosses_below(ema9, ema21) or ema9[-1] < ema21[-1],
            _crosses_below(ema9, ema21) or ema9[-1] < ema21[-1],
            _crosses_above(ema9, ema21) or ema9[-1] > ema21[-1],
        )
    if preset == "rsi_reversal":
        return (
            rsi14[-1] < 30 and closes[-1] > ema200[-1],
            rsi14[-1] > 70,
            rsi14[-1] > 70 and closes[-1] < ema200[-1],
            rsi14[-1] < 30,
        )
    if preset == "macd_trend_follow":
        volume_ok = volumes[-1] > volume_ma20[-1]
        return (
            _crosses_above(macd_line, macd_signal) and volume_ok,
            _crosses_below(macd_line, macd_signal),
            _crosses_below(macd_line, macd_signal) and volume_ok,
            _crosses_above(macd_line, macd_signal),
        )
    if preset == "bollinger_mean_reversion":
        return (
            closes[-1] < lower[-1] and rsi14[-1] < 35,
            closes[-1] > basis[-1],
            closes[-1] > upper[-1] and rsi14[-1] > 65,
            closes[-1] < basis[-1],
        )
    if preset == "breakout_trend":
        return (
            closes[-1] > breakout_high and volumes[-1] > volume_ma20[-1] * 1.5,
            closes[-1] < ema21[-1],
            closes[-1] < breakout_low and volumes[-1] > volume_ma20[-1] * 1.5,
            closes[-1] > ema21[-1],
        )
    if preset == "vwap_reversion":
        return (
            closes[-1] < vwap_value and rsi14[-1] < 40,
            closes[-1] > vwap_value,
            closes[-1] > vwap_value and rsi14[-1] > 60,
            closes[-1] < vwap_value,
        )
    if preset == "supertrend_follow":
        return (
            supertrend_state[-1] == 1 and closes[-1] > ema21[-1],
            supertrend_state[-1] == -1,
            supertrend_state[-1] == -1 and closes[-1] < ema21[-1],
            supertrend_state[-1] == 1,
        )
    if preset == "multi_factor_confirmation":
        bullish = ema21[-1] > ema55[-1] and rsi14[-1] > 55 and volumes[-1] > volume_ma20[-1]
        bearish = ema21[-1] < ema55[-1] and rsi14[-1] < 45 and volumes[-1] > volume_ma20[-1]
        return bullish, not bullish, bearish, not bearish
    return (
        _crosses_above(ema9, ema21) or ema9[-1] > ema21[-1],
        _crosses_below(ema9, ema21) or ema9[-1] < ema21[-1],
        _crosses_below(ema9, ema21) or ema9[-1] < ema21[-1],
        _crosses_above(ema9, ema21) or ema9[-1] > ema21[-1],
    )
