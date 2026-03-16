"""Price API routes."""
from flask import Blueprint, jsonify, request

from data.price_scraper import (
    DEFAULT_TICKERS,
    get_all_historical,
    get_latest_prices,
)

bp = Blueprint("prices", __name__, url_prefix="/api")


@bp.route("/prices/latest")
def latest():
    try:
        use_cache = request.args.get("cache", "true").lower() != "false"
        data = get_latest_prices(DEFAULT_TICKERS, use_cache=use_cache)
        out = {}
        for name, q in data.items():
            out[name] = {
                "price": q.get("price"),
                "change": q.get("change"),
                "change_pct": q.get("change_pct"),
            }
        brent = (data.get("Brent Crude Oil") or {}).get("price")
        wti = (data.get("WTI Crude Oil") or {}).get("price")
        if brent is not None and wti is not None:
            out["Brent-WTI Spread"] = {"price": round(brent - wti, 2), "change": None, "change_pct": None}
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/prices/history")
def history():
    tickers_param = request.args.get("tickers", ",".join(DEFAULT_TICKERS))
    days = int(request.args.get("days", 90))
    tickers = [t.strip() for t in tickers_param.split(",") if t.strip()]
    if not tickers:
        tickers = DEFAULT_TICKERS
    try:
        data = get_all_historical(tickers, days=days)
        out = {}
        for name, df in data.items():
            if df is None or df.empty:
                out[name] = []
                continue
            recs = df.reset_index().rename(columns={"Date": "date"}).to_dict(orient="records")
            for r in recs:
                if hasattr(r.get("date"), "isoformat"):
                    r["date"] = r["date"].isoformat()[:10]
            out[name] = recs
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
