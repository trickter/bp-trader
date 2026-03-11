from __future__ import annotations


class ApplicationError(RuntimeError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        retryable: bool = False,
        provider: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.provider = provider
        self.metadata = metadata or {}

    def to_detail(self) -> dict[str, object]:
        detail: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }
        if self.provider:
            detail["provider"] = self.provider
            detail["retryable"] = self.retryable
        detail.update(self.metadata)
        return detail


def from_backpack_request_error(exc) -> ApplicationError:
    metadata: dict[str, object] = {}
    if exc.upstream_status is not None:
        metadata["upstreamStatus"] = exc.upstream_status
    if getattr(exc, "upstream_code", None) is not None:
        metadata["upstreamCode"] = exc.upstream_code
    return ApplicationError(
        code=exc.code,
        message=exc.message,
        status_code=exc.suggested_http_status or 502,
        retryable=exc.retryable,
        provider="backpack",
        metadata=metadata,
    )
