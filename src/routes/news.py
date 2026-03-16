"""News API routes."""
from flask import Blueprint, jsonify, request

from data.rss_feeds import get_news_items, get_news_by_categories

bp = Blueprint("news", __name__, url_prefix="/api")


@bp.route("/news")
def news():
    limit = int(request.args.get("limit", 50))
    by_category = request.args.get("categories", "").lower() in ("1", "true", "yes")
    country = request.args.get("country", "").strip() or None
    try:
        if by_category:
            data = get_news_by_categories(max_items=limit, country_code=country)
            return jsonify({"categories": data})
        items = get_news_items(max_items=limit, country_code=country)
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e), "items": [], "categories": {}}), 500
