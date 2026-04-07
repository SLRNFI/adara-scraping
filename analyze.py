"""Sentiment analysis and brand positioning analysis for Adara Ventures."""

import json
import os
import re
from collections import Counter
from textblob import TextBlob
from config import OUTPUT_DIR


# Brand/positioning keyword categories
BRAND_CATEGORIES = {
    "deep_tech": [
        "deep tech", "deeptech", "technology", "innovation", "AI",
        "artificial intelligence", "machine learning", "robotics",
        "quantum", "biotech", "cybersecurity", "semiconductor", "hardware",
        "space tech", "spacetech", "climate tech", "cleantech",
    ],
    "europe_focus": [
        "europe", "european", "spain", "spanish", "EU", "madrid",
        "barcelona", "iberian", "pan-european", "continental",
    ],
    "venture_capital": [
        "venture capital", "VC", "fund", "investment", "portfolio",
        "startup", "seed", "series A", "series B", "growth",
        "early stage", "early-stage", "funding", "raise", "round",
    ],
    "team_leadership": [
        "partner", "founder", "managing", "GP", "general partner",
        "team", "leadership", "board", "advisor", "mentor",
    ],
    "track_record": [
        "exit", "IPO", "acquisition", "return", "track record",
        "success", "unicorn", "portfolio company", "invested",
    ],
    "reputation": [
        "trusted", "reputable", "leading", "top", "best", "recognized",
        "award", "ranking", "prestigious", "influential",
    ],
}

# ---- VC-domain sentiment adjustments ----
# Phrases that TextBlob wrongly scores as negative but are neutral/positive in VC context
POSITIVE_VC_PHRASES = [
    "funding round", "raises", "raised", "series a", "series b", "series c",
    "closes", "closed", "closing", "close a", "backed by", "leads",
    "led by", "co-leads", "investment in", "invests in", "invested in",
    "announces", "announced", "launch", "launched", "accelerate",
    "portfolio", "partners with", "joins", "joined", "selected",
    "surpasses", "valuation", "pre-money", "post-money",
    "exits", "acquisition", "acquired", "IPO",
    "deep tech", "fund", "venture", "capital",
    "honored", "proud", "award", "recognized", "alliance",
    "milestone", "momentum", "growth", "expanding", "strengthen",
]

# Phrases/patterns that are genuinely negative
GENUINELY_NEGATIVE_PHRASES = [
    "lawsuit", "sued", "scandal", "fraud", "bankrupt", "collapse",
    "layoff", "fired", "shut down", "failed", "failure",
    "controversy", "criticized", "criticism", "investigation",
    "loss", "losses", "downturn", "write-off", "write off",
    "disappointing", "underperform",
]

# Boilerplate noise to filter from sentiment scoring
BOILERPLATE_PATTERNS = [
    r"something went wrong",
    r"cookies?\s*(policy|disclaimer|privacy)",
    r"©\s*\d{4}",
    r"GDPR.*privacy.*cookies",
    r"accept\s+cookies",
    r"read\s*more$",
    r"subscribe.*newsletter",
]

# Neutral patterns — legal entities, dry factual references that TextBlob mis-scores
NEUTRAL_OVERRIDE_PATTERNS = [
    r"S\.?C\.?A\.?\s*SICAR",       # Luxembourg fund legal entity type
    r"S\.?C\.?Sp",                   # another Luxembourg entity type
    r"\bSICAV\b",
    r"\bS\.?A\.?\s*$",              # trailing S.A. legal suffix
    r"institution\s*profile",
    r"company\s*profile",
    r"crunchbase.*profile",
    r"pitchbook.*profile",
]


