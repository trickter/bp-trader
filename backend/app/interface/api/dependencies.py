from __future__ import annotations

from fastapi import Request

from ...infrastructure.bootstrap import ServiceContainer


def get_services(request: Request) -> ServiceContainer:
    return request.app.state.services
