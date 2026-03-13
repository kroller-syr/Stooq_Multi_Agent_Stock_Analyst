import re
from typing import Any


POS_WORDS = {
    "beat", "beats", "growth", "surge", "record", "strong", "profit", "profits",
    "upgrade", "upgraded", "bullish", "rally", "outperform", "positive", "improve", "improved",
}
NEG_WORDS = {
    "miss", "misses", "decline", "drop", "weak", "loss", "losses", "downgrade", "downgraded",
    "bearish", "slump", "underperform", "negative", "fall", "falls", "lawsuit", "probe",
}


def _tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    return re.findall(r"[a-z']+", text)


def score_articles_sentiment(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Returns:
      - per_article: list with {title, url, score}
      - summary: counts and average
    """
    per_article = []
    scores = []

    for a in articles:
        title = a.get("title") or ""
        snippet = a.get("snippet") or ""
        tokens = _tokenize(title + " " + snippet)

        pos = sum(1 for t in tokens if t in POS_WORDS)
        neg = sum(1 for t in tokens if t in NEG_WORDS)

        score = pos - neg
        scores.append(score)

        per_article.append({
            "title": title,
            "url": a.get("url"),
            "domain": a.get("domain"),
            "seendate": a.get("seendate"),
            "score": score,
            "pos_hits": pos,
            "neg_hits": neg,
        })

    avg = sum(scores) / len(scores) if scores else 0.0
    pos_ct = sum(1 for s in scores if s > 0)
    neg_ct = sum(1 for s in scores if s < 0)
    neu_ct = sum(1 for s in scores if s == 0)

    summary = {
        "n_articles": len(scores),
        "avg_score": avg,
        "positive_articles": pos_ct,
        "negative_articles": neg_ct,
        "neutral_articles": neu_ct,
    }

    return {"summary": summary, "per_article": per_article}