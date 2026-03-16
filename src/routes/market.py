"""Market signals, forecast, RL, opportunities, scenario, decisions API routes."""
from flask import Blueprint, jsonify, request

from data.price_scraper import DEFAULT_TICKERS, get_latest_prices, get_all_historical
from data.india_supply_chain import get_india_supply_chain_data
from data.decision_framework import evaluate_decisions
from data.risk_sentiment import get_risk_summary
from data.market_signals import (
    get_market_signals,
    get_price_forecast,
    get_rl_signals,
    get_opportunities,
)

bp = Blueprint("market", __name__, url_prefix="/api")

SCENARIO_TIMESPAN_DAYS = {"1d": 1, "3d": 3, "7d": 7, "1m": 30}
SCENARIO_COMMODITIES = ["WTI Crude Oil", "Brent Crude Oil", "Natural Gas", "Gold"]


@bp.route("/market-signals")
def market_signals():
    """Momentum, confidence, opportunity, sector shares."""
    try:
        latest = get_latest_prices(DEFAULT_TICKERS)
        history = get_all_historical(DEFAULT_TICKERS, days=90)
        risk = get_risk_summary()
        risk_score = risk.get("score") or 0
        data = get_market_signals(latest, history, risk_score)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "momentum": 52, "confidence": 50, "sectors": {}}), 500


@bp.route("/price-forecast")
def price_forecast():
    """ML forecast (linear trend + next-day) for WTI."""
    try:
        history = get_all_historical(DEFAULT_TICKERS, days=90)
        data = get_price_forecast(history, "WTI Crude Oil")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "forecast": None}), 500


@bp.route("/rl-signals")
def rl_signals():
    """Reinforcement learning style signals (Long WTI, Hedge, Balanced)."""
    try:
        history = get_all_historical(DEFAULT_TICKERS, days=90)
        return jsonify(get_rl_signals(history))
    except Exception as e:
        return jsonify({"error": str(e), "action": "Balanced", "scores": {}}), 500


@bp.route("/opportunities")
def opportunities():
    """Actionable opportunities (theme, priority, impact, next_step, status)."""
    try:
        latest = get_latest_prices(DEFAULT_TICKERS)
        history = get_all_historical(DEFAULT_TICKERS, days=90)
        supply = get_india_supply_chain_data()
        decisions = evaluate_decisions(latest, history, supply)
        risk = get_risk_summary()
        items = get_opportunities(decisions, risk.get("score") or 0)
        return jsonify({"opportunities": items})
    except Exception as e:
        return jsonify({"error": str(e), "opportunities": []}), 500


@bp.route("/scenario")
def scenario():
    """Scenario explorer: timespan, commodity, risk_band -> summary, price, forecast, decisions_snippet."""
    timespan = request.args.get("timespan", "7d")
    commodity = request.args.get("commodity", "WTI Crude Oil")
    risk_band = request.args.get("risk_band", "medium")
    days = SCENARIO_TIMESPAN_DAYS.get(timespan, 7)
    if commodity not in SCENARIO_COMMODITIES:
        commodity = "WTI Crude Oil"
    try:
        latest = get_latest_prices(DEFAULT_TICKERS)
        history = get_all_historical(DEFAULT_TICKERS, days=min(days, 90))
        supply = get_india_supply_chain_data()
        risk = get_risk_summary()
        risk_score = risk.get("score") or 0
        decisions = evaluate_decisions(latest, history, supply)
        forecast_data = get_price_forecast(history, commodity)
        price_info = latest.get(commodity) or {}
        price_val = price_info.get("price")
        forecast_val = forecast_data.get("forecast")
        decisions_snippet = [
            {"condition": d.get("condition"), "message": d.get("message"), "severity": d.get("severity")}
            for d in (decisions or [])[:3]
        ]
        summary_parts = [
            "Given " + timespan + " window, " + commodity + ", risk band " + risk_band + ".",
            "Current price: " + ("$" + str(round(price_val, 2)) if price_val is not None else "N/A") + ".",
        ]
        if forecast_val is not None:
            summary_parts.append("Next-day forecast: $" + str(forecast_val) + ".")
        summary_parts.append("Oil supply risk score: " + str(risk_score) + "/10.")
        return jsonify({
            "summary": " ".join(summary_parts),
            "price": price_val,
            "forecast": forecast_val,
            "decisions_snippet": decisions_snippet,
            "risk_score": risk_score,
        })
    except Exception as e:
        return jsonify({"error": str(e), "summary": "", "price": None, "forecast": None, "decisions_snippet": []}), 500


@bp.route("/decisions")
def decisions():
    try:
        latest = get_latest_prices(DEFAULT_TICKERS)
        history = get_all_historical(DEFAULT_TICKERS, days=90)
        supply_chain = get_india_supply_chain_data()
        decisions_list = evaluate_decisions(latest, history, supply_chain)
        return jsonify({"decisions": decisions_list})
    except Exception as e:
        return jsonify({"error": str(e), "decisions": []}), 500
