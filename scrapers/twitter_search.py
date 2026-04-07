"""Twitter/X scraper using Apify's tweet-scraper actor."""

import json
import os
from apify_client import ApifyClient
from config import APIFY_TOKEN, TWITTER_QUERIES, TWITTER_MAX_TWEETS, OUTPUT_DIR


def _parse_tweet(tweet, query):
    """Parse a tweet from the Apify tweet-scraper (61RPP7dywgiy0JPD0) format."""
    author = tweet.get("author", {})
    return {
        "source": "twitter",
        "query": query,
        "text": tweet.get("fullText", tweet.get("full_text", tweet.get("text", ""))),
        "user": author.get("userName", ""),
        "user_name": author.get("name", ""),
        "user_description": author.get("description", ""),
        "user_verified": author.get("isBlueVerified", False),
        "date": tweet.get("createdAt", ""),
        "retweet_count": tweet.get("retweetCount", 0),
        "like_count": tweet.get("likeCount", 0),
        "reply_count": tweet.get("replyCount", 0),
        "quote_count": tweet.get("quoteCount", 0),
        "view_count": tweet.get("viewCount", 0),
        "bookmark_count": tweet.get("bookmarkCount", 0),
        "url": tweet.get("url", ""),
        "is_retweet": tweet.get("isRetweet", False),
        "is_reply": tweet.get("isReply", False),
        "lang": tweet.get("lang", ""),
    }


def run_twitter_search():
    """Scrape Twitter/X for mentions of Adara Ventures."""
    client = ApifyClient(APIFY_TOKEN)
    all_results = []

    for query in TWITTER_QUERIES:
        print(f"  [Twitter] Searching: {query}")
        run_input = {
            "searchTerms": [query],
            "maxTweets": TWITTER_MAX_TWEETS,
            "sort": "Latest",
            "tweetLanguage": "en",
        }

        try:
            run = client.actor("apidojo/tweet-scraper").call(run_input=run_input)
            dataset_items = list(
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )
            for tweet in dataset_items:
                all_results.append(_parse_tweet(tweet, query))
            print(f"    -> Found {len(dataset_items)} tweets")
        except Exception as e:
            print(f"    -> Error: {e}")

    # Deduplicate by URL (more reliable than text)
    seen = set()
    deduped = []
    for r in all_results:
        key = r.get("url") or r["text"]
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    all_results = deduped

    output_path = os.path.join(OUTPUT_DIR, "twitter_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  [Twitter] Total unique tweets saved: {len(all_results)}")
    return all_results


def reparse_twitter_from_apify():
    """Re-extract Twitter data from existing Apify datasets (no new API calls)."""
    client = ApifyClient(APIFY_TOKEN)
    all_results = []
    seen = set()

    # Get all recent runs and find tweet-scraper datasets
    runs = list(client.runs().list(limit=20).items)
    tweet_dataset_ids = set()
    for r in runs:
        if r.get("actId") in ("61RPP7dywgiy0JPD0", "dMVfdJsIq6XnFIU99"):
            ds_id = r.get("defaultDatasetId", "")
            if ds_id:
                tweet_dataset_ids.add(ds_id)

    print(f"  [Twitter] Found {len(tweet_dataset_ids)} tweet datasets to re-parse")

    for ds_id in tweet_dataset_ids:
        items = list(client.dataset(ds_id).iterate_items())
        for tweet in items:
            parsed = _parse_tweet(tweet, "")
            key = parsed.get("url") or parsed["text"]
            if key not in seen:
                seen.add(key)
                all_results.append(parsed)

    output_path = os.path.join(OUTPUT_DIR, "twitter_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  [Twitter] Re-parsed {len(all_results)} unique tweets with engagement data")
    return all_results


if __name__ == "__main__":
    reparse_twitter_from_apify()
