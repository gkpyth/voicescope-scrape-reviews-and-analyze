"""
scraper.py
----------
One-time script to collect company reviews from the internet.

What it scrapes: date, rating, review body text (body is only used as input to categorize reviews.
It is never stored in the final CSV).

Respect the scraping limitations of review pages set by the provider. Check /robots.txt.

Usage:
    python scraper.py

Output:
    data/reviews_raw.csv - (contains temporary body text to be categorized)
"""


# TODO: requests-based scraping being blocked after a couple test runs - rewrite scraper using Selenium or Playwright for future data refreshes.


import json
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG - Specific to website
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL  = os.getenv("BASE_URL")
WEBSITE_URL = os.getenv("WEBSITE_URL")
MAX_PAGES = 10       # Capped unauthenticated access at 10 pages
DELAY     = 2.5      # Seconds between requests — be a good, polite bot
OUTPUT    = "data/reviews_raw.csv"

# Browser-like headers reduce the chance of being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": BASE_URL,
}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────
def extract_from_jsonld(soup: BeautifulSoup) -> list[dict]:
    """
    Primary strategy: parse JSON-LD structured data embedded in the page.
    Some websites include schema.org/LocalBusiness markup with review nodes.
    This is, theoretically, more stable than targeting CSS class names (which are hashed and changed frequently).
    If scraping from another website in the future which allows JSON-LD, this would be a good place to start.
    """
    # NOTE: Extraction should change to match the schema.org/LocalBusiness markup of the specific website.
    reviews = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data  = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") != "LocalBusiness":
                    continue
                for review in item.get("review", []):
                    rating = review.get("reviewRating", {}).get("ratingValue")
                    body   = (review.get("reviewBody") or "").strip()
                    date   = (review.get("datePublished") or "")[:10]  # YYYY-MM-DD
                    if rating and body:
                        reviews.append(
                            {"date": date, "rating": int(float(rating)), "body": body}
                        )
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return reviews


# Honestly, this is the most reliable way to get reviews from most websites.
# Schema should change to match the markup of the specific website.
def extract_from_html(soup: BeautifulSoup) -> list[dict]:
    """
    Fallback strategy: parse HTML elements directly.
    Targets data attributes which are more stable than auto-generated class names.
    """
    reviews = []
    for article in soup.select("article[data-service-review-card-paper]"):
        try:
            # Star rating
            rating_element = article.select_one("[data-service-review-rating]")
            rating = int(rating_element["data-service-review-rating"]) if rating_element else None

            # Review body text
            body_element = article.select_one("p[data-service-review-text-typography]")
            body = body_element.get_text(strip=True) if body_element else None

            # Publication date
            time_element = article.select_one("time[datetime]")
            date = time_element["datetime"][:10] if time_element else None

            if rating and body:
                reviews.append({"date": date, "rating": rating, "body": body})
        except (KeyError, TypeError, ValueError):
            continue                # Ensure the script keeps going on periodic random fails
    return reviews


# Persistent session - simulates real browser visit by hitting the homepage first to pick up cookies before requesting
# review pages.
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def warm_session() -> None:
    """Visiting the homepage to acquire cookies before scraping review pages."""
    try:
        SESSION.get(BASE_URL, timeout=15)
        time.sleep(1.5)
    except Exception:
        pass


def scrape_page(page_num: int) -> list[dict]:
    """Fetch a single page of reviews and return parsed records."""
    url = WEBSITE_URL if page_num == 1 else f"{WEBSITE_URL}?page={page_num}"
    response = SESSION.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    reviews = extract_from_jsonld(soup)

    if not reviews:
        print(f"  ↳ JSON-LD empty on page {page_num}, trying HTML fallback...")
        reviews = extract_from_html(soup)

    return reviews


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    os.makedirs("data", exist_ok=True)
    all_reviews: list[dict] = []

    print("Warming session (acquiring cookies)...")
    warm_session()
    print(f"Starting scrape: {WEBSITE_URL}")
    print(f"Pages to attempt: {MAX_PAGES}  |  Delay: {DELAY}s\n")

    for page in range(1, MAX_PAGES + 1):
        print(f"Page {page}/{MAX_PAGES}...", end=" ", flush=True)
        try:
            page_reviews = scrape_page(page)
        except requests.HTTPError as e:
            print(f"HTTP error — {e}. Stopping.")
            break
        except Exception as e:
            print(f"Unexpected error — {e}. Stopping.")
            break

        if not page_reviews:
            print("No reviews found. Stopping (likely hit the login wall).")
            break

        all_reviews.extend(page_reviews)
        print(f"{len(page_reviews)} reviews  (running total: {len(all_reviews)})")

        # !Important! - Polite delay between requests
        if page < MAX_PAGES:
            time.sleep(DELAY)

    if not all_reviews:
        print("\nNo reviews collected. The page structure may have changed.")
        return

    df = pd.DataFrame(all_reviews)
    df.to_csv(OUTPUT, index=False)
    print(f"\n✓ Done — {len(df)} reviews saved to {OUTPUT}")
    print("  Next step: run  python categorize.py")


if __name__ == "__main__":
    main()