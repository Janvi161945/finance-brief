"""Three-layer dedup: exact URL/title, fuzzy title similarity, cross-run history."""

import os
import re
import json
import hashlib
import logging
from difflib import SequenceMatcher

from . import config
from .fetch import Article

log = logging.getLogger("dedupe")

_STOPWORDS = {"the", "a", "an", "of", "in", "on", "to", "for", "and", "as",
              "at", "by", "is", "are", "with", "after", "amid", "over"}


def _normalize(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9 ]", " ", title)
    words = [w for w in title.split() if w not in _STOPWORDS]
    return " ".join(words)


def _hash(title: str) -> str:
    return hashlib.sha1(_normalize(title).encode()).hexdigest()


def _load_seen() -> dict:
    try:
        with open(config.SEEN_DB) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_seen(seen: dict):
    os.makedirs(os.path.dirname(config.SEEN_DB), exist_ok=True)
    # keep only ~2000 most recent entries so the file doesn't grow forever
    items = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)[:2000]
    with open(config.SEEN_DB, "w") as f:
        json.dump(dict(items), f)


def deduplicate(articles: list[Article], skip_history: bool = False) -> list[Article]:
    """Return unique, previously-unseen articles (newest version kept)."""
    seen_db = {} if skip_history else _load_seen()
    now_ts = max((a.published.timestamp() for a in articles), default=0)

    # newest first so the freshest duplicate survives
    articles = sorted(articles, key=lambda a: a.published, reverse=True)

    unique: list[Article] = []
    seen_links: set[str] = set()
    seen_hashes: set[str] = set()
    norm_titles: list[str] = []

    dropped = 0
    for art in articles:
        h = _hash(art.title)
        if art.link in seen_links or h in seen_hashes or h in seen_db:
            dropped += 1
            continue

        # fuzzy match against already-accepted titles
        norm = _normalize(art.title)
        if any(
            SequenceMatcher(None, norm, prev).ratio() >= config.FUZZY_DEDUP_THRESHOLD
            for prev in norm_titles
        ):
            dropped += 1
            continue

        unique.append(art)
        seen_links.add(art.link)
        seen_hashes.add(h)
        norm_titles.append(norm)
        seen_db[h] = now_ts

    if not skip_history:
        _save_seen(seen_db)
    log.info("Dedup: kept %d, dropped %d", len(unique), dropped)
    return unique
