# ☀️ Morning Finance Brief

A personal finance-news agent. Every morning it:

1. **Fetches** ~11 RSS feeds (Reuters, Moneycontrol, Economic Times, Yahoo Finance, CNBC, LiveMint, Finshots) + optionally the **Marketaux API** (with sentiment)
2. **Deduplicates** — exact URL/title match, fuzzy title similarity (catches the same story reworded across outlets), and cross-run history so you never see yesterday's news again
3. **Categorizes** into Markets / IPO / Funding & Startups / Crypto / Economy & Policy / Earnings & Companies — keyword rules by default, or AI-powered if you add an `ANTHROPIC_API_KEY`
4. **Builds a brief** — Markdown file + Telegram-ready messages, with an optional AI-written 3-sentence "what matters today" overview
5. **Delivers** to Telegram (or just saves locally)

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in only the keys you want — everything is optional
python -m finance_brief.main --no-telegram
```

Your brief lands in `data/brief_YYYY-MM-DD.md`.

## Flags

| Command | What it does |
|---|---|
| `python -m finance_brief.main` | Full run: fetch → dedupe → categorize → save → Telegram |
| `... --no-telegram` | Skip Telegram, just save the Markdown file |
| `... --fresh` | Ignore cross-run history (re-include articles seen in earlier runs) |

## Telegram setup (2 minutes)

1. Message **@BotFather** on Telegram → `/newbot` → copy the token
2. Send your new bot any message, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and copy the `chat.id`
3. Put both in `.env` as `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## AI mode (optional)

Add `ANTHROPIC_API_KEY` to `.env` and `pip install anthropic`. You get:
- Smarter categorization (one cheap batch call per run with `claude-haiku-4-5`)
- A 3–4 sentence editor's overview at the top of the brief

Without a key, the keyword classifier handles everything for free.

## Schedule it daily

**Linux/Mac (cron, 7:30 AM IST):**
```bash
crontab -e
30 7 * * * cd /path/to/finance-brief && /usr/bin/python3 -m finance_brief.main >> data/cron.log 2>&1
```

**GitHub Actions (free, no server needed)** — `.github/workflows/brief.yml`:
```yaml
name: Morning Brief
on:
  schedule:
    - cron: "0 2 * * *"   # 02:00 UTC = 7:30 AM IST
  workflow_dispatch:
jobs:
  brief:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python -m finance_brief.main
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```
(Note: cross-run dedup history won't persist between Actions runs unless you cache `data/` — or just rely on `MAX_AGE_HOURS=24`.)

## Customizing

Everything lives in `finance_brief/config.py`:
- **Add/remove feeds** in `RSS_FEEDS` (any RSS URL works — NDTV Profit, Business Standard, TechCrunch, etc.)
- **Tune categories** in `CATEGORY_KEYWORDS` (first match wins)
- **`MAX_PER_CATEGORY`**, **`MAX_AGE_HOURS`**, **`FUZZY_DEDUP_THRESHOLD`** for brief size/strictness

## Project structure

```
finance_brief/
├── config.py      # feeds, categories, settings — edit me
├── fetch.py       # RSS + Marketaux fetching
├── dedupe.py      # exact + fuzzy + cross-run dedup
├── categorize.py  # keyword rules / Claude batch categorization
├── summarize.py   # Markdown + Telegram brief builder, AI overview
├── notify.py      # Telegram sender, file saver
└── main.py        # pipeline orchestrator
```

## Notes

- A failing feed never kills the run — it's logged and skipped (RSS URLs do change occasionally; swap them in `config.py` if one dies).
- Some publishers (notably Reuters) have moved/restricted their public RSS feeds over time. If a feed returns nothing, Google News RSS is a reliable substitute, e.g. `https://news.google.com/rss/search?q=site:reuters.com+finance&hl=en-IN&gl=IN&ceid=IN:en`
- This is for personal reading. Respect each site's terms of service and don't republish their content.
