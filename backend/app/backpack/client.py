from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import httpx

from .exceptions import BackpackAuthError, BackpackRequestError
from .serialize import canonical_query_string
from .signing import sign_instruction
from .types import BackpackAuthConfig, BackpackRequestConfig


SIGNED_ENDPOINTS: dict[str, BackpackRequestConfig] = {
    "account": BackpackRequestConfig(instruction="accountQuery", path="/api/v1/account"),
    "capital": BackpackRequestConfig(instruction="capitalQuery", path="/api/v1/capital"),
    "collateral": BackpackRequestConfig(instruction="collateralQuery", path="/api/v1/collateral"),
    "positions": BackpackRequestConfig(instruction="positionQuery", path="/api/v1/position"),
    "fills_history": BackpackRequestConfig(instruction="fillHistoryQuery", path="/wapi/v1/history/fills"),
    "funding_history": BackpackRequestConfig(instruction="fundingHistoryQuery", path="/wapi/v1/history/funding"),
}

PUBLIC_ENDPOINTS: dict[str, str] = {
    "markets": "/api/v1/markets",
    "market": "/api/v1/market",
    "klines": "/api/v1/klines",
    "open_interest": "/api/v1/openInterest",
    "funding_rates": "/api/v1/fundingRates",
}


class BackpackClient:
    def __init__(
        self,
        config: BackpackAuthConfig,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._external_client = http_client
        self._client = http_client or httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_seconds,
            headers={"User-Agent": config.user_agent, "Accept": "application/json"},
        )

    async def __aenter__(self) -> "BackpackClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._external_client is None:
            await self._client.aclose()

    async def get_public(
        self,
        path: str,
        *,
        params: Mapping[str, object | None] | None = None,
    ) -> Any:
        return await self._request("GET", path, params=dict(params or {}), headers=None)

    async def get_signed(
        self,
        *,
        instruction: str,
        path: str,
        params: Mapping[str, object | None] | None = None,
    ) -> Any:
        signed_params = dict(params or {})
        headers = self._build_signed_headers(instruction=instruction, params=signed_params)
        return await self._request("GET", path, params=signed_params, headers=headers)

    async def get_account(self) -> Any:
        endpoint = SIGNED_ENDPOINTS["account"]
        return await self.get_signed(instruction=endpoint.instruction, path=endpoint.path)

    async def get_capital_balances(self) -> Any:
        endpoint = SIGNED_ENDPOINTS["capital"]
        return await self.get_signed(instruction=endpoint.instruction, path=endpoint.path)

    async def get_capital(self) -> Any:
        return await self.get_capital_balances()

    async def get_collateral(self) -> Any:
        endpoint = SIGNED_ENDPOINTS["collateral"]
        return await self.get_signed(instruction=endpoint.instruction, path=endpoint.path)

    async def get_positions(self, *, symbol: str | None = None) -> Any:
        endpoint = SIGNED_ENDPOINTS["positions"]
        return await self.get_signed(
            instruction=endpoint.instruction,
            path=endpoint.path,
            params={"symbol": symbol},
        )

    async def get_fills_history(
        self,
        *,
        symbol: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        endpoint = SIGNED_ENDPOINTS["fills_history"]
        return await self.get_signed(
            instruction=endpoint.instruction,
            path=endpoint.path,
            params={"symbol": symbol, "limit": limit, "offset": offset},
        )

    async def get_fills(
        self,
        symbol: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        return await self.get_fills_history(symbol=symbol, limit=limit, offset=offset)

    async def get_funding_history(
        self,
        *,
        symbol: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        endpoint = SIGNED_ENDPOINTS["funding_history"]
        return await self.get_signed(
            instruction=endpoint.instruction,
            path=endpoint.path,
            params={"symbol": symbol, "limit": limit, "offset": offset},
        )

    async def get_markets(self) -> Any:
        return await self.get_public(PUBLIC_ENDPOINTS["markets"])

    async def get_market(self, symbol: str) -> Any:
        return await self.get_public(PUBLIC_ENDPOINTS["market"], params={"symbol": symbol})

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_type: str | None = None,
        price_source: object | None = None,
    ) -> Any:
        resolved_price_type = price_type
        if resolved_price_type is None and price_source is not None:
            value = getattr(price_source, "value", price_source)
            resolved_price_type = {
                "last": "Last",
                "mark": "Mark",
                "index": "Index",
            }.get(str(value).lower(), str(value))
        return await self.get_public(
            PUBLIC_ENDPOINTS["klines"],
            params={
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
                "priceType": resolved_price_type,
            },
        )

    async def get_open_interest(
        self,
        symbol: str | None = None,
        interval: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> Any:
        return await self.get_public(
            PUBLIC_ENDPOINTS["open_interest"],
            params={
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
            },
        )

    async def get_funding_rates(
        self,
        *,
        symbol: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        return await self.get_public(
            PUBLIC_ENDPOINTS["funding_rates"],
            params={"symbol": symbol, "limit": limit, "offset": offset},
        )

    def _build_signed_headers(
        self,
        *,
        instruction: str,
        params: Mapping[str, object | None],
    ) -> dict[str, str]:
        if not self._config.api_key or not self._config.private_key:
            raise BackpackAuthError("Signed Backpack requests require api_key and private_key.")

        timestamp_ms = int(time.time() * 1000)
        signature = sign_instruction(
            private_key=self._config.private_key,
            instruction=instruction,
            params=dict(params),
            timestamp_ms=timestamp_ms,
            window_ms=self._config.window_ms,
        )
        return {
            "X-API-Key": self._config.api_key,
            "X-Signature": signature,
            "X-Timestamp": str(timestamp_ms),
            "X-Window": str(self._config.window_ms),
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object | None],
        headers: Mapping[str, str] | None,
    ) -> Any:
        encoded_params = canonical_query_string(params)
        url = path
        if encoded_params:
            url = f"{path}?{encoded_params}"

        response = await self._client.request(method, url, headers=headers)

        if response.status_code >= 400:
            raise BackpackRequestError(
                f"Backpack request failed with status {response.status_code}.",
                status_code=response.status_code,
                payload=_safe_json(response),
            )

        return _safe_json(response)


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text
