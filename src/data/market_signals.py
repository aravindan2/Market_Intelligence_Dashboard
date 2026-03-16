"""
Market signals: momentum, confidence, sector shares, price forecast, RL signals, opportunities.
Ported from Dash market_intel / int dashboards.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np

# Sector weights for signals (Trading, Refining, Logistics, Storage, Analytics)
SECTOR_WEIGHTS = {"Trading": 28, "Refining": 24, "Logistics": 20, "Storage": 18, "Analytics": 10}

# Actionable opportunities template (theme, priority, impact, next_step, status)
OPPORTUNITIES_TEMPLATE = [
    {"theme": "Asia-Pacific demand pulse", "priority": "High", "impact": "+13%", "next_step": "Line up spot coverage for March cargoes", "status": "Monitoring"},
    {"theme": "Floating storage squeeze", "priority": "Medium", "impact": "+8%", "next_step": "Re-assess WAF & West of Suez carriers", "status": "Action"},
    {"theme": "Supply chain resilience", "priority": "Low", "impact": "+5%", "next_step": "Refresh inland storage contracts", "status": "Watch"},
]


def _history_to_close_series(history: dict[str, Any], name: str = "WTI Crude Oil") -> tuple[list[float], list[str]]:
    """Extract Close series and dates. Accepts DataFrame or list of {date, Close}."""
    data = (history or {}).get(name)
    if data is None:
        return [], []
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            if "Close" not in data.columns or data.empty:
                return [], []
            closes = data["Close"].astype(float).tolist()
            dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10] for d in data.index]
            return closes, dates
    except Exception:
        pass
    if not isinstance(data, list):
        return [], []
    closes, dates = [], []
    for r in data:
        c = r.get("Close")
        d = r.get("date")
        if c is not None:
            try:
                closes.append(float(c))
                dates.append(str(d)[:10] if d else "")
            except (ValueError, TypeError):
                pass
    return closes, dates


def compute_momentum_series(closes: list[float], days: int = 30) -> list[float]:
    """Generate momentum-like series from price (scaled 15-96)."""
    if len(closes) < 2:
        return [52.0] * max(1, days)
    n = min(len(closes), days)
    base = 52.0
    momentum = [base]
    for i in range(1, n):
        ret = (closes[i] - closes[i - 1]) / closes[i - 1] if closes[i - 1] else 0
        momentum.append(min(96, max(15, momentum[-1] + ret * 100 + 0.1)))
    return momentum


def compute_sector_shares(momentum: float) -> dict[str, float]:
    """Return sector share % from momentum (tweaked by seed)."""
    seed = int(datetime.utcnow().strftime("%Y%m%d"))
    rng = np.random.default_rng(seed)
    tweaks = {k: v + rng.normal(0, 2) for k, v in SECTOR_WEIGHTS.items()}
    total = sum(tweaks.values())
    return {k: round(v / total * 100, 1) for k, v in tweaks.items()}


def ml_price_forecast(closes: list[float]) -> tuple[float, float, list[float], float]:
    """Linear regression forecast. Returns (forecast_price, slope, trend_vals, r2)."""
    if not closes or len(closes) < 2:
        return float(closes[-1]) if closes else 0.0, 0.0, list(closes), 0.0
    vals = np.array(closes, dtype=float)
    indices = np.arange(len(vals))
    slope, intercept = np.polyfit(indices, vals, 1)
    trend = slope * indices + intercept
    ss_tot = np.sum((vals - vals.mean()) ** 2)
    ss_res = np.sum((vals - trend) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    forecast = slope * len(vals) + intercept
    return float(forecast), float(slope), trend.tolist(), float(r2)


def rl_strategy(closes: list[float]) -> tuple[str, dict[str, float]]:
    """Simple bandit-style signal from returns. Returns (best_action, {action: score})."""
    if not closes or len(closes) < 3:
        return "Balanced", {"Long WTI": 0.0, "Hedge Storage": 0.0, "Balanced": 0.0}
    vals = np.array(closes, dtype=float)
    returns = np.diff(vals) / vals[:-1]
    returns = returns[~np.isnan(returns)]
    if len(returns) < 5:
        return "Balanced", {"Long WTI": 0.0, "Hedge Storage": 0.0, "Balanced": 0.0}
    actions = ["Long WTI", "Hedge Storage", "Balanced"]

    def reward_long(r: float) -> float:
        return float(r)

    def reward_hedge(r: float) -> float:
        return -abs(r) * 0.35

    def reward_balanced(r: float) -> float:
        return float(r) * 0.5 - abs(r) * 0.25

    rewards = {"Long WTI": reward_long, "Hedge Storage": reward_hedge, "Balanced": reward_balanced}
    q = np.zeros(3)
    alpha, epsilon = 0.15, 0.25
    seed = int(datetime.utcnow().strftime("%Y%m%d"))
    rng = np.random.default_rng(seed)
    for r in returns[-20:]:
        if rng.random() < epsilon:
            idx = rng.integers(3)
        else:
            idx = int(np.argmax(q))
        reward = rewards[actions[idx]](r)
        q[idx] += alpha * (reward - q[idx])
    best_idx = int(np.argmax(q))
    return actions[best_idx], {actions[i]: float(q[i]) for i in range(3)}


def get_market_signals(latest_prices: dict[str, Any], history: dict[str, Any], risk_score: float = 0) -> dict[str, Any]:
    """Compute momentum, confidence, opportunity, sector shares."""
    closes, _ = _history_to_close_series(history, "WTI Crude Oil")
    momentum_series = compute_momentum_series(closes)
    momentum_last = momentum_series[-1] if momentum_series else 52.0
    momentum_delta = momentum_series[-1] - momentum_series[0] if len(momentum_series) >= 2 else 0.0
    opportunity = max(momentum_series) - min(momentum_series) if momentum_series else 0.0
    confidence = min(99, max(25, 48 + (momentum_last - 52) * 0.45))
    sectors = compute_sector_shares(momentum_last)
    return {
        "momentum": round(momentum_last, 1),
        "momentum_delta": round(momentum_delta, 1),
        "confidence": round(confidence, 1),
        "opportunity": round(opportunity, 1),
        "risk": risk_score,
        "sectors": sectors,
    }


def get_price_forecast(history: dict[str, Any], name: str = "WTI Crude Oil") -> dict[str, Any]:
    """Return forecast_price, slope, r2, trend (for overlay)."""
    closes, dates = _history_to_close_series(history, name)
    if not closes:
        return {"forecast": None, "slope": 0, "r2": 0, "trend": []}
    forecast, slope, trend, r2 = ml_price_forecast(closes)
    return {"forecast": round(forecast, 2), "slope": round(slope, 4), "r2": round(r2, 2), "trend": trend, "dates": dates}


def get_rl_signals(history: dict[str, Any]) -> dict[str, Any]:
    """Return RL action and scores."""
    closes, _ = _history_to_close_series(history, "WTI Crude Oil")
    action, scores = rl_strategy(closes)
    return {"action": action, "scores": scores}


def get_opportunities(decisions: list[dict[str, Any]], risk_score: float) -> list[dict[str, Any]]:
    """Merge template opportunities with decisions-derived ones. Format: theme, priority, impact, next_step, status."""
    out = list(OPPORTUNITIES_TEMPLATE)
    for d in (decisions or [])[:3]:
        msg = d.get("message") or ""
        sev = d.get("severity") or "info"
        priority = "High" if sev == "critical" else "Medium" if sev == "warning" else "Low"
        out.append({
            "theme": d.get("condition") or "Market alert",
            "priority": priority,
            "impact": "+3%" if risk_score >= 6 else "Monitor",
            "next_step": msg[:60] + ("…" if len(msg) > 60 else ""),
            "status": "Action" if sev in ("warning", "critical") else "Monitoring",
        })
    return out[:6]
