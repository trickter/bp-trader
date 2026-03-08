from __future__ import annotations

import httpx
import pytest

from app.backpack.client import BackpackClient
from app.backpack.exceptions import BackpackRequestError
from app.backpack.types import BackpackAuthConfig


@pytest.mark.anyio
async def test_transport_errors_are_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    http_client = httpx.AsyncClient(
        base_url="https://api.backpack.exchange",
        transport=httpx.MockTransport(handler),
    )
    client = BackpackClient(BackpackAuthConfig(), http_client=http_client)

    with pytest.raises(BackpackRequestError) as exc_info:
        await client.get_public("/api/v1/markets")

    await http_client.aclose()

    error = exc_info.value
    assert str(error) == "Backpack request could not reach the provider."
    assert error.code == "backpack_transport_error"
    assert error.status_code == 502
    assert error.upstream_status is None
    assert error.retryable is True


@pytest.mark.anyio
async def test_upstream_http_errors_do_not_expose_payloads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            request=request,
            json={"message": "provider is down", "debug": {"traceId": "secret"}},
        )

    http_client = httpx.AsyncClient(
        base_url="https://api.backpack.exchange",
        transport=httpx.MockTransport(handler),
    )
    client = BackpackClient(BackpackAuthConfig(), http_client=http_client)

    with pytest.raises(BackpackRequestError) as exc_info:
        await client.get_public("/api/v1/markets")

    await http_client.aclose()

    error = exc_info.value
    assert str(error) == "Backpack request was rejected by the provider."
    assert error.code == "backpack_upstream_error"
    assert error.status_code == 503
    assert error.upstream_status == 503
    assert error.retryable is True
    assert error.to_response_detail() == {
        "code": "backpack_upstream_error",
        "message": "Backpack request was rejected by the provider.",
        "provider": "backpack",
        "retryable": True,
        "upstreamStatus": 503,
    }
