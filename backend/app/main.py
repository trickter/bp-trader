from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .backpack import BackpackAuthConfig, BackpackAuthError, BackpackClient, BackpackRequestError
from .auth import require_admin_api_token
from .backtest_engine import build_backtest_result as build_backtest_result_from_candles
from .config import settings
from .mock_data import (
    ACCOUNT_EVENTS,
    ALERTS,
    ASSET_BALANCES,
    BACKTEST_RESULT,
    CANDLES,
    EXCHANGE_ACCOUNTS,
    MARKET_PULSE,
    MARKET_SYMBOLS,
    POSITIONS,
    PROFILE_SUMMARY,
    RISK_CONTROLS,
    STRATEGIES,
    build_backtest_acceptance,
)
from .providers import BackpackProvider, ProviderError
from .schemas import (
    AgentCapability,
    AgentContext,
    BacktestRequest,
    KlineResponse,
    PriceSource,
    RiskControls,
    StrategySummary,
    StrategyUpsertRequest,
)


def _normalized_risk_controls(request: Request) -> RiskControls:
    current = getattr(request.app.state, "risk_controls", RISK_CONTROLS)
    if isinstance(current, RiskControls):
        payload = current.model_dump()
    elif isinstance(current, dict):
        payload = current
    else:
        payload = {}
    normalized = RISK_CONTROLS.model_copy(update=payload)
    request.app.state.risk_controls = normalized
    return normalized


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.backpack_client = None
    app.state.backpack_provider = None
    app.state.backtest_runs = {"demo": BACKTEST_RESULT}
    app.state.strategy_registry = [item.model_copy(deep=True) for item in STRATEGIES]
    app.state.risk_controls = RISK_CONTROLS.model_copy(deep=True)
    app.state.market_symbols = list(MARKET_SYMBOLS)
    app.state.live_profile_snapshot_cache = {}
    app.state.live_profile_snapshot_locks = {}

    if settings.backpack_mode == "live":
        client = BackpackClient(
            BackpackAuthConfig(
                base_url=settings.backpack_api_base_url,
                api_key=settings.backpack_api_key or None,
                private_key=settings.backpack_private_key or None,
                window_ms=settings.backpack_window_ms,
            )
        )
        await client.__aenter__()
        app.state.backpack_client = client
        app.state.backpack_provider = BackpackProvider(
            client=client,
            account_label=settings.backpack_account_label,
            market_type=settings.backpack_default_market_type,
            default_price_source=PriceSource(settings.backpack_default_price_source),
        )

    try:
        yield
    finally:
        if app.state.backpack_client is not None:
            await app.state.backpack_client.__aexit__(None, None, None)


app = FastAPI(
    title="Backpack Quant Console API",
    version="0.1.0",
    description="Normalized admin API for profile, strategies, backtests, execution, and settings.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api", dependencies=[Depends(require_admin_api_token)])


@app.get("/healthz")
def healthcheck():
    return {
        "status": "ok",
        "environment": settings.app_env,
        "service": "backpack-quant-console-api",
        "backpackMode": settings.backpack_mode,
    }


@api_router.get("/profile/summary")
async def get_profile_summary(request: Request):
    return (await _load_profile_snapshot(request)).summary.data.model_dump(by_alias=True)


@api_router.get("/profile/assets")
async def get_profile_assets(request: Request):
    snapshot = await _load_profile_snapshot(request)
    return [item.data.model_dump(by_alias=True) for item in snapshot.assets.items]


@api_router.get("/profile/positions")
async def get_profile_positions(request: Request):
    snapshot = await _load_profile_snapshot(request)
    return [item.data.model_dump(by_alias=True) for item in snapshot.positions.items]


@api_router.get("/profile/account-events")
async def get_account_events(request: Request):
    events = await _load_account_events(request)
    return [item.data.model_dump(by_alias=True) for item in events.items]


@api_router.get("/strategies")
def get_strategies(request: Request):
    registry = getattr(request.app.state, "strategy_registry", STRATEGIES)
    return [item.model_dump(by_alias=True) for item in registry]


