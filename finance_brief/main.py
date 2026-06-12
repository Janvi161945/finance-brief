"""Morning Finance Brief — main pipeline.

Usage:
    python -m finance_brief.main                # full run (fetch -> brief -> notify)
    python -m finance_brief.main --no-telegram  # just save the markdown file
    python -m finance_brief.main --fresh        # ignore cross-run dedup history
"""

import sys
import logging

# Load .env if python-dotenv is installed (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from . import fetch, dedupe, categorize, summarize, notify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


def run(send_to_telegram: bool = True, fresh: bool = False) -> int:
    log.info("=== Morning Finance Brief ===")

    articles = fetch.fetch_all()
    log.info("Total fetched: %d", len(articles))
    if not articles:
        log.error("No articles fetched. Check your network / feed URLs.")
        return 1

    articles = dedupe.deduplicate(articles, skip_history=fresh)
    if not articles:
        log.info("Nothing new since the last run. Done.")
        return 0

    articles = categorize.categorize(articles)

    markdown = summarize.build_markdown(articles)
    path = notify.save_markdown(markdown)
    print(f"\nBrief saved: {path}\n")

    if send_to_telegram:
        notify.send_telegram(summarize.build_telegram_html(articles))

    return 0


if __name__ == "__main__":
    sys.exit(
        run(
            send_to_telegram="--no-telegram" not in sys.argv,
            fresh="--fresh" in sys.argv,
        )
    )