def analyze_sentiment(text):
    """Analyze sentiment with VC-domain awareness.

    Combines TextBlob baseline with domain-specific adjustments
    to avoid misclassifying funding announcements, deal news, etc.
    """
    if not text or not text.strip():
        return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}

    # Strip boilerplate noise before analysis
    clean_text = text
    for pattern in BOILERPLATE_PATTERNS:
        clean_text = re.sub(pattern, "", clean_text, flags=re.IGNORECASE)
    clean_text = clean_text.strip()

    if not clean_text:
        return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}

    # TextBlob baseline
    blob = TextBlob(clean_text)
    base_polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    text_lower = clean_text.lower()

    # Override: legal entity names, profile pages, and other dry factual text
    # that TextBlob wrongly scores as slightly negative
    if base_polarity < 0 and base_polarity >= -0.5:
        for pat in NEUTRAL_OVERRIDE_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return {"polarity": 0.0, "subjectivity": round(subjectivity, 3), "label": "neutral"}

    # Check for genuinely negative content first
    neg_hits = sum(1 for p in GENUINELY_NEGATIVE_PHRASES if p in text_lower)
    if neg_hits >= 2:
        # Multiple negative signals — trust the negative reading
        polarity = min(base_polarity, -0.2)
        label = "negative"
        return {"polarity": round(polarity, 3), "subjectivity": round(subjectivity, 3), "label": label}

    # Count positive VC-domain signals
    pos_vc_hits = sum(1 for p in POSITIVE_VC_PHRASES if p in text_lower)

    # Domain adjustment: if TextBlob says negative but text has VC-positive phrases
    adjusted_polarity = base_polarity
    if base_polarity < 0 and pos_vc_hits >= 1:
        # Boost polarity — funding/deal announcements are positive context
        boost = min(0.15 * pos_vc_hits, 0.5)
        adjusted_polarity = base_polarity + boost

    # If TextBlob is near-neutral but lots of positive VC signals, nudge positive
    if -0.1 <= base_polarity <= 0.1 and pos_vc_hits >= 2:
        adjusted_polarity = max(adjusted_polarity, 0.1 + 0.02 * pos_vc_hits)

    polarity = max(-1.0, min(1.0, adjusted_polarity))

    if polarity > 0.05:
        label = "positive"
    elif polarity < -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {"polarity": round(polarity, 3), "subjectivity": round(subjectivity, 3), "label": label}


def extract_brand_signals(text):
    """Identify brand/positioning keywords in text."""
    if not text:
        return {}
    text_lower = text.lower()
    found = {}
    for category, keywords in BRAND_CATEGORIES.items():
        matches = [kw for kw in keywords if kw.lower() in text_lower]
        if matches:
            found[category] = matches
    return found


