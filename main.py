"""
Adara Ventures — Brand & Sentiment Scraping Pipeline
=====================================================
Orchestrates scraping from multiple sources via Apify, runs sentiment
analysis, and generates an HTML report.

Usage:
    python main.py              # Run full pipeline
    python main.py --scrape     # Only scrape (skip analysis/report)
    python main.py --analyze    # Only analyze + report (skip scraping)
"""

import sys
import time
import json
import os
from datetime import datetime

from config import APIFY_TOKEN, OUTPUT_DIR


def check_apify_balance():
    """Check remaining Apify account balance before running."""
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_TOKEN)
    try:
        user = client.user().get()
        plan = user.get("plan", {})
        print(f"  Account: {user.get('username', 'unknown')}")
        print(f"  Plan: {plan.get('id', 'unknown')}")
        # Proxy & usage info may vary by plan
        return True
    except Exception as e:
        print(f"  WARNING: Could not verify Apify account: {e}")
        return True  # proceed anyway


def run_scraping():
    """Run all scrapers sequentially to control costs."""
    from scrapers.google_search import run_google_search
    from scrapers.google_news import run_google_news
    from scrapers.twitter_search import run_twitter_search
    from scrapers.web_content import run_web_scraper

    print("\n" + "=" * 60)
    print("PHASE 1: SCRAPING")
    print("=" * 60)

    # 1. Google Search — broadest coverage, most cost-effective
    print("\n[1/4] Google Search Results")
    t0 = time.time()
    google_results = run_google_search()
    print(f"       Done in {time.time()-t0:.0f}s\n")

    # 2. Google News — press & media coverage
    print("[2/4] Google News")
    t0 = time.time()
    news_results = run_google_news()
    print(f"       Done in {time.time()-t0:.0f}s\n")

    # 3. Twitter/X — social sentiment
    print("[3/4] Twitter / X")
    t0 = time.time()
    twitter_results = run_twitter_search()
    print(f"       Done in {time.time()-t0:.0f}s\n")

    # 4. Web content — Adara's own site + key external pages
    # Extract top URLs from Google results to also scrape
    extra_urls = []
    for r in (google_results + news_results):
        url = r.get("url", "")
        if url and "google.com" not in url and url not in extra_urls:
            extra_urls.append(url)
    extra_urls = extra_urls[:20]  # limit to top 20 for budget

    print("[4/4] Web Content Scraping")
    t0 = time.time()
    web_results = run_web_scraper(extra_urls=extra_urls)
    print(f"       Done in {time.time()-t0:.0f}s\n")

    # Summary
    total = len(google_results) + len(news_results) + len(twitter_results) + len(web_results)
    print(f"SCRAPING COMPLETE: {total} total data points collected")
    print(f"  - Google Search: {len(google_results)}")
    print(f"  - Google News:   {len(news_results)}")
    print(f"  - Twitter/X:     {len(twitter_results)}")
    print(f"  - Web Content:   {len(web_results)}")


def run_analysis():
    """Run sentiment analysis and generate report."""
    from analyze import analyze_all_data
    from report import generate_report

    print("\n" + "=" * 60)
    print("PHASE 2: ANALYSIS & REPORT")
    print("=" * 60)

    print("\n[1/2] Sentiment & Brand Analysis")
    report_data = analyze_all_data()

    print("\n[2/2] Generating HTML Report")
    report_path = generate_report()

    if report_data:
        overall = report_data["overall"]
        dist = overall.get("sentiment_distribution", {})
        print(f"\n{'=' * 60}")
        print("RESULTS SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Total items analyzed: {overall['total_items_analyzed']}")
        print(f"  Overall sentiment:    {overall['avg_polarity']:+.3f}")
        print(f"    Positive: {dist.get('positive', 0)}")
        print(f"    Neutral:  {dist.get('neutral', 0)}")
        print(f"    Negative: {dist.get('negative', 0)}")
        print(f"\n  Top brand signals:")
        for signal, count in list(overall.get("brand_signal_frequency", {}).items())[:6]:
            print(f"    {signal.replace('_', ' '):20s} — {count} mentions")

    if report_path:
        print(f"\n  Report: {report_path}")
        print(f"  Open in browser to view the full interactive report.")


def main():
    print("=" * 60)
    print("  ADARA VENTURES — Brand & Sentiment Scraping Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check what mode to run
    args = set(sys.argv[1:])
    scrape_only = "--scrape" in args
    analyze_only = "--analyze" in args

    if not analyze_only:
        print("\nChecking Apify account...")
        check_apify_balance()

    if analyze_only:
        run_analysis()
    elif scrape_only:
        run_scraping()
    else:
        run_scraping()
        run_analysis()

    print(f"\nPipeline finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