@api_router.get("/strategies/{strategy_id}")
def get_strategy(strategy_id: str, request: Request):
    strategy = _get_strategy_or_404(request, strategy_id)
    return strategy.model_dump(by_alias=True)


@api_router.post("/strategies", status_code=status.HTTP_201_CREATED)
def create_strategy(payload: StrategyUpsertRequest, request: Request):
    strategy_id = f"strat_{uuid4().hex[:8]}"
    strategy = StrategySummary(
        id=strategy_id,
        name=payload.name,
        kind=payload.kind,
        description=payload.description,
        market=payload.market,
        account_id=payload.account_id,
        runtime=payload.runtime,
        status=payload.status,
        last_backtest="",
        sharpe=0.0,
        price_source=payload.price_source,
        parameters=payload.parameters,
    )
    request.app.state.strategy_registry.append(strategy)
    return strategy.model_dump(by_alias=True)


@api_router.put("/strategies/{strategy_id}")
def update_strategy(strategy_id: str, payload: StrategyUpsertRequest, request: Request):
    strategy = _get_strategy_or_404(request, strategy_id)
    updated = strategy.model_copy(
        update={
            "name": payload.name,
            "kind": payload.kind,
            "description": payload.description,
            "market": payload.market,
            "account_id": payload.account_id,
            "runtime": payload.runtime,
            "status": payload.status,
            "price_source": payload.price_source,
            "parameters": payload.parameters,
        }
    )
    registry = getattr(request.app.state, "strategy_registry", [])
    for index, item in enumerate(registry):
        if item.id == strategy_id:
            registry[index] = updated
            break
    return updated.model_dump(by_alias=True)


@api_router.post("/strategies/templates/{template_id}/backtests")
async def create_template_backtest(template_id: str, request: BacktestRequest, http_request: Request):
    _get_strategy_or_404(http_request, template_id)
    return await _create_backtest_run(
        app_request=http_request,
        strategy_id=template_id,
        strategy_kind="template",
        request=request,
    )


@api_router.post("/strategies/scripts/{strategy_id}/backtests")
async def create_script_backtest(strategy_id: str, request: BacktestRequest, http_request: Request):
    _get_strategy_or_404(http_request, strategy_id)
    return await _create_backtest_run(
        app_request=http_request,
        strategy_id=strategy_id,
        strategy_kind="script",
        request=request,
    )


@api_router.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str, request: Request):
    registry = getattr(request.app.state, "backtest_runs", {})
    payload = registry.get(backtest_id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "backtest_not_found", "message": "Backtest run does not exist."},
        )
    return payload.model_dump(by_alias=True)


@api_router.get("/markets/pulse")
async def get_market_pulse(request: Request):
    market_pulse = await _load_market_pulse(request, symbol=settings.backpack_default_symbol)
    return [item.data.model_dump(by_alias=True) for item in market_pulse.metrics.items]


@api_router.get("/markets/pulse/{symbol}")
async def get_market_pulse_for_symbol(request: Request, symbol: str):
    market_pulse = await _load_market_pulse(request, symbol=symbol)
    return [item.data.model_dump(by_alias=True) for item in market_pulse.metrics.items]


@api_router.get("/markets/symbols")
def get_market_symbols(request: Request):
    return getattr(request.app.state, "market_symbols", MARKET_SYMBOLS)


@api_router.get("/markets/{symbol}/klines")
async def get_klines(
    request: Request,
    symbol: str,
    interval: str = Query(...),
    start_time: int = Query(..., description="UTC seconds"),
    end_time: int = Query(..., description="UTC seconds"),
    price_source: PriceSource = Query(...),
):
    if settings.backpack_mode == "live":
        payload = await _provider_fetch(
            request,
            lambda provider: provider.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                price_source=price_source,
            ),
        )
        return payload.data.model_dump(by_alias=True)

    from .mock_data import _generate_candles

    seed = sum(ord(char) for char in f"{symbol}:{interval}:{price_source}:{start_time}:{end_time}")
    payload = KlineResponse(
        symbol=symbol,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        price_source=price_source,
        candles=_generate_candles(
            symbol=symbol,
            seed=seed,
            request=BacktestRequest(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                price_source=price_source,
                fee_bps=0,
                slippage_bps=0,
            ),
        ),
    )
    return payload.model_dump(by_alias=True)


