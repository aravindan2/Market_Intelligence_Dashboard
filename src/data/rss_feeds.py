"""
RSS aggregator for oil/commodity news. Cached 15–30 min.
Expanded categories: Petroleum, OPEC, Geopolitical, Weather, Industry, Macro.
Keyword tagging for risk radar.
"""
from __future__ import annotations

import re
import time
from typing import Any

try:
    import feedparser
except ImportError:
    feedparser = None

from data.news_sentiment import get_sentiment

# Curated oil/commodity feeds (no API key). (source_name, url, category)
FEEDS = [
    # Petroleum & EIA
    ("EIA - This Week in Petroleum", "https://www.eia.gov/rss/petroleum.xml", "Petroleum & EIA"),
    ("EIA - Today in Energy", "https://www.eia.gov/rss/todayinenergy.xml", "Petroleum & EIA"),
    # OPEC & Markets (primary + fallback; OilPrice also carries OPEC/market news)
    ("OPEC News", "https://www.opec.org/opec_web/en/rss.xml", "OPEC & Markets"),
    ("Reuters Energy", "https://feeds.reuters.com/reuters/energyNews", "OPEC & Markets"),
    # Geopolitical
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "Geopolitical"),
    ("Guardian Energy", "https://www.theguardian.com/environment/energy/rss", "Geopolitical"),
    # Weather & Natural Risk
    ("NHC Atlantic", "https://www.nhc.noaa.gov/index-at.xml", "Weather & Natural Risk"),
    ("NHC Eastern Pacific", "https://www.nhc.noaa.gov/index-ep.xml", "Weather & Natural Risk"),
    # Industry & Markets (OilPrice covers competitors, shipping, chokepoints)
    ("OilPrice.com", "https://oilprice.com/rss/main", "Industry & Markets"),
    # Macro & Demand
    ("Fed Monetary Policy", "https://federalreserve.gov/feeds/press_monetary.xml", "Macro & Demand"),
]

# Keyword tags for geopolitical risk radar. (pattern, tag_name, risk_weight: high=2, medium=1, low=0.5)
TAG_PATTERNS = [
    (r"\bsanctions?\b", "Sanctions", 2),
    (r"production\s+cut", "Production cut", 2),
    (r"pipeline\s+attack", "Pipeline attack", 2),
    (r"\bstrikes?\b", "Strikes", 1),
    (r"shipping\s+disruption", "Shipping disruption", 2),
    (r"\bchokepoint\b", "Chokepoint", 1),
    (r"\bhormuz\b", "Hormuz", 2),
    (r"\bsuez\b", "Suez", 1),
    (r"\bmalacca\b", "Malacca", 1),
    (r"canal\s+closure", "Canal closure", 2),
    (r"\bhurricane\b", "Hurricane", 1),
    (r"\bstorm\b", "Storm", 0.5),
    (r"\bflood\b", "Flood", 0.5),
    (r"\brig\b", "Rig", 0.5),
    (r"force\s+majeure", "Force majeure", 2),
    (r"refinery\s+shut", "Refinery shutdown", 1),
    (r"tanker\b", "Tanker", 0.5),
]

_cache: tuple[list[dict], float] = ([], 0.0)
CACHE_SEC = 1800  # 30 min


def _extract_tags(title: str, description: str) -> list[dict]:
    """Extract tags from title and description. Returns list of {tag, weight}."""
    text = (title or "") + " " + (description or "")
    text = text.lower()
    seen = set()
    out = []
    for pattern, tag_name, weight in TAG_PATTERNS:
        if re.search(pattern, text, re.I) and tag_name not in seen:
            seen.add(tag_name)
            out.append({"tag": tag_name, "weight": weight})
    return out


