"""
categorize.py
-------------
One-time script that enriches the raw reviews dataset with AI-generated
category and sentiment labels using the Google Gemini API (free tier).

Pipeline:
    scraper.py    ->  data/reviews_raw.csv
    categorize.py ->  reads body text, sends to Gemini, writes data/reviews.csv
    app.py        ->  reads data/reviews.csv — body text never touches it

Privacy note: review body text is used here as a prompt input and discarded.
The final CSV contains only: date, rating, category, sentiment.

Usage:
    python categorize.py

Requirements:
    GEMINI_API_KEY set in .env
"""

import json
import os
import time

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INPUT_FILE     = "data/reviews_raw.csv"
OUTPUT_FILE    = "data/reviews.csv"

# Gemini free tier: 15 requests/minute.
DELAY = 4.5     # A delay of 4.5 seconds -> ~13 RPM — safely under the limit.

CATEGORIES = [
    "Onboarding & Setup",
    "Customer Support",
    "Pricing & Value",
    "Product UX & Design",
    "Missing Features",
    "Reliability & Bugs",
    "Other",
]

SENTIMENTS = ["Positive", "Neutral", "Negative"]

# ─────────────────────────────────────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """
You are a Customer Success analyst reading software product reviews.

Analyze the review below and classify it using ONLY the options provided.

Categories: {categories}
Sentiments: {sentiments}

Review:
\"\"\"{body}\"\"\"

Respond with ONLY a valid JSON object — no markdown, no explanation, nothing else.
Format: {{"category": "<one of the categories>", "sentiment": "<one of the sentiments>"}}
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI SETUP — uses new google-genai SDK
# ─────────────────────────────────────────────────────────────────────────────
def setup_client():
    """Initialize and return the Gemini client using the google-genai SDK."""
    from google import genai

    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY not found. Add it to your .env file."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────
def classify(client, body: str) -> dict:
    """
    Send a review body to Gemini and return {category, sentiment}.

    Retry logic: up to 3 attempts, 3 seconds apart, for transient 503 errors
    (model high demand). Falls back to ("Other", "Neutral") if all
    attempts fail or a non-retriable error occurs.
    """
    prompt = PROMPT_TEMPLATE.format(
        categories=", ".join(CATEGORIES),
        sentiments=", ".join(SENTIMENTS),
        body=body.replace('"', "'"),
    )

    MAX_RETRIES = 3
    RETRY_DELAY = 3   # seconds between attempts

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL"),
                contents=prompt,
            )

            raw_text = (response.text or "").strip()

            # Strip markdown fences if Gemini wraps the response
            if raw_text.startswith("```"):
                parts    = raw_text.split("```")
                raw_text = parts[1].lstrip("json").strip() if len(parts) > 1 else raw_text

            result    = json.loads(raw_text)
            category  = result.get("category", "Other")
            sentiment = result.get("sentiment", "Neutral")

            # Reject anything outside the defined buckets
            if category  not in CATEGORIES:
                category  = "Other"
            if sentiment not in SENTIMENTS:
                sentiment = "Neutral"

            return {"category": category, "sentiment": sentiment}

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"attempt {attempt} failed ({e}) — retrying in {RETRY_DELAY}s...", end=" ", flush=True)
                time.sleep(RETRY_DELAY)

    # All attempts exhausted
    raise last_error


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        print("Run  python scraper.py  first.")
        return

    client = setup_client()
    df     = pd.read_csv(INPUT_FILE)
    total  = len(df)
    print(f"Loaded {total} reviews from {INPUT_FILE}")
    print(f"Sending to Gemini at ~{60 / DELAY:.0f} RPM (free tier limit: 15 RPM)\n")

    categories = []
    sentiments = []

    for i, row in df.iterrows():
        print(f"[{i + 1}/{total}] Classifying...", end=" ", flush=True)
        try:
            result = classify(client, str(row["body"]))
            categories.append(result["category"])
            sentiments.append(result["sentiment"])
            print(f"{result['category']}  .  {result['sentiment']}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Parse error ({e}) — defaulting to Other / Neutral")
            categories.append("Other")
            sentiments.append("Neutral")
        except Exception as e:
            print(f"API error ({e}) — defaulting to Other / Neutral")
            categories.append("Other")
            sentiments.append("Neutral")

        if i < total - 1:
            time.sleep(DELAY)

    # Output CSV — body intentionally excluded
    out_df = pd.DataFrame({
        "date":      df["date"],
        "rating":    df["rating"],
        "category":  categories,
        "sentiment": sentiments,
    })

    out_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone — {len(out_df)} reviews saved to {OUTPUT_FILE}")
    print("  Next step: run  streamlit run app.py")


if __name__ == "__main__":
    main()