@api_router.get("/alerts")
def get_alerts():
    return [item.model_dump(by_alias=True) for item in ALERTS]


@api_router.get("/risk-controls")
def get_risk_controls(request: Request):
    controls = _normalized_risk_controls(request)
    return controls.model_dump(by_alias=True)


@api_router.put("/risk-controls")
def update_risk_controls(payload: RiskControls, request: Request):
    updated = payload.model_copy(
        update={"updated_at": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")}
    )
    request.app.state.risk_controls = _normalized_risk_controls(request).model_copy(update=updated.model_dump())
    return updated.model_dump(by_alias=True)


@api_router.get("/settings/accounts")
@api_router.get("/settings/exchange-accounts")
async def get_exchange_accounts(request: Request):
    accounts = await _load_exchange_accounts(request)
    return [item.data.model_dump(by_alias=True) for item in accounts.items]


@api_router.get("/agent/capabilities")
async def get_agent_capabilities():
    return [item.model_dump(by_alias=True) for item in _agent_capabilities()]


@api_router.get("/agent/context")
async def get_agent_context(request: Request):
    await _load_exchange_accounts(request)
    account_mode = "live" if settings.backpack_mode == "live" else "mock"
    resources = {
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
    }
    payload = AgentContext(
        mode="admin",
        account_mode=account_mode,
        available_capabilities=[item.id for item in _agent_capabilities()],
        capabilities=_agent_capabilities(),
        domain_vocabulary=[
            "price_source",
            "account_event",
            "strategy_spec",
            "execution_intent",
            "backtest_run",
            "market_pulse",
            "exchange_account",
        ],
        resources=resources,
    )
    return payload.model_dump(by_alias=True)


async def _create_backtest_run(
    *,
    app_request: Request,
    strategy_id: str,
    strategy_kind: str,
    request: BacktestRequest,
) -> dict[str, object]:
    strategy = _get_strategy_or_404(app_request, strategy_id)
    backtest_id = f"{strategy_kind}-{strategy_id}-{uuid4().hex[:8]}"
    created_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    payload = await _build_backtest_result(
        request=app_request,
        strategy=strategy,
        backtest_id=backtest_id,
        backtest_request=request,
        created_at=created_at,
    )
    app_request.app.state.backtest_runs[backtest_id] = payload
    acceptance = build_backtest_acceptance(
        backtest_id=backtest_id,
        strategy_id=strategy_id,
        strategy_kind=strategy_kind,
        created_at=created_at,
        demo_mode=settings.backpack_mode == "mock",
    )
    return acceptance.model_dump(by_alias=True)


async def _build_backtest_result(
    *,
    request: Request,
    strategy: StrategySummary,
    backtest_id: str,
    backtest_request: BacktestRequest,
    created_at: str,
):
    if settings.backpack_mode == "live":
        kline_payload = await _provider_fetch(
            request,
            lambda provider: provider.fetch_klines(
                symbol=backtest_request.symbol,
                interval=backtest_request.interval,
                start_time=backtest_request.start_time,
                end_time=backtest_request.end_time,
                price_source=backtest_request.price_source,
            ),
        )
        candles = kline_payload.data.candles
        exchange_id = "backpack"
        market_type = settings.backpack_default_market_type
    else:
        from .mock_data import _generate_candles

        seed = sum(ord(char) for char in f"{strategy.id}:{backtest_request.symbol}:{backtest_request.price_source}:{backtest_request.interval}")
        candles = _generate_candles(symbol=backtest_request.symbol, seed=seed, request=backtest_request)
        exchange_id = "mock"
        market_type = "perp"

    return build_backtest_result_from_candles(
        backtest_id=backtest_id,
        strategy=strategy,
        request=backtest_request,
        risk_controls=getattr(request.app.state, "risk_controls", RISK_CONTROLS),
        candles=candles,
        created_at=created_at,
        exchange_id=exchange_id,
        market_type=market_type,
    )


async def _load_profile_snapshot(request: Request):
    if settings.backpack_mode != "live":
        return _build_mock_profile_snapshot()
    return await _request_cache(
        request,
        "profile_snapshot",
        lambda: _load_live_profile_snapshot(
            request,
            PriceSource(settings.backpack_default_price_source),
        ),
    )


async def _load_account_events(request: Request):
    if settings.backpack_mode != "live":
        return _build_mock_account_events()
    return await _request_cache(
        request,
        "account_events",
        lambda: _provider_fetch(
            request,
            lambda provider: provider.fetch_account_events(
                symbol=settings.backpack_default_symbol,
                limit=50,
            ),
        ),
    )


async def _load_market_pulse(request: Request, symbol: str):
    if settings.backpack_mode != "live":
        return _build_mock_market_pulse(symbol)
    return await _request_cache(
        request,
        f"market_pulse:{symbol}",
        lambda: _provider_fetch(
            request,
            lambda provider: provider.fetch_market_pulse(
                symbol=symbol,
                price_source=PriceSource(settings.backpack_default_price_source),
                include_klines=False,
            ),
        ),
    )


async def _load_exchange_accounts(request: Request):
    if settings.backpack_mode != "live":
        return _build_mock_exchange_accounts()
    return await _request_cache(
        request,
        "exchange_accounts",
        lambda: _provider_fetch(request, lambda provider: provider.fetch_exchange_accounts()),
    )


async def _request_cache(request: Request, key: str, factory):
    cache = request.scope.setdefault("quant_cache", {})
    if key not in cache:
        cache[key] = asyncio.create_task(factory())
    return await cache[key]


LIVE_PROFILE_SNAPSHOT_TTL_SECONDS = 1.0


async def _load_live_profile_snapshot(request: Request, price_source: PriceSource):
    cache_key = price_source.value
    cache = request.app.state.live_profile_snapshot_cache
    locks = request.app.state.live_profile_snapshot_locks

    entry = cache.get(cache_key)
    now = time.monotonic()
    if entry is not None and entry["expires_at"] > now:
        return entry["snapshot"]

    lock = locks.setdefault(cache_key, asyncio.Lock())
    async with lock:
        entry = cache.get(cache_key)
        now = time.monotonic()
        if entry is not None and entry["expires_at"] > now:
            return entry["snapshot"]

        snapshot = await _provider_fetch(
            request,
            lambda provider: provider.fetch_account_snapshot(price_source=price_source),
        )
        cache[cache_key] = {
            "snapshot": snapshot,
            "expires_at": now + LIVE_PROFILE_SNAPSHOT_TTL_SECONDS,
        }
        return snapshot


def _build_mock_profile_snapshot():
    from .providers.base import AccountSnapshot, NormalizedList, NormalizedRecord

    return AccountSnapshot(
        summary=NormalizedRecord(data=PROFILE_SUMMARY, raw_payload=PROFILE_SUMMARY.model_dump(by_alias=True)),
        assets=NormalizedList(
            items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in ASSET_BALANCES]
        ),
        positions=NormalizedList(
            items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in POSITIONS]
        ),
    )