def _parse_entry(entry: Any, source: str, category: str) -> dict:
    title = getattr(entry, "title", "") or ""
    link = getattr(entry, "link", "") or ""
    published = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""
    description = getattr(getattr(entry, "description", None) or getattr(entry, "summary", None), "value", "") or ""
    if not description and hasattr(entry, "description"):
        description = str(entry.description) if entry.description else ""
    if not description and hasattr(entry, "summary"):
        description = str(entry.summary) if entry.summary else ""

    tags = _extract_tags(title, description)
    tag_names = [t["tag"] for t in tags]
    sentiment = get_sentiment(title, description, tag_names)

    return {
        "title": title,
        "link": link,
        "published": published,
        "source": source,
        "category": category,
        "tags": tag_names,
        "sentiment": sentiment,
        "_tag_weights": tags,
    }


def _source_to_category(source: str) -> str:
    for _name, _url, cat in FEEDS:
        if _name == source:
            return cat
    return "General"


# Country code (e.g. USA, GBR) -> search terms for filtering news by region
COUNTRY_NEWS_TERMS: dict[str, list[str]] = {
    "USA": ["USA", "United States", "U.S.", "America", "American", "US "],
    "CAN": ["Canada", "Canadian"],
    "GBR": ["UK", "Britain", "British", "United Kingdom"],
    "DEU": ["Germany", "German"],
    "FRA": ["France", "French"],
    "IND": ["India", "Indian"],
    "CHN": ["China", "Chinese"],
    "JPN": ["Japan", "Japanese"],
    "RUS": ["Russia", "Russian"],
    "SAU": ["Saudi", "Saudi Arabia", "OPEC"],
    "ARE": ["UAE", "Dubai", "Emirates"],
    "BRA": ["Brazil", "Brazilian"],
    "AUS": ["Australia", "Australian"],
    "MEX": ["Mexico", "Mexican"],
    "IRQ": ["Iraq", "Iraqi"],
    "IRN": ["Iran", "Iranian"],
    "NGA": ["Nigeria", "Nigerian"],
    "ZAF": ["South Africa", "African"],
    "KOR": ["South Korea", "Korea", "Korean"],
}


def _item_matches_country(item: dict, country_code: str) -> bool:
    """True if item title/source/summary mentions the country."""
    terms = COUNTRY_NEWS_TERMS.get((country_code or "").upper(), [country_code] if country_code else [])
    if not terms:
        return True
    text = " ".join([
        str(item.get("title") or ""),
        str(item.get("source") or ""),
        str(item.get("category") or ""),
    ]).lower()
    return any(t.lower() in text for t in terms)


def _fetch_all(max_items: int = 80) -> list[dict]:
    items = []
    if not feedparser:
        return items
    per_feed = max(5, max_items // len(FEEDS))
    for name, url, category in FEEDS:
        try:
            d = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0 (compatible; MarketInt/1.0)"})
            for e in d.entries[:per_feed]:
                items.append(_parse_entry(e, name, category))
        except Exception:
            continue
    # Sort by published if parseable; keep order otherwise
    items = items[:max_items * 2]
    return items


def get_news_items(
    max_items: int = 50,
    use_cache: bool = True,
    strip_internal: bool = True,
    country_code: str | None = None,
) -> list[dict]:
    """Return list of {title, link, published, source, category, tags}. Cached 30 min. Optional country_code filters by region."""
    global _cache
    now = time.time()
    if use_cache and _cache[1] > now:
        data = _cache[0][: max_items * 2]
    else:
        data = _fetch_all(max_items=max_items * 2)
        _cache = (data, now + CACHE_SEC)
    if country_code:
        data = [i for i in data if _item_matches_country(i, country_code)]
    data = data[:max_items]
    if strip_internal:
        return [{k: v for k, v in item.items() if k != "_tag_weights"} for item in data]
    return data


def get_news_by_categories(
    max_items: int = 80,
    country_code: str | None = None,
) -> dict[str, list[dict]]:
    """Return { category: [items] } for frontend panels. Optional country_code filters by region."""
    items = get_news_items(max_items=max_items, use_cache=True, country_code=country_code)
    out: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("category") or "General"
        if cat not in out:
            out[cat] = []
        clean = {k: v for k, v in item.items() if k != "_tag_weights"}
        out[cat].append(clean)
    return out
