from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from psycopg import connect
from psycopg.rows import dict_row

from ...application.ports.repositories import ExecutionRuntimeRepository
from ...schemas import ExecutionEvent, ExecutionOrder, ExecutionRuntimeStatus, LiveStrategyExecution
from ..state import RuntimeState


DDL = """
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
"""


def _json_payload(model) -> str:
    return json.dumps(model.model_dump(mode="json"))


@dataclass(slots=True)
class PostgresExecutionRuntimeRepository(ExecutionRuntimeRepository):
    database_url: str
    state: RuntimeState

    def __post_init__(self) -> None:
        self._ensure_tables()

    def list_live_strategies(self) -> list[LiveStrategyExecution]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT payload FROM app_live_strategy_states ORDER BY updated_at DESC, strategy_id ASC"
            )
            rows = cur.fetchall()
        return [LiveStrategyExecution.model_validate(row["payload"]) for row in rows]

    def get_live_strategy(self, strategy_id: str) -> LiveStrategyExecution | None:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT payload FROM app_live_strategy_states WHERE strategy_id = %s",
                (strategy_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return LiveStrategyExecution.model_validate(row["payload"])

    def save_live_strategy(self, item: LiveStrategyExecution) -> LiveStrategyExecution:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_live_strategy_states(strategy_id, payload, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (strategy_id)
                DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                """,
                (item.strategy_id, _json_payload(item)),
            )
            conn.commit()
        return item

    def append_order(self, order: ExecutionOrder) -> ExecutionOrder:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_execution_orders_log(id, payload, created_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (id)
                DO UPDATE SET payload = EXCLUDED.payload
                """,
                (order.id, _json_payload(order)),
            )
            conn.commit()
        return order

    def list_orders(self) -> list[ExecutionOrder]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT payload FROM app_execution_orders_log ORDER BY created_at DESC LIMIT 100"
            )
            rows = cur.fetchall()
        return [ExecutionOrder.model_validate(row["payload"]) for row in rows]

    def append_event(self, event: ExecutionEvent) -> ExecutionEvent:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_execution_events_log(id, payload, created_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (id)
                DO UPDATE SET payload = EXCLUDED.payload
                """,
                (event.id, _json_payload(event)),
            )
            conn.commit()
        return event

    def list_events(self) -> list[ExecutionEvent]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT payload FROM app_execution_events_log ORDER BY created_at DESC LIMIT 200"
            )
            rows = cur.fetchall()
        return [ExecutionEvent.model_validate(row["payload"]) for row in rows]

    def get_runtime_status(self) -> ExecutionRuntimeStatus:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT payload FROM app_execution_runtime_state WHERE singleton_id = 1"
            )
            row = cur.fetchone()
        if row is None:
            status = ExecutionRuntimeStatus(
                mode="live",
                running=False,
                max_concurrent_strategies=2,
                active_strategy_count=0,
                enabled_strategy_count=len(self.list_live_strategies()),
            )
            self.save_runtime_status(status)
            return status
        return ExecutionRuntimeStatus.model_validate(row["payload"])

    def save_runtime_status(self, status: ExecutionRuntimeStatus) -> ExecutionRuntimeStatus:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_execution_runtime_state(singleton_id, payload, updated_at)
                VALUES (1, %s::jsonb, NOW())
                ON CONFLICT (singleton_id)
                DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                """,
                (_json_payload(status),),
            )
            conn.commit()
        return status

    def get_background_task(self) -> Any | None:
        return self.state.get("execution_runtime_task")

    def set_background_task(self, task: Any | None) -> None:
        self.state.set("execution_runtime_task", task)

    def _ensure_tables(self) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(DDL)
            conn.commit()

    def _conn(self):
        return connect(self.database_url, autocommit=False)
