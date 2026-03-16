"""Misc API routes: oil stocks, india supply chain."""
from flask import Blueprint, jsonify

from data.price_scraper import get_quotes_by_ticker
from data.india_supply_chain import get_india_supply_chain_data

bp = Blueprint("misc", __name__, url_prefix="/api")

OIL_STOCK_TICKERS = ["XOM", "CVX", "SHEL", "BP", "TTE", "OXY", "EOG", "SLB"]
OIL_STOCK_LABELS = {
    "XOM": "Exxon", "CVX": "Chevron", "SHEL": "Shell", "BP": "BP",
    "TTE": "TotalEnergies", "OXY": "Oxy", "EOG": "EOG", "SLB": "SLB",
}


@bp.route("/oil-stocks")
def oil_stocks():
    try:
        data = get_quotes_by_ticker(OIL_STOCK_TICKERS)
        out = {}
        for ticker, q in data.items():
            out[ticker] = {
                "label": OIL_STOCK_LABELS.get(ticker, ticker),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
            }
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/india-supply-chain")
def india_supply_chain():
    try:
        data = get_india_supply_chain_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