def _build_mock_account_events():
    from .providers.base import NormalizedList, NormalizedRecord

    return NormalizedList(
        items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in ACCOUNT_EVENTS]
    )


def _build_mock_market_pulse(symbol: str):
    from .providers.base import MarketPulseSnapshot, NormalizedList, NormalizedRecord

    base = symbol.split("_", 1)[0]
    return MarketPulseSnapshot(
        metrics=NormalizedList(
            items=[
                NormalizedRecord(
                    data=item.model_copy(update={"label": item.label.replace("BTC", base)}),
                    raw_payload=item.model_dump(by_alias=True),
                )
                for item in MARKET_PULSE
            ]
        )
    )


def _build_mock_exchange_accounts():
    from .providers.base import NormalizedList, NormalizedRecord

    return NormalizedList(
        items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in EXCHANGE_ACCOUNTS]
    )


def _agent_capabilities() -> list[AgentCapability]:
    return [
        AgentCapability(
            id="profile.summary.read",
            label="Read profile summary",
            description="Read normalized equity, margin, pnl, and sync state.",
            route="/api/profile/summary",
            entity="profile_summary",
        ),
        AgentCapability(
            id="profile.assets.read",
            label="Read asset balances",
            description="Read normalized asset balances with collateral value and weight.",
            route="/api/profile/assets",
            entity="asset_balance",
        ),
        AgentCapability(
            id="profile.positions.read",
            label="Read open positions",
            description="Read normalized positions with mark price and pnl.",
            route="/api/profile/positions",
            entity="position",
        ),
        AgentCapability(
            id="profile.events.read",
            label="Read account ledger",
            description="Read normalized account events for fills, funding, fees, and system actions.",
            route="/api/profile/account-events",
            entity="account_event",
        ),
        AgentCapability(
            id="strategies.read",
            label="Read strategies",
            description="Read strategy registry metadata and last backtest context.",
            route="/api/strategies",
            entity="strategy",
        ),
        AgentCapability(
            id="strategies.write",
            label="Write strategies",
            description="Create or update strategy definitions and parameters.",
            read_only=False,
            route="/api/strategies",
            entity="strategy",
        ),
        AgentCapability(
            id="backtests.create",
            label="Create backtest run",
            description="Create a backtest run using the same request contract as the admin UI.",
            route="/api/strategies/{template_or_script}/backtests",
            entity="backtest_run",
        ),
        AgentCapability(
            id="backtests.read",
            label="Read backtest result",
            description="Read a normalized backtest result by id.",
            route="/api/backtests/{id}",
            entity="backtest_result",
        ),
        AgentCapability(
            id="markets.pulse.read",
            label="Read market pulse",
            description="Read operator-facing market pulse metrics with freshness semantics.",
            route="/api/markets/pulse",
            entity="market_metric",
        ),
        AgentCapability(
            id="markets.symbols.read",
            label="Read market symbols",
            description="Read the supported market symbols for UI selectors and agents.",
            route="/api/markets/symbols",
            entity="market_symbol",
        ),
        AgentCapability(
            id="markets.klines.read",
            label="Read klines",
            description="Read normalized klines by symbol, interval, time range, and price source.",
            route="/api/markets/{symbol}/klines",
            entity="kline",
        ),
        AgentCapability(
            id="risk_controls.read",
            label="Read risk controls",
            description="Read the explicit operator risk envelope.",
            route="/api/risk-controls",
            entity="risk_controls",
        ),
        AgentCapability(
            id="risk_controls.write",
            label="Write risk controls",
            description="Update the explicit operator risk envelope.",
            read_only=False,
            route="/api/risk-controls",
            entity="risk_controls",
        ),
        AgentCapability(
            id="settings.exchange_accounts.read",
            label="Read exchange accounts",
            description="Read normalized exchange-account metadata and credential rotation state.",
            route="/api/settings/accounts",
            entity="exchange_account",
        ),
    ]


def _get_strategy_or_404(request: Request, strategy_id: str) -> StrategySummary:
    registry = getattr(request.app.state, "strategy_registry", STRATEGIES)
    for item in registry:
        if item.id == strategy_id:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "strategy_not_found", "message": "Strategy does not exist."},
    )


async def _provider_fetch(request: Request, callback):
    provider = getattr(request.app.state, "backpack_provider", None)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_provider_error_detail(
                code="provider_not_initialized",
                message="Backpack live provider is not initialized.",
                retryable=True,
            ),
        )
    try:
        return await callback(provider)
    except BackpackAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_provider_error_detail(
                code="provider_auth_error",
                message=str(exc),
                retryable=False,
            ),
        ) from exc
    except BackpackRequestError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=exc.to_response_detail(),
        ) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_provider_error_detail(
                code="provider_response_invalid",
                message=str(exc),
                retryable=False,
            ),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _provider_error_detail(*, code: str, message: str, retryable: bool) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "provider": "backpack",
        "retryable": retryable,
    }


app.include_router(api_router)
