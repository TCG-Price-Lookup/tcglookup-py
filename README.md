# tcglookup-py

[![PyPI version](https://img.shields.io/pypi/v/tcglookup.svg)](https://pypi.org/project/tcglookup/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Powered by TCG Price Lookup](https://img.shields.io/badge/powered%20by-TCG%20Price%20Lookup-purple.svg)](https://tcgpricelookup.com/tcg-api)

The official Python SDK for the [**TCG Price Lookup API**](https://tcgpricelookup.com/tcg-api) — live trading card prices across **Pokemon, Magic: The Gathering, Yu-Gi-Oh!, Disney Lorcana, One Piece TCG, Star Wars: Unlimited, and Flesh and Blood**.

One API for every major trading card game. TCGPlayer market prices, eBay sold averages, and PSA / BGS / CGC graded comps — all in one place.

## Install

```bash
pip install tcglookup
```

## Quickstart

```python
from tcglookup import TcgLookupClient

client = TcgLookupClient(api_key="tlk_live_...")

# Search for cards
results = client.cards.search(q="charizard", game="pokemon", limit=5)
for card in results["data"]:
    print(card["name"], card["prices"]["raw"])

# Get a single card by ID
card = client.cards.get("a3f8c1e2-...")
print(card["name"], card["prices"])

# Daily price history (paid plans)
history = client.cards.history("a3f8c1e2-...", period="30d")
for day in history["data"]:
    print(day["date"], day["prices"])

# List all supported games
for game in client.games.list()["data"]:
    print(game["slug"], game["name"], game["count"], "cards")
```

## Get an API key

Sign up at [tcgpricelookup.com/tcg-api](https://tcgpricelookup.com/tcg-api). The free tier includes TCGPlayer market prices. Paid plans unlock eBay sold averages, PSA / BGS / CGC graded prices, and full price history.

## API surface

### Cards

```python
client.cards.search(
    q="blue-eyes white dragon",
    game="yugioh",       # pokemon | mtg | yugioh | onepiece | lorcana | swu | fab
    set="lob",           # set slug
    limit=20,
    offset=0,
)

client.cards.get("<card-uuid>")

client.cards.history("<card-uuid>", period="30d")  # 7d | 30d | 90d | 1y

# Resolve one exact printing by set + collector number.
# Reliable for special treatments (Showcase, Borderless, Extended Art,
# Etched Foil), which a name search would shadow with the base printing.
card = client.cards.resolve_printing(
    game="magic",
    set="commander-legends-battle-for-baldurs-gate",
    number="418",        # the Showcase collector number, not the base 270
    variant="Foil",      # optional: "Normal" | "Foil" when a number has both
)
print(card["id"], card["name"])  # -> the exact Showcase Foil UUID
```

### Sets

```python
client.sets.list(game="mtg", limit=50)
```

### Games

```python
client.games.list()
```

### Batch lookups

Pass an iterable of IDs and the SDK auto-chunks into 20-ID batches:

```python
results = client.cards.search(ids=["uuid1", "uuid2", ..., "uuid100"])
```

## Error handling

```python
from tcglookup import (
    TcgLookupClient,
    AuthenticationError,
    PlanAccessError,
    NotFoundError,
    RateLimitError,
)

client = TcgLookupClient(api_key="tlk_live_...")

try:
    history = client.cards.history("<uuid>", period="1y")
except AuthenticationError:
    print("Bad API key")
except PlanAccessError:
    print("History requires a paid plan — upgrade at tcgpricelookup.com/tcg-api")
except NotFoundError:
    print("That card doesn't exist")
except RateLimitError:
    print(f"Rate limited. Quota: {client.rate_limit.remaining}/{client.rate_limit.limit}")
```

## Rate limits

After every successful request, the most recent rate-limit headers are available on the client:

```python
client.cards.search(q="pikachu")
print(client.rate_limit.remaining, "/", client.rate_limit.limit)
```

## Use as a context manager

```python
with TcgLookupClient(api_key="tlk_live_...") as client:
    cards = client.cards.search(q="black lotus", game="mtg")
# HTTP connection pool is closed automatically
```

## Sister SDKs

- [tcglookup-js](https://github.com/TCG-Price-Lookup/tcglookup-js) — JavaScript / TypeScript
- [tcglookup-go](https://github.com/TCG-Price-Lookup/tcglookup-go) — Go
- [tcglookup-rs](https://github.com/TCG-Price-Lookup/tcglookup-rs) — Rust
- [tcglookup-php](https://github.com/TCG-Price-Lookup/tcglookup-php) — PHP
- [tcglookup CLI](https://www.npmjs.com/package/tcglookup) — terminal client
- [tcg-api-examples](https://github.com/TCG-Price-Lookup/tcg-api-examples) — runnable code samples in 8 languages
- [tcg-discord-bot](https://github.com/TCG-Price-Lookup/tcg-discord-bot) — self-hosted Discord bot with slash commands

The full developer ecosystem index lives at **[awesome-tcg](https://github.com/TCG-Price-Lookup/awesome-tcg)**.

## License

MIT — see [LICENSE](LICENSE).

---

Built by [TCG Price Lookup](https://tcgpricelookup.com). Get a free API key at [tcgpricelookup.com/tcg-api](https://tcgpricelookup.com/tcg-api).
