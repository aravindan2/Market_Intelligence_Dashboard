"""Map API routes (country-level price index)."""
from flask import Blueprint, jsonify

from data.price_scraper import get_latest_prices, DEFAULT_TICKERS

bp = Blueprint("map", __name__, url_prefix="/api")


@bp.route("/map/prices")
def prices():
    """Country-level price index for global map (derived from latest prices)."""
    try:
        latest = get_latest_prices(DEFAULT_TICKERS)
        wti = (latest.get("WTI Crude Oil") or {}).get("price") or 75.0
        brent = (latest.get("Brent Crude Oil") or {}).get("price") or 78.0
        countries = {
            "USA": wti, "CAN": wti, "MEX": wti * 1.01,
            "GBR": brent, "DEU": brent, "FRA": brent, "ITA": brent, "ESP": brent,
            "RUS": wti * 0.98, "CHN": wti * 1.01, "IND": wti * 1.02, "JPN": brent * 1.01, "KOR": wti * 1.01,
            "SAU": wti * 0.99, "ARE": wti * 1.01, "IRQ": wti * 0.98, "IRN": wti * 0.97,
            "BRA": wti * 0.99, "ZAF": brent * 0.99, "AUS": brent * 1.01, "NGA": wti * 0.98,
        }
        return jsonify({"countries": countries})
    except Exception as e:
        return jsonify({"error": str(e), "countries": {}}), 500
