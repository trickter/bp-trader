from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .infrastructure.bootstrap import app_lifespan
from .interface.api.exception_handlers import register_exception_handlers
from .interface.api.router import api_router


app = FastAPI(
    title="Backpack Quant Console API",
    version="0.1.0",
    description="Normalized admin API for profile, strategies, backtests, execution, and settings.",
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck():
    return {
        "status": "ok",
        "environment": settings.app_env,
        "service": "backpack-quant-console-api",
        "backpackMode": settings.backpack_mode,
    }


register_exception_handlers(app)
app.include_router(api_router)
