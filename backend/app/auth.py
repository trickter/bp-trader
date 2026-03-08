from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Header, HTTPException, status

from .config import settings


async def require_admin_api_token(
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-Token header.",
        )

    if not hmac.compare_digest(x_admin_token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API token.",
        )
