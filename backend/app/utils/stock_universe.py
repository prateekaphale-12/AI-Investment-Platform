"""Pre-defined ticker universes by sector/theme for deterministic planning."""

from __future__ import annotations

# ~30 symbols across sectors (expandable)
SECTOR_TICKERS: dict[str, list[str]] = {
    "technology": ["AAPL", "MSFT", "GOOGL", "META", "CRM", "ORCL"],
    "semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "MU"],
    "healthcare": ["JNJ", "UNH", "LLY", "PFE", "ABBV"],
    "financials": ["JPM", "BAC", "GS", "MS", "V"],
    "consumer": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
    "energy": ["XOM", "CVX", "COP"],
}

# Aliases users might type (case-insensitive matching in planner)
ALIASES: dict[str, str] = {
    "ai": "technology",
    "software": "technology",
    "tech": "technology",
    "chips": "semiconductors",
    "semis": "semiconductors",
    "finance": "financials",
    "banking": "financials",
    "retail": "consumer",
    "auto": "consumer",
}


def normalize_sector_key(name: str) -> str:
    n = name.strip().lower().replace("&", "and")
    return ALIASES.get(n, n)


def tickers_for_interests(interests: list[str]) -> list[str]:
    if not interests:
        return sum(SECTOR_TICKERS.values(), [])[:12]
    out: list[str] = []
    seen: set[str] = set()
    for raw in interests:
        key = normalize_sector_key(raw)
        for sector, ticks in SECTOR_TICKERS.items():
            if key == sector or key in sector or sector in key:
                for t in ticks:
                    if t not in seen:
                        seen.add(t)
                        out.append(t)
    if not out:
        return sum(SECTOR_TICKERS.values(), [])[:12]
    return out


def available_sectors() -> list[str]:
    return sorted(SECTOR_TICKERS.keys())
