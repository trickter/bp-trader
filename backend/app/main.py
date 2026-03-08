from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .backpack import BackpackAuthConfig, BackpackAuthError, BackpackClient, BackpackRequestError
from .auth import require_admin_api_token
from .config import settings
from .mock_data import (
    ACCOUNT_EVENTS,
    ALERTS,
    ASSET_BALANCES,
    BACKTEST_RESULT,
    CANDLES,
    EXCHANGE_ACCOUNTS,
    MARKET_PULSE,
    POSITIONS,
    PROFILE_SUMMARY,
    STRATEGIES,
)
from .providers import BackpackProvider, ProviderError
from .schemas import BacktestRequest, KlineResponse, PriceSource


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.backpack_client = None
    app.state.backpack_provider = None

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
    if settings.backpack_mode == "live":
        snapshot = await _provider_fetch(
            request,
            lambda provider: provider.fetch_account_snapshot(
                price_source=PriceSource(settings.backpack_default_price_source)
            ),
        )
        return snapshot.summary.data.model_dump(by_alias=True)
    return PROFILE_SUMMARY.model_dump(by_alias=True)


@api_router.get("/profile/assets")
async def get_profile_assets(request: Request):
    if settings.backpack_mode == "live":
        snapshot = await _provider_fetch(
            request,
            lambda provider: provider.fetch_account_snapshot(
                price_source=PriceSource(settings.backpack_default_price_source)
            ),
        )
        return [item.data.model_dump(by_alias=True) for item in snapshot.assets.items]
    return [item.model_dump(by_alias=True) for item in ASSET_BALANCES]


@api_router.get("/profile/positions")
async def get_profile_positions(request: Request):
    if settings.backpack_mode == "live":
        snapshot = await _provider_fetch(
            request,
            lambda provider: provider.fetch_account_snapshot(
                price_source=PriceSource(settings.backpack_default_price_source)
            ),
        )
        return [item.data.model_dump(by_alias=True) for item in snapshot.positions.items]
    return [item.model_dump(by_alias=True) for item in POSITIONS]


@api_router.get("/profile/account-events")
async def get_account_events(request: Request):
    if settings.backpack_mode == "live":
        events = await _provider_fetch(
            request,
            lambda provider: provider.fetch_account_events(
                symbol=settings.backpack_default_symbol,
                limit=50,
            ),
        )
        return [item.data.model_dump(by_alias=True) for item in events.items]
    return [item.model_dump(by_alias=True) for item in ACCOUNT_EVENTS]


@api_router.get("/strategies")
def get_strategies():
    return [item.model_dump(by_alias=True) for item in STRATEGIES]


@api_router.post("/strategies/templates/{template_id}/backtests")
def create_template_backtest(template_id: str, request: BacktestRequest):
    payload = BACKTEST_RESULT.model_copy(
        update={
            "id": f"template-{template_id}-preview",
            "price_source": request.price_source,
        }
    )
    return payload.model_dump(by_alias=True)


@api_router.post("/strategies/scripts/{strategy_id}/backtests")
def create_script_backtest(strategy_id: str, request: BacktestRequest):
    payload = BACKTEST_RESULT.model_copy(
        update={
            "id": f"script-{strategy_id}-preview",
            "price_source": request.price_source,
        }
    )
    return payload.model_dump(by_alias=True)


@api_router.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str):
    payload = BACKTEST_RESULT.model_copy(update={"id": backtest_id})
    return payload.model_dump(by_alias=True)


@api_router.get("/markets/pulse")
async def get_market_pulse(request: Request):
    if settings.backpack_mode == "live":
        market_pulse = await _provider_fetch(
            request,
            lambda provider: provider.fetch_market_pulse(
                symbol=settings.backpack_default_symbol,
                interval=settings.backpack_default_interval,
                start_time=0,
                end_time=0,
                price_source=PriceSource(settings.backpack_default_price_source),
            ),
        )
        return [item.data.model_dump(by_alias=True) for item in market_pulse.metrics.items]
    return [item.model_dump(by_alias=True) for item in MARKET_PULSE]


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

    payload = KlineResponse(
        symbol=symbol,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        price_source=price_source,
        candles=CANDLES,
    )
    return payload.model_dump(by_alias=True)


@api_router.get("/alerts")
def get_alerts():
    return [item.model_dump(by_alias=True) for item in ALERTS]


@api_router.get("/settings/accounts")
@api_router.get("/settings/exchange-accounts")
async def get_exchange_accounts(request: Request):
    if settings.backpack_mode == "live":
        accounts = await _provider_fetch(request, lambda provider: provider.fetch_exchange_accounts())
        return [item.data.model_dump(by_alias=True) for item in accounts.items]
    return [item.model_dump(by_alias=True) for item in EXCHANGE_ACCOUNTS]


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
