"""
Configuration: RSS feeds, categories, and settings.
Edit this file to add/remove sources or tweak categories.
"""

import os

# ---------------------------------------------------------------------------
# RSS FEEDS  (name -> feed URL)
# ---------------------------------------------------------------------------
RSS_FEEDS = {
    # --- India (Primary Sources) ---
    "Moneycontrol Top News": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Moneycontrol Markets":  "https://www.moneycontrol.com/rss/marketreports.xml",
    "Moneycontrol IPO":      "https://www.moneycontrol.com/rss/iponews.xml",
    "Moneycontrol Mutual Funds": "https://www.moneycontrol.com/rss/mutualfundsnews.xml",
    "ET Markets":            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "ET Economy":            "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "ET Earnings":           "https://economictimes.indiatimes.com/earnings/rssfeeds/1373376045.cms",
    "LiveMint Markets":      "https://www.livemint.com/rss/markets",
    "LiveMint Money":        "https://www.livemint.com/rss/money",
    "Finshots":              "https://finshots.in/rss/",
    "Business Standard":     "https://www.business-standard.com/rss/",
    "BSE India":             "https://www.bseindia.com/rss/news.xml",

    # --- Global (Secondary - Optional) ---
    # Uncomment below if you want some global news alongside Indian news
    # "Reuters Markets":       "https://feeds.reuters.com/news/wealth",
    # "Yahoo Finance":         "https://finance.yahoo.com/news/rssindex",
}

# ---------------------------------------------------------------------------
# OPTIONAL: Marketaux API (financial news + sentiment) -> https://www.marketaux.com
# Set MARKETAUX_API_KEY in your .env to enable.
# ---------------------------------------------------------------------------
MARKETAUX_ENABLED = bool(os.getenv("MARKETAUX_API_KEY"))
MARKETAUX_URL = "https://api.marketaux.com/v1/news/all"
MARKETAUX_PARAMS = {
    "countries": "in",  # India only
    "filter_entities": "true",
    "language": "en",
    "limit": 50,
}

# ---------------------------------------------------------------------------
# CATEGORIES + keyword rules (used as fallback / when no LLM key is set)
# Order matters: first match wins.
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "IPO": [
        "ipo", "initial public offering", "listing day", "grey market premium",
        "gmp", "drhp", "anchor investor", "issue price", "subscribed",
        "lists at", "stock market debut",
    ],
    "Funding & Startups": [
        "funding", "raises", "raised $", "raised rs", "series a", "series b",
        "series c", "seed round", "valuation", "venture capital", "vc firm",
        "startup", "unicorn", "acquihire", "angel invest",
    ],
    "Crypto": [
        "bitcoin", "ethereum", "crypto", "blockchain", "btc", "eth",
        "stablecoin", "web3", "defi", "binance", "coinbase",
    ],
    "Economy & Policy": [
        "rbi", "federal reserve", "fed ", "interest rate", "repo rate",
        "inflation", "cpi", "gdp", "fiscal", "budget", "monetary policy",
        "tariff", "trade deal", "imf", "world bank", "unemployment",
        "current account", "rupee", "forex reserves",
    ],
    "Earnings & Companies": [
        "q1 results", "q2 results", "q3 results", "q4 results", "earnings",
        "net profit", "revenue", "quarterly", "merger", "acquisition",
        "buyback", "dividend", "ceo", "board approves", "stake sale",
    ],
    "Markets": [
        "sensex", "nifty", "stocks", "shares", "equity", "rally", "selloff",
        "bull", "bear", "wall street", "dow jones", "nasdaq", "s&p 500",
        "fii", "dii", "gold price", "crude oil", "bond yield",
    ],
}
DEFAULT_CATEGORY = "Other"

# Category emoji for the brief
CATEGORY_EMOJI = {
    "Markets": "📈",
    "IPO": "🛎️",
    "Funding & Startups": "🚀",
    "Crypto": "🪙",
    "Economy & Policy": "🏛️",
    "Earnings & Companies": "🏢",
    "Other": "📰",
}

# ---------------------------------------------------------------------------
# General settings
# ---------------------------------------------------------------------------
MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", "24"))   # only keep recent news
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "8"))
FUZZY_DEDUP_THRESHOLD = 0.80                            # title similarity 0-1
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
SEEN_DB = os.path.join(DATA_DIR, "seen_articles.json")  # cross-run dedup
REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (FinanceBriefBot/1.0)"
