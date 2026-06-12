"""Fetch articles from RSS feeds and (optionally) the Marketaux API."""

import os
import time
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

import requests
import feedparser

from . import config

log = logging.getLogger("fetch")


@dataclass
class Article:
    title: str
    link: str
    source: str
    published: datetime
    summary: str = ""
    category: str = ""
    sentiment: float | None = None  # only from Marketaux

    def to_dict(self):
        return {
            "title": self.title,
            "link": self.link,
            "source": self.source,
            "published": self.published.isoformat(),
            "summary": self.summary,
            "category": self.category,
            "sentiment": self.sentiment,
        }


def _parse_date(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _clean(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text or "")          # strip HTML
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss() -> list[Article]:
    """Fetch all configured RSS feeds. A failing feed never kills the run."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.MAX_AGE_HOURS)
    articles: list[Article] = []

    for name, url in config.RSS_FEEDS.items():
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            log.warning("Feed failed [%s]: %s", name, e)
            continue

        count = 0
        for entry in feed.entries:
            title = _clean(getattr(entry, "title", ""))
            link = getattr(entry, "link", "")
            if not title or not link:
                continue
            published = _parse_date(entry)
            if published < cutoff:
                continue
            articles.append(
                Article(
                    title=title,
                    link=link,
                    source=name,
                    published=published,
                    summary=_clean(getattr(entry, "summary", ""))[:500],
                )
            )
            count += 1
        log.info("Fetched %d fresh articles from %s", count, name)

    return articles


def fetch_marketaux() -> list[Article]:
    """Optional: pull from Marketaux (needs MARKETAUX_API_KEY)."""
    api_key = os.getenv("MARKETAUX_API_KEY")
    if not api_key:
        return []
    try:
        params = dict(config.MARKETAUX_PARAMS)
        params["api_token"] = api_key
        params["published_after"] = (
            datetime.now(timezone.utc) - timedelta(hours=config.MAX_AGE_HOURS)
        ).strftime("%Y-%m-%dT%H:%M")
        resp = requests.get(config.MARKETAUX_URL, params=params,
                            timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.warning("Marketaux failed: %s", e)
        return []

    out = []
    for item in data.get("data", []):
        sentiments = [
            e.get("sentiment_score")
            for e in item.get("entities", [])
            if e.get("sentiment_score") is not None
        ]
        out.append(
            Article(
                title=_clean(item.get("title", "")),
                link=item.get("url", ""),
                source=item.get("source", "Marketaux"),
                published=datetime.fromisoformat(
                    item["published_at"].replace("Z", "+00:00")
                ),
                summary=_clean(item.get("description", ""))[:500],
                sentiment=sum(sentiments) / len(sentiments) if sentiments else None,
            )
        )
    log.info("Fetched %d articles from Marketaux", len(out))
    return out


def fetch_all() -> list[Article]:
    return fetch_rss() + fetch_marketaux()
