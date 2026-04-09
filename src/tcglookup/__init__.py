"""TCG Price Lookup — Python SDK.

Live trading card prices across Pokemon, MTG, Yu-Gi-Oh, Lorcana,
One Piece, Star Wars: Unlimited, and Flesh and Blood.

Quickstart:

    from tcglookup import TcgLookupClient

    client = TcgLookupClient(api_key="tlk_live_...")
    results = client.cards.search(q="charizard", game="pokemon", limit=5)
    for card in results["data"]:
        print(card["name"], card["prices"])

Get a free API key at https://tcgpricelookup.com/tcg-api
"""

from .client import TcgLookupClient
from .errors import (
    TcgLookupError,
    AuthenticationError,
    PlanAccessError,
    NotFoundError,
    RateLimitError,
)

__version__ = "0.1.0"
__all__ = [
    "TcgLookupClient",
    "TcgLookupError",
    "AuthenticationError",
    "PlanAccessError",
    "NotFoundError",
    "RateLimitError",
]
