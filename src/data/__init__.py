# Data layer: scraping, RSS, India supply chain, dynamic pricing hook.
from .price_scraper import get_latest_prices, get_historical_series, get_all_historical
from .india_supply_chain import get_india_supply_chain_data
from .dynamic_pricing import get_dynamic_prices

def get_news_items(*args, **kwargs):
    from .rss_feeds import get_news_items as _fn
    return _fn(*args, **kwargs)

__all__ = [
    "get_latest_prices",
    "get_historical_series",
    "get_all_historical",
    "get_news_items",
    "get_india_supply_chain_data",
    "get_dynamic_prices",
]
