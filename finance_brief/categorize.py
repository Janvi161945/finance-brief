"""Categorize articles.

Two modes:
  1. Keyword rules (default, zero cost, works offline)
  2. LLM batch categorization via Anthropic API (set ANTHROPIC_API_KEY)
"""

import os
import json
import logging

from . import config
from .fetch import Article

log = logging.getLogger("categorize")

CATEGORIES = list(config.CATEGORY_KEYWORDS.keys()) + [config.DEFAULT_CATEGORY]


def _keyword_category(article: Article) -> str:
    text = f"{article.title} {article.summary}".lower()
    for category, keywords in config.CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return config.DEFAULT_CATEGORY


def _llm_categorize(articles: list[Article]) -> bool:
    """Batch-categorize via Claude. Returns True on success."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not articles:
        return False
    try:
        import anthropic
    except ImportError:
        log.warning("anthropic package not installed; falling back to keywords. "
                    "Run: pip install anthropic")
        return False

    client = anthropic.Anthropic(api_key=api_key)
    numbered = "\n".join(f"{i}. {a.title}" for i, a in enumerate(articles))
    prompt = (
        "Categorize each finance headline into exactly one of these categories:\n"
        f"{json.dumps(CATEGORIES)}\n\n"
        f"Headlines:\n{numbered}\n\n"
        'Respond ONLY with a JSON object mapping index to category, e.g. '
        '{"0": "Markets", "1": "IPO"}. No other text.'
    )
    try:
        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```")
        mapping = json.loads(raw)
        for i, art in enumerate(articles):
            cat = mapping.get(str(i), config.DEFAULT_CATEGORY)
            art.category = cat if cat in CATEGORIES else config.DEFAULT_CATEGORY
        log.info("LLM categorized %d articles", len(articles))
        return True
    except Exception as e:
        log.warning("LLM categorization failed (%s); using keywords", e)
        return False


def categorize(articles: list[Article]) -> list[Article]:
    if not _llm_categorize(articles):
        for art in articles:
            art.category = _keyword_category(art)
    return articles
