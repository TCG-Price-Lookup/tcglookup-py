"""Synchronous and async client for the TCG Price Lookup API."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

import httpx

from .errors import error_from_response

DEFAULT_BASE_URL = "https://api.tcgpricelookup.com/v1"
DEFAULT_USER_AGENT = "tcglookup-py/0.1.0"
SEARCH_IDS_CHUNK_SIZE = 20


class _RateLimit:
    """Rate-limit info captured from the most recent response headers."""

    __slots__ = ("limit", "remaining")

    def __init__(self) -> None:
        self.limit: Optional[int] = None
        self.remaining: Optional[int] = None


class TcgLookupClient:
    """Synchronous client for the TCG Price Lookup REST API.

    Args:
        api_key: Your API key. Get one free at
            https://tcgpricelookup.com/tcg-api.
        base_url: Override the API base URL. Defaults to production.
        timeout: Per-request timeout in seconds. Default 30.
        user_agent: Override the User-Agent header.

    Example:

        >>> client = TcgLookupClient(api_key="tlk_live_...")
        >>> result = client.cards.search(q="charizard", game="pokemon")
        >>> for card in result["data"]:
        ...     print(card["name"])
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        user_agent: str = DEFAULT_USER_AGENT,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_key or not isinstance(api_key, str):
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._user_agent = user_agent
        self._http = http_client or httpx.Client(timeout=timeout)
        self.rate_limit = _RateLimit()

        self.cards = CardsResource(self)
        self.sets = SetsResource(self)
        self.games = GamesResource(self)

    # ------------------------------------------------------------------ public

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "TcgLookupClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ----------------------------------------------------------------- internal

    def _request(
        self,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
    ) -> Any:
        url = self._base_url + (path if path.startswith("/") else f"/{path}")
        params = _clean_query(query)
        response = self._http.get(
            url,
            params=params,
            headers={
                "X-API-Key": self._api_key,
                "Accept": "application/json",
                "User-Agent": self._user_agent,
            },
        )
        self._capture_rate_limit(response)
        body = _parse_body(response)
        if response.is_error:
            raise error_from_response(
                status=response.status_code, url=str(response.url), body=body
            )
        return body

    def _capture_rate_limit(self, response: httpx.Response) -> None:
        limit = response.headers.get("x-ratelimit-limit")
        remaining = response.headers.get("x-ratelimit-remaining")
        self.rate_limit.limit = int(limit) if limit else None
        self.rate_limit.remaining = int(remaining) if remaining else None


def _clean_query(query: Mapping[str, Any] | None) -> dict[str, str]:
    if not query:
        return {}
    out: dict[str, str] = {}
    for key, value in query.items():
        if value is None or value == "":
            continue
        out[key] = str(value)
    return out


def _parse_body(response: httpx.Response) -> Any:
    text = response.text
    if not text:
        return None
    try:
        return response.json()
    except ValueError:
        return text


# ============================================================ resources


class CardsResource:
    """Operations on cards."""

    def __init__(self, client: "TcgLookupClient") -> None:
        self._client = client

    def search(
        self,
        *,
        q: str | None = None,
        ids: Iterable[str] | None = None,
        game: str | None = None,
        set: str | None = None,  # noqa: A002 — matches API param name
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Search cards by name, set, game, or batch by IDs.

        Passing more than 20 IDs auto-chunks into multiple requests.

        Returns a paginated dict::

            {"data": [<card>, ...], "total": int, "limit": int, "offset": int}
        """
        ids_list = list(ids) if ids else []
        if not ids_list:
            return self._search_once(
                q=q, ids=None, game=game, set=set, limit=limit, offset=offset
            )
        if len(ids_list) <= SEARCH_IDS_CHUNK_SIZE:
            return self._search_once(
                q=q, ids=",".join(ids_list), game=game, set=set, limit=limit, offset=offset
            )
        return self._search_chunked(
            ids_list, q=q, game=game, set=set, limit=limit, offset=offset
        )

    def get(self, card_id: str) -> dict[str, Any]:
        """Get a single card by its UUID."""
        if not card_id:
            raise ValueError("card_id is required")
        return self._client._request(f"/cards/{card_id}")

    def history(
        self, card_id: str, *, period: str | None = None
    ) -> dict[str, Any]:
        """Daily price history for a card.

        Trader plan and above. Free-tier keys raise PlanAccessError.

        Args:
            period: One of ``"7d"``, ``"30d"``, ``"90d"``, ``"1y"``.
        """
        if not card_id:
            raise ValueError("card_id is required")
        return self._client._request(
            f"/cards/{card_id}/history", query={"period": period}
        )

    # -- helpers --------------------------------------------------------

    def _search_once(
        self,
        *,
        q: str | None,
        ids: str | None,
        game: str | None,
        set: str | None,  # noqa: A002
        limit: int | None,
        offset: int | None,
    ) -> dict[str, Any]:
        return self._client._request(
            "/cards/search",
            query={
                "q": q,
                "ids": ids,
                "game": game,
                "set": set,
                "limit": limit,
                "offset": offset,
            },
        )

    def _search_chunked(
        self,
        ids: list[str],
        *,
        q: str | None,
        game: str | None,
        set: str | None,  # noqa: A002
        limit: int | None,
        offset: int | None,
    ) -> dict[str, Any]:
        merged: list[Any] = []
        for i in range(0, len(ids), SEARCH_IDS_CHUNK_SIZE):
            chunk = ids[i : i + SEARCH_IDS_CHUNK_SIZE]
            page = self._search_once(
                q=q,
                ids=",".join(chunk),
                game=game,
                set=set,
                limit=limit,
                offset=offset,
            )
            merged.extend(page.get("data", []))
        return {
            "data": merged,
            "total": len(merged),
            "limit": limit if limit is not None else len(merged),
            "offset": offset if offset is not None else 0,
        }


class SetsResource:
    """Operations on sets."""

    def __init__(self, client: "TcgLookupClient") -> None:
        self._client = client

    def list(
        self,
        *,
        game: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List sets across all games, or filter by game slug."""
        return self._client._request(
            "/sets", query={"game": game, "limit": limit, "offset": offset}
        )


class GamesResource:
    """Operations on games."""

    def __init__(self, client: "TcgLookupClient") -> None:
        self._client = client

    def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List every supported trading card game."""
        return self._client._request(
            "/games", query={"limit": limit, "offset": offset}
        )