def analyze_all_data():
    """Load all scraped data and run sentiment + brand analysis."""
    data_files = {
        "google_search": "google_search_results.json",
        "google_news": "google_news_results.json",
        "twitter": "twitter_results.json",
        "linkedin": "linkedin_results.json",
        "web_content": "web_content_results.json",
    }

    all_analyzed = []
    source_summaries = {}

    for source_name, filename in data_files.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  [Analysis] Skipping {source_name} — file not found")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)

        print(f"  [Analysis] Processing {len(items)} items from {source_name}")

        sentiments = []
        brand_signals = Counter()
        analyzed_items = []

        for item in items:
            # Build the text to analyze based on source
            if source_name in ("twitter", "linkedin"):
                text = item.get("text", "")
            elif source_name == "web_content":
                text = f"{item.get('title', '')} {item.get('meta_description', '')} {item.get('text', '')}"
            else:
                text = f"{item.get('title', '')} {item.get('description', '')}"

            sentiment = analyze_sentiment(text)
            brand = extract_brand_signals(text)

            sentiments.append(sentiment)
            for cat in brand:
                brand_signals[cat] += 1

            analyzed_item = {**item, "sentiment": sentiment, "brand_signals": brand}
            analyzed_items.append(analyzed_item)

        all_analyzed.extend(analyzed_items)

        # Compute source summary
        if sentiments:
            avg_polarity = sum(s["polarity"] for s in sentiments) / len(sentiments)
            avg_subjectivity = sum(s["subjectivity"] for s in sentiments) / len(sentiments)
            label_counts = Counter(s["label"] for s in sentiments)
        else:
            avg_polarity = 0
            avg_subjectivity = 0
            label_counts = {}

        source_summaries[source_name] = {
            "total_items": len(items),
            "avg_polarity": round(avg_polarity, 3),
            "avg_subjectivity": round(avg_subjectivity, 3),
            "sentiment_distribution": dict(label_counts),
            "top_brand_signals": dict(brand_signals.most_common(10)),
        }

    # Overall summary
    all_sentiments = [item["sentiment"] for item in all_analyzed]
    if all_sentiments:
        overall_polarity = sum(s["polarity"] for s in all_sentiments) / len(all_sentiments)
        overall_subjectivity = sum(s["subjectivity"] for s in all_sentiments) / len(all_sentiments)
        overall_labels = Counter(s["label"] for s in all_sentiments)
    else:
        overall_polarity = 0
        overall_subjectivity = 0
        overall_labels = {}

    all_brand_signals = Counter()
    for item in all_analyzed:
        for cat in item.get("brand_signals", {}):
            all_brand_signals[cat] += 1

    # Find most positive and most negative items
    positive_items = sorted(all_analyzed, key=lambda x: x["sentiment"]["polarity"], reverse=True)[:10]
    negative_items = sorted(all_analyzed, key=lambda x: x["sentiment"]["polarity"])[:10]

    # Find most engaged twitter mentions (use view_count + like_count + retweet_count)
    twitter_items = [i for i in all_analyzed if i.get("source") == "twitter"]
    top_twitter = sorted(
        twitter_items,
        key=lambda x: (
            x.get("view_count", 0)
            + x.get("like_count", 0) * 10
            + x.get("retweet_count", 0) * 20
            + x.get("reply_count", 0) * 5
        ),
        reverse=True,
    )[:10]

    # Find most engaged LinkedIn posts
    linkedin_items = [i for i in all_analyzed if i.get("source") == "linkedin"]
    top_linkedin = sorted(
        linkedin_items,
        key=lambda x: (
            x.get("like_count", 0)
            + x.get("comment_count", 0) * 5
            + x.get("share_count", 0) * 10
        ),
        reverse=True,
    )[:15]

    report_data = {
        "overall": {
            "total_items_analyzed": len(all_analyzed),
            "avg_polarity": round(overall_polarity, 3),
            "avg_subjectivity": round(overall_subjectivity, 3),
            "sentiment_distribution": dict(overall_labels),
            "brand_signal_frequency": dict(all_brand_signals.most_common()),
        },
        "by_source": source_summaries,
        "most_positive": [
            _summarize_item(i) for i in positive_items
        ],
        "most_negative": [
            _summarize_item(i) for i in negative_items
        ],
        "top_twitter_engagement": [
            _summarize_item(i) for i in top_twitter
        ],
        "top_linkedin_engagement": [
            _summarize_item(i) for i in top_linkedin
        ],
    }

    # Save full analyzed data
    analyzed_path = os.path.join(OUTPUT_DIR, "analyzed_data.json")
    with open(analyzed_path, "w", encoding="utf-8") as f:
        json.dump(all_analyzed, f, indent=2, ensure_ascii=False)

    # Save report data
    report_path = os.path.join(OUTPUT_DIR, "report_data.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"  [Analysis] Complete. {len(all_analyzed)} total items analyzed.")
    return report_data


def _summarize_item(item):
    """Create a concise summary of an analyzed item."""
    summary = {
        "source": item.get("source", ""),
        "sentiment": item.get("sentiment", {}),
        "brand_signals": item.get("brand_signals", {}),
    }
    if item.get("source") == "twitter":
        summary["text"] = item.get("text", "")[:300]
        summary["user"] = item.get("user", "")
        summary["user_name"] = item.get("user_name", "")
        summary["date"] = item.get("date", "")
        summary["like_count"] = item.get("like_count", 0)
        summary["retweet_count"] = item.get("retweet_count", 0)
        summary["reply_count"] = item.get("reply_count", 0)
        summary["view_count"] = item.get("view_count", 0)
        summary["engagement"] = (
            item.get("like_count", 0)
            + item.get("retweet_count", 0)
            + item.get("reply_count", 0)
        )
        summary["url"] = item.get("url", "")
    elif item.get("source") == "linkedin":
        summary["text"] = item.get("text", "")[:300]
        summary["author"] = item.get("author", "")
        summary["author_type"] = item.get("author_type", "")
        summary["author_followers"] = item.get("author_followers", "")
        summary["date"] = item.get("date", "")
        summary["time_since"] = item.get("time_since", "")
        summary["like_count"] = item.get("like_count", 0)
        summary["comment_count"] = item.get("comment_count", 0)
        summary["share_count"] = item.get("share_count", 0)
        summary["url"] = item.get("url", "")
    else:
        summary["title"] = item.get("title", "")
        summary["url"] = item.get("url", "")
        summary["description"] = item.get("description", "")[:300]
    return summary


if __name__ == "__main__":
    analyze_all_data()
