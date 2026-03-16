"""
Price scraper: yfinance primary (no API key), Yahoo quote/chart as fallback.
Returns unified structure: latest price + OHLC series.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    import yfinance as yf
except ImportError:
    yf = None

# Ticker -> display name for dashboards
TICKER_TO_NAME = {
    "CL=F": "WTI Crude Oil",
    "BZ=F": "Brent Crude Oil",
    "NG=F": "Natural Gas",
    "GC=F": "Gold",
    "ZL=F": "Soybean Oil",
    "ZO=F": "Oat",
    "DX-Y.NYB": "Dollar Index",
}
NAME_TO_TICKER = {v: k for k, v in TICKER_TO_NAME.items()}

# Commodities we support for quote + history (Yahoo symbols)
DEFAULT_TICKERS = ["CL=F", "BZ=F", "NG=F", "GC=F", "ZL=F"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# In-memory cache: (ticker, cache_type) -> (value, expiry)
_cache: dict[tuple[str, str], tuple[Any, float]] = {}
QUOTE_CACHE_SEC = 300   # 5 min
HISTORY_CACHE_SEC = 900  # 15 min


def _cached(key: tuple[str, str], ttl_sec: float, fn, *args, **kwargs):
    now = time.time()
    if key in _cache:
        val, expiry = _cache[key]
        if now < expiry:
            return val
    val = fn(*args, **kwargs)
    _cache[key] = (val, now + ttl_sec)
    return val


def _fetch_quote_yfinance(ticker: str) -> dict | None:
    """Fetch latest price and change via yfinance (no API key)."""
    if not yf:
        return None
    try:
        t = yf.Ticker(ticker)
        name = TICKER_TO_NAME.get(ticker, ticker)

        # Prefer history (most reliable for futures); try 5d then 1mo
        for period in ("5d", "1mo"):
            hist = t.history(period=period, interval="1d")
            if hist is not None and not hist.empty and "Close" in hist.columns:
                close = hist["Close"].dropna()
                if not close.empty:
                    curr = float(close.iloc[-1])
                    out = {"ticker": ticker, "name": name, "price": curr}
                    if len(close) >= 2:
                        prev = float(close.iloc[-2])
                        out["change"] = curr - prev
                        out["change_pct"] = ((curr - prev) / prev * 100) if prev else None
                    return out

        # Fallback: info dict (keys vary by ticker type)
        info = t.info
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or info.get("open")
            or info.get("regularMarketOpen")
        )
        if price is not None:
            try:
                return {"ticker": ticker, "name": name, "price": float(price)}
            except (TypeError, ValueError):
                pass

        # fast_info sometimes has current_price when info is slow/empty
        try:
            if hasattr(t, "fast_info") and t.fast_info is not None:
                cp = getattr(t.fast_info, "last_price", None) or getattr(
                    t.fast_info, "regular_market_price", None
                )
                if cp is not None:
                    return {"ticker": ticker, "name": name, "price": float(cp)}
        except Exception:
            pass
    except Exception:
        pass
    return None


def _fetch_history_yfinance(ticker: str, days: int = 90) -> pd.DataFrame | None:
    """Fetch OHLC history via yfinance (no API key)."""
    if not yf:
        return None
    try:
        df = yf.download(
            ticker,
            period="max",
            interval="1d",
            progress=False,
            threads=False,
            timeout=15,
        )
        if df is None or df.empty:
            return None
        if hasattr(df.columns, "levels") and df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)
        needed = ["Open", "High", "Low", "Close"]
        if "Volume" in df.columns:
            needed = ["Open", "High", "Low", "Close", "Volume"]
        df = df[[c for c in needed if c in df.columns]].copy()
        if "Close" not in df.columns:
            return None
        df = df.dropna(subset=["Close"]).tail(days)
        if "Volume" not in df.columns:
            df["Volume"] = 0
        df.index.name = "Date"
        return df
    except Exception:
        return None


def _fetch_quote_yahoo(ticker: str) -> dict | None:
    """Scrape Yahoo Finance quote page for current price and change."""
    url = f"https://finance.yahoo.com/quote/{ticker}"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        out = {"ticker": ticker, "name": TICKER_TO_NAME.get(ticker, ticker)}

        # Yahoo quote page: main price in data-symbol section, or fin-streamer with data-field
        # e.g. <fin-streamer data-field="regularMarketPrice" data-symbol="CL=F" value="75.32">
        for tag in soup.find_all("fin-streamer", {"data-field": "regularMarketPrice"}):
            if tag.get("data-symbol") == ticker or not tag.get("data-symbol"):
                try:
                    out["price"] = float(tag.get("value") or tag.text.replace(",", ""))
                except (ValueError, TypeError):
                    pass
                break
        if "price" not in out:
            # Fallback: look for span with class Fw(b) and price-like text
            for span in soup.find_all("span", class_=lambda c: c and "Fw(b)" in str(c)):
                t = span.get_text(strip=True).replace(",", "")
                if t and t[0].isdigit() and "." in t:
                    try:
                        out["price"] = float(t)
                        break
                    except ValueError:
                        continue

        # Previous close / change
        for tag in soup.find_all("fin-streamer", {"data-field": "regularMarketChange"}):
            try:
                raw = tag.get("value") or tag.text.replace(",", "").replace("+", "")
                out["change"] = float(raw)
            except (ValueError, TypeError):
                pass
            break
        for tag in soup.find_all("fin-streamer", {"data-field": "regularMarketChangePercent"}):
            try:
                raw = tag.get("value") or tag.text.replace(",", "").replace("+", "").replace("%", "")
                out["change_pct"] = float(raw)
            except (ValueError, TypeError):
                pass
            break

        if "price" in out:
            return out
    except Exception:
        pass
    return None


def _fetch_history_yahoo(ticker: str, days: int = 90) -> pd.DataFrame | None:
    """Fetch historical OHLC via Yahoo chart endpoint (no API key)."""
    # Chart API returns JSON; same idea as yfinance, no key required with browser UA
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=days)).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={start}&period2={end}&interval=1d&events=history"
    )
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        r.raise_for_status()
        j = r.json()
        if "chart" not in j or "result" not in j["chart"] or not j["chart"]["result"]:
            return None
        res = j["chart"]["result"][0]
        ts = res.get("timestamp") or []
        quotes = res.get("indicators", {}).get("quote", [{}])[0]
        o = quotes.get("open") or [None] * len(ts)
        h = quotes.get("high") or [None] * len(ts)
        l = quotes.get("low") or [None] * len(ts)
        c = quotes.get("close") or [None] * len(ts)
        v = quotes.get("volume") or [0] * len(ts)
        df = pd.DataFrame({
            "Date": pd.to_datetime(ts, unit="s"),
            "Open": o, "High": h, "Low": l, "Close": c, "Volume": v,
        })
        df = df.dropna(subset=["Close"]).set_index("Date").sort_index()
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception:
        return None


def _fetch_quote(ticker: str) -> dict | None:
    """Try yfinance first, then Yahoo quote scrape."""
    q = _fetch_quote_yfinance(ticker) if yf else None
    if not q or q.get("price") is None:
        q = _fetch_quote_yahoo(ticker)
    return q


def get_latest_prices(tickers: list[str] | None = None, use_cache: bool = True) -> dict[str, dict]:
    """Return latest quote per ticker. Keys are display names. yfinance primary, Yahoo fallback."""
    tickers = tickers or DEFAULT_TICKERS
    out = {}
    for t in tickers:
        key = (t, "quote")
        if use_cache:
            q = _cached(key, QUOTE_CACHE_SEC, _fetch_quote, t)
        else:
            q = _fetch_quote(t)
        if q:
            name = q.get("name") or TICKER_TO_NAME.get(t, t)
            out[name] = q
    return out


def get_quotes_by_ticker(
    tickers: list[str], use_cache: bool = True
) -> dict[str, dict[str, Any]]:
    """Return latest quote per ticker keyed by ticker. Each value has price, change_pct, name."""
    out: dict[str, dict[str, Any]] = {}
    for t in tickers:
        key = (t, "quote")
        if use_cache:
            q = _cached(key, QUOTE_CACHE_SEC, _fetch_quote, t)
        else:
            q = _fetch_quote(t)
        if q:
            out[t] = {
                "price": q.get("price"),
                "change": q.get("change"),
                "change_pct": q.get("change_pct"),
                "name": q.get("name") or TICKER_TO_NAME.get(t, t),
            }
    return out


def _fetch_history(ticker: str, days: int) -> pd.DataFrame | None:
    """Try yfinance first, then Yahoo chart API."""
    df = _fetch_history_yfinance(ticker, days) if yf else None
    if df is None or df.empty:
        df = _fetch_history_yahoo(ticker, days)
    return df


def get_historical_series(
    ticker: str, days: int = 90, use_cache: bool = True
) -> pd.DataFrame | None:
    """Return OHLC DataFrame for one ticker. yfinance primary, Yahoo fallback."""
    key = (ticker, f"hist_{days}")
    if use_cache:
        return _cached(key, HISTORY_CACHE_SEC, _fetch_history, ticker, days)
    return _fetch_history(ticker, days)


def get_all_historical(tickers: list[str] | None = None, days: int = 90) -> dict[str, pd.DataFrame]:
    """Return OHLC series for each ticker. Keys are display names."""
    tickers = tickers or DEFAULT_TICKERS
    out = {}
    for t in tickers:
        df = get_historical_series(t, days=days)
        if df is not None and not df.empty:
            name = TICKER_TO_NAME.get(t, t)
            out[name] = df
    return out
