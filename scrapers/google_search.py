"""Google Search scraper using Apify's google-search-scraper actor."""

import json
import os
from apify_client import ApifyClient
from config import APIFY_TOKEN, GOOGLE_QUERIES, GOOGLE_MAX_PAGES, OUTPUT_DIR


def run_google_search():
    """Run Google Search scraper for all configured queries."""
    client = ApifyClient(APIFY_TOKEN)
    all_results = []

    for query in GOOGLE_QUERIES:
        print(f"  [Google] Searching: {query}")
        run_input = {
            "queries": query,
            "maxPagesPerQuery": GOOGLE_MAX_PAGES,
            "resultsPerPage": 10,
            "languageCode": "en",
            "mobileResults": False,
            "includeUnfilteredResults": False,
        }

        try:
            run = client.actor("apify/google-search-scraper").call(run_input=run_input)
            dataset_items = list(
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )

            for item in dataset_items:
                organic = item.get("organicResults", [])
                for result in organic:
                    all_results.append({
                        "source": "google_search",
                        "query": query,
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", ""),
                        "date": result.get("date", ""),
                    })

            print(f"    -> Found {len(dataset_items)} page(s) of results")
        except Exception as e:
            print(f"    -> Error: {e}")

    # Save results
    output_path = os.path.join(OUTPUT_DIR, "google_search_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  [Google] Total results saved: {len(all_results)}")
    return all_results


if __name__ == "__main__":
    run_google_search()
