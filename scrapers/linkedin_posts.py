"""LinkedIn post scraper using Apify actors for Adara Ventures engagement data."""

import json
import os
from apify_client import ApifyClient
from config import APIFY_TOKEN, OUTPUT_DIR


# Adara Ventures LinkedIn company URL
LINKEDIN_COMPANY_URL = "https://www.linkedin.com/company/adaravc/"

# Known LinkedIn post URLs from Google search results
KNOWN_POST_URLS = [
    "https://www.linkedin.com/posts/adaravc_adara-ventures-year-in-review-2025-activity-7407794860151287808-kKft",
    "https://www.linkedin.com/posts/adaravc_ai-activity-7104762855882657793-M4xp",
    "https://www.linkedin.com/posts/strachanross_strengthening-the-adara-ventures-team-promotions-activity-7175404728774737920-VOJV",
    "https://www.linkedin.com/posts/adaravc_adara-ventures-year-in-review-2023-activity-7143917571698855936-aAdw",
]


def run_linkedin_scraper():
    """Scrape LinkedIn posts from Adara Ventures company page."""
    client = ApifyClient(APIFY_TOKEN)
    all_results = []

    # Strategy 1: Scrape company posts using linkedin-post-search
    print("  [LinkedIn] Scraping Adara Ventures company posts...")
    try:
        run_input = {
            "searchTerms": ["Adara Ventures"],
            "maxResults": 50,
            "sortBy": "relevance",
        }
        run = client.actor("curious_coder/linkedin-post-search-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"    -> Found {len(items)} LinkedIn posts")

        for post in items:
            all_results.append({
                "source": "linkedin",
                "text": post.get("text", post.get("content", "")),
                "author": post.get("authorName", post.get("author", "")),
                "author_title": post.get("authorTitle", ""),
                "author_url": post.get("authorUrl", post.get("authorProfileUrl", "")),
                "url": post.get("postUrl", post.get("url", "")),
                "date": post.get("publishedAt", post.get("postedDate", "")),
                "like_count": post.get("likeCount", post.get("numLikes", 0)),
                "comment_count": post.get("commentCount", post.get("numComments", 0)),
                "repost_count": post.get("repostCount", post.get("numShares", 0)),
                "impression_count": post.get("impressionCount", post.get("numImpressions", 0)),
            })
    except Exception as e:
        print(f"    -> Error with linkedin-post-search: {e}")
        print("    -> Trying alternative approach...")

        # Strategy 2: Use a general LinkedIn scraper
        try:
            run_input = {
                "urls": [LINKEDIN_COMPANY_URL],
                "maxPosts": 50,
            }
            run = client.actor("anchor/linkedin-scraper").call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            print(f"    -> Found {len(items)} items via linkedin-scraper")

            for post in items:
                all_results.append({
                    "source": "linkedin",
                    "text": post.get("text", post.get("content", post.get("description", ""))),
                    "author": post.get("authorName", post.get("author", "")),
                    "author_title": post.get("authorTitle", ""),
                    "author_url": post.get("authorUrl", ""),
                    "url": post.get("postUrl", post.get("url", "")),
                    "date": post.get("publishedAt", post.get("postedDate", "")),
                    "like_count": post.get("likeCount", post.get("numLikes", 0)),
                    "comment_count": post.get("commentCount", post.get("numComments", 0)),
                    "repost_count": post.get("repostCount", post.get("numShares", 0)),
                    "impression_count": post.get("impressionCount", 0),
                })
        except Exception as e2:
            print(f"    -> Fallback also failed: {e2}")

    output_path = os.path.join(OUTPUT_DIR, "linkedin_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  [LinkedIn] Total posts saved: {len(all_results)}")
    return all_results


if __name__ == "__main__":
    run_linkedin_scraper()
