"""
Oil supply risk score from tagged news. No paid APIs.
"""
from __future__ import annotations

from data.rss_feeds import get_news_items


def compute_risk_score(items: list[dict]) -> tuple[float, list[str]]:
    """
    Compute Oil Supply Risk Score (0-10) from news items with _tag_weights.
    Returns (score, top_tags).
    """
    total = 0.0
    tag_counts: dict[str, float] = {}
    for item in items:
        weights = item.get("_tag_weights", [])
        for t in weights:
            tag = t.get("tag", "")
            w = float(t.get("weight", 0))
            total += w
            tag_counts[tag] = tag_counts.get(tag, 0) + w

    # Cap at 10
    score = min(10.0, total)

    # Top tags by weighted count
    top = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
    top_tags = [t[0] for t in top]

    return (round(score, 1), top_tags)


def get_risk_summary() -> dict:
    """
    Return { score, summary, tags } for /api/risk-summary.
    """
    items = get_news_items(max_items=50, use_cache=True, strip_internal=False)
    # get_news_items strips _tag_weights in get_news_by_categories but not in get_news_items
    # We need the raw items with _tag_weights - get_news_items returns from _fetch_all
    # which includes _tag_weights. So we're good.
    score, top_tags = compute_risk_score(items)

    # Build 3-line summary
    if top_tags:
        themes = ", ".join(top_tags[:5])
        summary = f"Key themes: {themes}. Oil supply risk: {score}/10."
    else:
        summary = f"Oil supply risk: {score}/10. No high-signal tags in recent headlines."

    return {
        "score": score,
        "summary": summary,
        "tags": top_tags,
    }
