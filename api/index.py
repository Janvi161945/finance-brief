"""Vercel Serverless Function - Finance Brief (Telegram-only, no UI)."""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import finance_brief
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import bot modules
from finance_brief import fetch, dedupe, categorize, summarize, notify


async def handler(request):
    """HTTP handler for Vercel - runs bot and sends to Telegram."""

    try:
        print("[INFO] Starting finance brief...")

        # Step 1: Fetch from 12 Indian feeds
        print("[FETCH] Downloading articles from RSS feeds...")
        articles = fetch.fetch_all()
        print(f"[FETCH] Got {len(articles)} articles")

        if not articles:
            print("[ERROR] No articles fetched")
            return {
                'statusCode': 404,
                'body': 'No articles fetched. Check network/feeds.'
            }

        # Step 2: Remove duplicates
        print("[DEDUPE] Removing duplicates...")
        articles = dedupe.deduplicate(articles, skip_history=False)
        print(f"[DEDUPE] {len(articles)} unique articles after dedup")

        if not articles:
            print("[INFO] Nothing new since last run")
            return {
                'statusCode': 200,
                'body': 'Nothing new since last run.'
            }

        # Step 3: Categorize articles
        print("[CATEGORIZE] Tagging articles (IPO, Markets, Economy, etc.)...")
        articles = categorize.categorize(articles)
        print("[CATEGORIZE] Done")

        # Step 4: Build brief
        print("[SUMMARIZE] Building markdown brief...")
        markdown = summarize.build_markdown(articles)
        print("[SUMMARIZE] Done")

        # Step 5: Save markdown file
        print("[SAVE] Saving brief to file...")
        brief_path = notify.save_markdown(markdown)
        print(f"[SAVE] Saved to: {brief_path}")

        # Step 6: Send to Telegram
        print("[TELEGRAM] Building Telegram messages...")
        telegram_msgs = summarize.build_telegram_html(articles)
        print(f"[TELEGRAM] Sending {len(telegram_msgs)} message(s)...")
        notify.send_telegram(telegram_msgs)
        print("[TELEGRAM] Sent successfully!")

        # Return success JSON
        print("[SUCCESS] Finance brief complete")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': f'Success! Sent {len(articles)} articles to Telegram.'
        }

    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': error_msg
        }
