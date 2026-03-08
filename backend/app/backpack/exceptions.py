class BackpackError(Exception):
    """Base class for Backpack transport errors."""


class BackpackSigningError(BackpackError):
    """Raised when signing material or signature generation is invalid."""


class BackpackAuthError(BackpackError):
    """Raised when auth configuration is incomplete for a signed request."""


class BackpackRequestError(BackpackError):
    """Raised when the Backpack API request fails in a client-safe way."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "backpack_request_failed",
        status_code: int | None = None,
        upstream_status: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.upstream_status = upstream_status
        self.retryable = retryable

    def to_response_detail(self) -> dict[str, object]:
        detail: dict[str, object] = {
            "code": self.code,
            "message": str(self),
            "provider": "backpack",
            "retryable": self.retryable,
        }
        if self.upstream_status is not None:
            detail["upstreamStatus"] = self.upstream_status
        return detail
