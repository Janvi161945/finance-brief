"""Build the Morning Finance Brief (Markdown + Telegram-HTML formats)."""

import os
import logging
from datetime import datetime
from collections import defaultdict

from . import config
from .fetch import Article

log = logging.getLogger("summarize")


def _group(articles: list[Article]) -> dict[str, list[Article]]:
    groups = defaultdict(list)
    for a in articles:
        groups[a.category].append(a)
    # cap per category, ordered by category importance
    order = list(config.CATEGORY_KEYWORDS.keys()) + [config.DEFAULT_CATEGORY]
    return {
        cat: sorted(groups[cat], key=lambda a: a.published, reverse=True)[: config.MAX_PER_CATEGORY]
        for cat in order
        if groups.get(cat)
    }


def _ai_overview(articles: list[Article]) -> str | None:
    """Optional 3-4 sentence 'what matters today' written by Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not articles:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        headlines = "\n".join(f"- [{a.category}] {a.title}" for a in articles[:40])
        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": (
                    "You are a finance editor. Based on today's headlines below, write a "
                    "crisp 3-4 sentence morning overview of what matters most for an "
                    "Indian retail investor following global + Indian markets. "
                    "Plain text only, no markdown.\n\n" + headlines
                ),
            }],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        log.warning("AI overview failed: %s", e)
        return None


def build_markdown(articles: list[Article]) -> str:
    today = datetime.now().strftime("%A, %d %B %Y")
    lines = [f"# ☀️ Morning Finance Brief — {today}", ""]

    overview = _ai_overview(articles)
    if overview:
        lines += [f"> {overview}", ""]

    for cat, arts in _group(articles).items():
        emoji = config.CATEGORY_EMOJI.get(cat, "📰")
        lines.append(f"## {emoji} {cat}")
        for a in arts:
            sent = ""
            if a.sentiment is not None:
                sent = " 🟢" if a.sentiment > 0.15 else (" 🔴" if a.sentiment < -0.15 else "")
            lines.append(f"- [{a.title}]({a.link}) — *{a.source}*{sent}")
        lines.append("")

    lines.append(f"_{len(articles)} unique stories from {len(config.RSS_FEEDS)} sources._")
    return "\n".join(lines)


def build_telegram_html(articles: list[Article]) -> list[str]:
    """Telegram messages (HTML parse mode), split under the 4096-char limit."""
    import html

    today = datetime.now().strftime("%a, %d %b %Y")
    chunks: list[str] = []
    current = [f"☀️ <b>Morning Finance Brief</b> — {today}\n"]

    overview = _ai_overview(articles)
    if overview:
        current.append(f"<i>{html.escape(overview)}</i>\n")

    def flush():
        if current:
            chunks.append("\n".join(current))

    size = sum(len(c) for c in current)
    for cat, arts in _group(articles).items():
        emoji = config.CATEGORY_EMOJI.get(cat, "📰")
        block = [f"\n{emoji} <b>{html.escape(cat)}</b>"]
        for a in arts:
            block.append(
                f'• <a href="{html.escape(a.link, quote=True)}">'
                f"{html.escape(a.title)}</a> — {html.escape(a.source)}"
            )
        block_text = "\n".join(block)
        if size + len(block_text) > 3800:
            flush()
            current.clear()
            size = 0
        current.append(block_text)
        size += len(block_text)
    flush()
    return chunks
