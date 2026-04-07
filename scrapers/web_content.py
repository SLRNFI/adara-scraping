"""Web content scraper — scrapes Adara Ventures' own site + key external pages."""

import json
import os
from apify_client import ApifyClient
from config import APIFY_TOKEN, OUTPUT_DIR


# Key URLs to scrape for full content
SEED_URLS = [
    "https://www.adaraventures.com/",
    "https://www.adaraventures.com/about",
    "https://www.adaraventures.com/team",
    "https://www.adaraventures.com/portfolio",
    "https://www.adaraventures.com/blog",
    "https://www.crunchbase.com/organization/adara-ventures",
]


def run_web_scraper(extra_urls=None):
    """Scrape web pages for full content about Adara Ventures."""
    client = ApifyClient(APIFY_TOKEN)
    urls = SEED_URLS + (extra_urls or [])
    all_results = []

    print(f"  [Web] Scraping {len(urls)} URLs...")

    run_input = {
        "startUrls": [{"url": u} for u in urls],
        "maxCrawlDepth": 1,
        "maxPagesPerCrawl": 50,
        "pageFunction": """async function pageFunction(context) {
            const { page, request } = context;
            const title = await page.title();
            const text = await page.evaluate(() => {
                // Remove scripts, styles, nav, footer
                const removes = document.querySelectorAll('script, style, nav, footer, header');
                removes.forEach(el => el.remove());
                return document.body ? document.body.innerText.trim() : '';
            });
            const metaDesc = await page.evaluate(() => {
                const meta = document.querySelector('meta[name="description"]');
                return meta ? meta.getAttribute('content') : '';
            });
            return {
                url: request.url,
                title,
                metaDescription: metaDesc,
                text: text.substring(0, 5000),  // cap at 5k chars per page
            };
        }""",
    }

    try:
        run = client.actor("apify/web-scraper").call(run_input=run_input)
        dataset_items = list(
            client.dataset(run["defaultDatasetId"]).iterate_items()
        )

        for item in dataset_items:
            all_results.append({
                "source": "web_scrape",
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "meta_description": item.get("metaDescription", ""),
                "text": item.get("text", ""),
            })

        print(f"    -> Scraped {len(dataset_items)} pages")
    except Exception as e:
        print(f"    -> Error: {e}")
        # Fallback: try with cheerio-scraper (cheaper, no JS rendering)
        print("    -> Trying cheerio-scraper fallback...")
        try:
            run_input_fallback = {
                "startUrls": [{"url": u} for u in urls],
                "maxCrawlDepth": 1,
                "maxRequestsPerCrawl": 50,
                "pageFunction": """async function pageFunction(context) {
                    const { $, request } = context;
                    const title = $('title').text();
                    const metaDesc = $('meta[name="description"]').attr('content') || '';
                    // Remove nav, footer, script, style
                    $('script, style, nav, footer, header').remove();
                    const text = $('body').text().replace(/\\s+/g, ' ').trim().substring(0, 5000);
                    return {
                        url: request.url,
                        title,
                        metaDescription: metaDesc,
                        text,
                    };
                }""",
            }
            run = client.actor("apify/cheerio-scraper").call(run_input=run_input_fallback)
            dataset_items = list(
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )
            for item in dataset_items:
                all_results.append({
                    "source": "web_scrape",
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "meta_description": item.get("metaDescription", ""),
                    "text": item.get("text", ""),
                })
            print(f"    -> Scraped {len(dataset_items)} pages (fallback)")
        except Exception as e2:
            print(f"    -> Fallback also failed: {e2}")

    output_path = os.path.join(OUTPUT_DIR, "web_content_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  [Web] Total pages saved: {len(all_results)}")
    return all_results


if __name__ == "__main__":
    run_web_scraper()
