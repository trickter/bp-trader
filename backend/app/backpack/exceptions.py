class BackpackError(Exception):
    """Base class for Backpack transport errors."""


class BackpackSigningError(BackpackError):
    """Raised when signing material or signature generation is invalid."""


class BackpackAuthError(BackpackError):
    """Raised when auth configuration is incomplete for a signed request."""


class BackpackRequestError(BackpackError):
    """Raised when the Backpack API request fails."""

    def __init__(self, message: str, status_code: int | None = None, payload: object | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
