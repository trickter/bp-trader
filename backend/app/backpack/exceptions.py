class BackpackError(Exception):
    """Base class for Backpack transport errors."""


class BackpackSigningError(BackpackError):
    """Raised when signing material or signature generation is invalid."""


class BackpackAuthError(BackpackError):
    """Raised when auth configuration is incomplete for a signed request."""


class BackpackRequestError(BackpackError):
    """Raised when the Backpack API request fails in infrastructure-safe terms."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "backpack_request_failed",
        suggested_http_status: int | None = None,
        upstream_status: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.suggested_http_status = suggested_http_status
        self.upstream_status = upstream_status
        self.retryable = retryable

    @property
    def status_code(self) -> int | None:
        return self.suggested_http_status

    def to_error_context(self) -> dict[str, object]:
        context: dict[str, object] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.suggested_http_status is not None:
            context["statusCode"] = self.suggested_http_status
        if self.upstream_status is not None:
            context["upstreamStatus"] = self.upstream_status
        return context
