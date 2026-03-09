from __future__ import annotations

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from ...application.errors import ApplicationError
from ...domain.shared.errors import NotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def handle_application_error(_, exc: ApplicationError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.to_detail()})

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": {"code": exc.code, "message": exc.message}},
        )
