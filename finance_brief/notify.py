"""Deliver the brief: Telegram bot and/or local Markdown file."""

import os
import logging
from datetime import datetime

import requests

from . import config

log = logging.getLogger("notify")


def send_telegram(messages: list[str]) -> bool:
    """Send via Telegram bot. Needs TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID.

    Setup (one time):
      1. Message @BotFather on Telegram -> /newbot -> copy the token
      2. Message your new bot anything, then open:
         https://api.telegram.org/bot<TOKEN>/getUpdates
         and copy your chat id from the response.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.info("Telegram not configured (set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok = True
    for msg in messages:
        try:
            r = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=config.REQUEST_TIMEOUT,
            )
            r.raise_for_status()
        except Exception as e:
            log.error("Telegram send failed: %s", e)
            ok = False
    if ok:
        log.info("Sent %d Telegram message(s)", len(messages))
    return ok


def save_markdown(markdown: str) -> str:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    path = os.path.join(
        config.DATA_DIR, f"brief_{datetime.now().strftime('%Y-%m-%d')}.md"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    log.info("Saved brief to %s", path)
    return path
