"""
Lexicon-based sentiment for news (no API key). Returns positive | neutral | negative.
"""
from __future__ import annotations

# Minimal VADER-style word lists (subset for oil/commodity headlines)
POSITIVE = {
    "gain", "gains", "gained", "rise", "rises", "rising", "surge", "surges", "growth",
    "recovery", "recover", "recovered", "boost", "boosts", "strong", "strength",
    "record", "high", "higher", "peak", "soar", "soaring", "jump", "jumps",
    "rally", "rallies", "expand", "expansion", "demand", "optimism", "positive",
    "stability", "stable", "deal", "agreement", "approval", "approve",
}
NEGATIVE = {
    "fall", "falls", "falling", "drop", "drops", "dropped", "decline", "declines",
    "loss", "losses", "cut", "cuts", "cutting", "crash", "crisis", "crises",
    "war", "attack", "attacks", "strike", "strikes", "sanction", "sanctions",
    "disruption", "disrupt", "shut", "shutdown", "failure", "fail", "risk", "risks",
    "volatility", "volatile", "fear", "concern", "concerns", "warning", "warn",
    "recession", "recession", "shortage", "shortages", "inflation", "negative",
    "collapse", "collapsed", "damage", "damaged", "destroy", "destroyed",
}


def get_sentiment(title: str, description: str, tag_names: list[str] | None = None) -> str:
    """
    Return "positive" | "neutral" | "negative" from title + description.
    tag_names (e.g. Sanctions, Pipeline attack) can push toward negative.
    """
    text = ((title or "") + " " + (description or "")).lower()
    tokens = set(w.strip(".,!?;:\"'") for w in text.split() if len(w.strip(".,!?;:\"'")) > 2)
    pos_count = sum(1 for t in tokens if t in POSITIVE)
    neg_count = sum(1 for t in tokens if t in NEGATIVE)
    # Risk tags push negative
    if tag_names:
        risk_tags = {"Sanctions", "Production cut", "Pipeline attack", "Strikes", "Shipping disruption",
                     "Chokepoint", "Hormuz", "Force majeure", "Refinery shutdown"}
        neg_count += sum(1 for tag in tag_names if tag in risk_tags)
    if pos_count > neg_count:
        return "positive"
    if neg_count > pos_count:
        return "negative"
    return "neutral"
