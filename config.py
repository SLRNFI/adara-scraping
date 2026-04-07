"""Configuration for Adara Ventures scraping pipeline."""

import os

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
if not APIFY_TOKEN:
    raise ValueError("Set APIFY_API_TOKEN environment variable. See .env.example")

TARGET = "Adara Ventures"

# Google search queries — broad coverage of branding, sentiment, portfolio, press
GOOGLE_QUERIES = [
    '"Adara Ventures"',
    '"Adara Ventures" review OR opinion OR reputation',
    '"Adara Ventures" portfolio OR investment OR fund',
    '"Adara Ventures" funding OR raise OR close',
    '"Adara Ventures" partner OR team OR founder',
    'site:linkedin.com "Adara Ventures"',
    'site:twitter.com OR site:x.com "Adara Ventures"',
    'site:crunchbase.com "Adara Ventures"',
    '"Adara Ventures" Europe OR Spain OR deep tech',
]

# Max pages per Google query (each page = 10 results)
GOOGLE_MAX_PAGES = 3

# Twitter search queries
TWITTER_QUERIES = [
    "Adara Ventures",
    "@AdaraVentures",
    "AdaraVentures",
]

TWITTER_MAX_TWEETS = 200

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
