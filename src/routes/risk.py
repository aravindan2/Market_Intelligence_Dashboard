"""Risk summary API routes."""
from flask import Blueprint, jsonify

from data.risk_sentiment import get_risk_summary

bp = Blueprint("risk", __name__, url_prefix="/api")


@bp.route("/risk-summary")
def risk_summary():
    try:
        data = get_risk_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "score": 0, "summary": "", "tags": []}), 500
