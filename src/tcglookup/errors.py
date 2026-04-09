"""Error classes for the TCG Price Lookup API.

The API returns errors as ``{"error": "<message>"}``. This module maps
HTTP status codes to specific exception subclasses so callers can
``except`` on the precise failure mode they care about.
"""

from typing import Any


class TcgLookupError(Exception):
    """Base exception for any non-2xx response from the API."""

    def __init__(self, message: str, *, status: int, url: str, body: Any = None):
        super().__init__(message)
        self.status = status
        self.url = url
        self.body = body

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{type(self).__name__}(status={self.status}, message={self.args[0]!r})"


class AuthenticationError(TcgLookupError):
    """401 — missing or invalid API key."""


class PlanAccessError(TcgLookupError):
    """403 — your plan does not include access to this resource.

    Free plan keys hit this on price history endpoints. Upgrade to
    Trader or higher at https://tcgpricelookup.com/tcg-api.
    """


class NotFoundError(TcgLookupError):
    """404 — card / set / game does not exist."""


class RateLimitError(TcgLookupError):
    """429 — rate limit exceeded.

    Inspect ``client.rate_limit`` after the call to see your current
    quota window. Wait until the window resets or upgrade your plan.
    """


def error_from_response(*, status: int, url: str, body: Any) -> TcgLookupError:
    """Map an HTTP status to the most specific exception subclass."""
    message = _extract_message(body) or f"HTTP {status}"
    cls: type[TcgLookupError] = {
        401: AuthenticationError,
        403: PlanAccessError,
        404: NotFoundError,
        429: RateLimitError,
    }.get(status, TcgLookupError)
    return cls(message, status=status, url=url, body=body)


def _extract_message(body: Any) -> str | None:
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, str):
            return err
    return None
