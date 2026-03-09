from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..shared.enums import PriceSource


@dataclass(slots=True)
class Strategy:
    id: str
    name: str
    kind: str
    market: str
    runtime: str
    status: str
    price_source: PriceSource
    description: str = ""
    account_id: str = ""
    last_backtest: str = ""
    sharpe: float = 0.0
    parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        strategy_id: str,
        name: str,
        kind: str,
        description: str,
        market: str,
        account_id: str,
        runtime: str,
        status: str,
        price_source: PriceSource,
        parameters: dict[str, Any],
    ) -> "Strategy":
        return cls(
            id=strategy_id,
            name=name,
            kind=kind,
            description=description,
            market=market,
            account_id=account_id,
            runtime=runtime,
            status=status,
            last_backtest="",
            sharpe=0.0,
            price_source=price_source,
            parameters=dict(parameters),
        )

    def update(
        self,
        *,
        name: str,
        kind: str,
        description: str,
        market: str,
        account_id: str,
        runtime: str,
        status: str,
        price_source: PriceSource,
        parameters: dict[str, Any],
    ) -> "Strategy":
        return Strategy(
            id=self.id,
            name=name,
            kind=kind,
            description=description,
            market=market,
            account_id=account_id,
            runtime=runtime,
            status=status,
            last_backtest=self.last_backtest,
            sharpe=self.sharpe,
            price_source=price_source,
            parameters=dict(parameters),
        )
