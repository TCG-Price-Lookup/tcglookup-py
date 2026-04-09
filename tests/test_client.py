"""Smoke tests for the synchronous client.

Uses pytest-httpx to mock the HTTP layer, so these run without
hitting the live API. To run against the real API, set the
``TCGLOOKUP_API_KEY`` env var and remove the mock.
"""

import pytest
from pytest_httpx import HTTPXMock

from tcglookup import (
    AuthenticationError,
    NotFoundError,
    PlanAccessError,
    RateLimitError,
    TcgLookupClient,
)


def make_client() -> TcgLookupClient:
    return TcgLookupClient(api_key="tlk_test_xxx")


def test_search_passes_query_params(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.tcgpricelookup.com/v1/cards/search?q=charizard&game=pokemon&limit=5",
        json={"data": [], "total": 0, "limit": 5, "offset": 0},
    )
    client = make_client()
    result = client.cards.search(q="charizard", game="pokemon", limit=5)
    assert result["total"] == 0


def test_get_card_by_id(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.tcgpricelookup.com/v1/cards/abc-123",
        json={"id": "abc-123", "name": "Charizard"},
    )
    client = make_client()
    card = client.cards.get("abc-123")
    assert card["name"] == "Charizard"


def test_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.tcgpricelookup.com/v1/games",
        status_code=401,
        json={"error": "invalid api key"},
    )
    client = make_client()
    with pytest.raises(AuthenticationError) as exc:
        client.games.list()
    assert exc.value.status == 401


def test_plan_access_error_on_history(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.tcgpricelookup.com/v1/cards/abc-123/history?period=30d",
        status_code=403,
        json={"error": "history requires Trader plan"},
    )
    client = make_client()
    with pytest.raises(PlanAccessError):
        client.cards.history("abc-123", period="30d")


def test_not_found_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.tcgpricelookup.com/v1/cards/missing",
        status_code=404,
        json={"error": "card not found"},
    )
    client = make_client()
    with pytest.raises(NotFoundError):
        client.cards.get("missing")


def test_rate_limit_error_and_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.tcgpricelookup.com/v1/cards/search?q=pikachu",
        status_code=429,
        json={"error": "rate limit exceeded"},
        headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "0"},
    )
    client = make_client()
    with pytest.raises(RateLimitError):
        client.cards.search(q="pikachu")
    assert client.rate_limit.limit == 100
    assert client.rate_limit.remaining == 0


def test_batch_search_chunks_over_20_ids(httpx_mock: HTTPXMock) -> None:
    ids = [f"id-{i}" for i in range(45)]
    # First chunk: 20
    httpx_mock.add_response(
        url=httpx_mock.IS_MATCH_ALL_URLS if hasattr(httpx_mock, "IS_MATCH_ALL_URLS") else None,
        method="GET",
        json={"data": [{"id": f"id-{i}"} for i in range(20)], "total": 20, "limit": 20, "offset": 0},
    )
    httpx_mock.add_response(
        method="GET",
        json={"data": [{"id": f"id-{i}"} for i in range(20, 40)], "total": 20, "limit": 20, "offset": 0},
    )
    httpx_mock.add_response(
        method="GET",
        json={"data": [{"id": f"id-{i}"} for i in range(40, 45)], "total": 5, "limit": 5, "offset": 0},
    )
    client = make_client()
    result = client.cards.search(ids=ids)
    assert len(result["data"]) == 45
