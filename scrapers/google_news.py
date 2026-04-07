"""Google News scraper using Apify's google-search-scraper with news tab."""

import json
import os
from apify_client import ApifyClient
from config import APIFY_TOKEN, OUTPUT_DIR


NEWS_QUERIES = [
    '"Adara Ventures"',
    '"Adara Ventures" fund OR investment',
    '"Adara Ventures" deep tech OR Europe',
]


def run_google_news():
    """Scrape Google News results for Adara Ventures."""
    client = ApifyClient(APIFY_TOKEN)
    all_results = []

    for query in NEWS_QUERIES:
        print(f"  [News] Searching: {query}")
        run_input = {
            "queries": query,
            "maxPagesPerQuery": 3,
            "resultsPerPage": 10,
            "languageCode": "en",
            "mobileResults": False,
            # Use the news search type
            "searchType": "news",
        }

        try:
            run = client.actor("apify/google-search-scraper").call(run_input=run_input)
            dataset_items = list(
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )

            for item in dataset_items:
                # News results can be in newsResults or organicResults
                news = item.get("newsResults", item.get("organicResults", []))
                for result in news:
                    all_results.append({
                        "source": "google_news",
                        "query": query,
                        "title": result.get("title", ""),
                        "url": result.get("url", result.get("link", "")),
                        "description": result.get("description", result.get("snippet", "")),
                        "date": result.get("date", result.get("publishedAt", "")),
                        "publisher": result.get("source", ""),
                    })

            print(f"    -> Found {len(dataset_items)} page(s) of news results")
        except Exception as e:
            print(f"    -> Error: {e}")

    output_path = os.path.join(OUTPUT_DIR, "google_news_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  [News] Total news results saved: {len(all_results)}")
    return all_results


if __name__ == "__main__":
    run_google_news()
