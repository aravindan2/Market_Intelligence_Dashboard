"""
Decision framework: thresholds, alerts, recommendations from prices + supply chain.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

def _load_thresholds() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent.parent / "config" / "thresholds.json"
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "wti_max": 90, "wti_min": 60,
        "brent_max": 95, "brent_min": 62,
        "volatility_pct_max": 5,
        "refining_margin_min": 2,
        "price_above_30d_avg_alert": True,
        "spread_brent_wti_max": 5,
    }


def evaluate_decisions(
    latest_prices: dict[str, Any],
    history: dict[str, Any],
    supply_chain: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """
    Returns list of { type, condition, message, severity }.
    type: "alert" | "recommendation"
    severity: "info" | "warning" | "critical"
    """
    out = []
    th = _load_thresholds()

    wti = latest_prices.get("WTI Crude Oil", {}) or {}
    brent = latest_prices.get("Brent Crude Oil", {}) or {}
    wti_price = wti.get("price")
    brent_price = brent.get("price")

    if wti_price is not None:
        if wti_price >= th.get("wti_max", 90):
            out.append({
                "type": "alert",
                "condition": f"WTI >= ${th['wti_max']}",
                "message": f"WTI at ${wti_price:.2f} is at or above max threshold ${th['wti_max']}.",
                "severity": "warning",
            })
        if wti_price <= th.get("wti_min", 60):
            out.append({
                "type": "alert",
                "condition": f"WTI <= ${th['wti_min']}",
                "message": f"WTI at ${wti_price:.2f} is at or below min threshold ${th['wti_min']}.",
                "severity": "warning",
            })

    if brent_price is not None:
        if brent_price >= th.get("brent_max", 95):
            out.append({
                "type": "alert",
                "condition": f"Brent >= ${th['brent_max']}",
                "message": f"Brent at ${brent_price:.2f} is at or above max threshold.",
                "severity": "warning",
            })
        if brent_price <= th.get("brent_min", 62):
            out.append({
                "type": "alert",
                "condition": f"Brent <= ${th['brent_min']}",
                "message": f"Brent at ${brent_price:.2f} is at or below min threshold.",
                "severity": "warning",
            })

    if wti_price is not None and brent_price is not None:
        spread = brent_price - wti_price
        if spread > th.get("spread_brent_wti_max", 5):
            out.append({
                "type": "recommendation",
                "condition": "Brent–WTI spread",
                "message": f"Brent–WTI spread widened to ${spread:.2f}. Check arbitrage.",
                "severity": "info",
            })

    # History-based: 30d average and volatility
    vol_limit = th.get("volatility_pct_max", 5)
    for name, df in (history or {}).items():
        if df is None or not hasattr(df, "columns") or "Close" not in df.columns or len(df) < 2:
            continue
        close = df["Close"]
        avg30 = float(close.tail(30).mean()) if len(close) >= 30 else float(close.mean())
        latest = float(close.iloc[-1])
        ret = close.pct_change().dropna()
        vol = float(ret.tail(30).std() * 100) if len(ret) >= 30 else 0.0

        if th.get("price_above_30d_avg_alert") and latest > avg30 * 1.02:
            out.append({
                "type": "recommendation",
                "condition": f"{name} vs 30d avg",
                "message": f"{name} above 30-day average – consider hedging.",
                "severity": "info",
            })
        if vol >= vol_limit:
            out.append({
                "type": "alert",
                "condition": f"Volatility >= {vol_limit}%",
                "message": f"{name} 30d volatility at {vol:.1f}% (threshold {vol_limit}%).",
                "severity": "warning",
            })

    # Supply chain
    if supply_chain:
        summary = supply_chain.get("summary") or {}
        stages = supply_chain.get("stages") or []
        margin_min = th.get("refining_margin_min", 2)
        if stages:
            try:
                refining = next(s for s in stages if s.get("id") == "refining")
                ext = next(s for s in stages if s.get("id") == "extraction")
                if refining and ext:
                    ref_idx = refining.get("price_index")
                    ext_idx = ext.get("price_index")
                    if ref_idx is not None and ext_idx is not None:
                        margin = ref_idx - ext_idx
                        if margin < margin_min:
                            out.append({
                                "type": "alert",
                                "condition": "Refining margin",
                                "message": f"Refining margin below threshold ({margin:.1f} < {margin_min}).",
                                "severity": "warning",
                            })
            except (StopIteration, TypeError):
                pass
        monthly = summary.get("monthly_crude_processed_kt")
        if monthly is not None and isinstance(monthly, (int, float)) and monthly < 2000:
            out.append({
                "type": "recommendation",
                "condition": "Crude processed",
                "message": "Monthly crude processed below 2000 kT – monitor supply.",
                "severity": "info",
            })

    return out
