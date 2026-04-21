# VoiceScope

A webapp AI categorization pipeline that transforms data (e.g., public reviews) into structured sentiment intelligence. This is part of personal bootcamp portfolio projects.

## Features
- Web scraper collecting data (e.g., public reviews — respecting /robots.txt and public access cap)
- AI-powered semantic categorization via Google Gemini — no keyword matching
- Retry logic for transient API failures (3 attempts, 3 seconds apart)
- Privacy-first pipeline — no personal identifying data is collected or stored. In this case, review text was used as input only, never stored or displayed
- Interactive Streamlit dashboard styled to match portfolio design system
- Stacked sentiment bar chart per category (Positive / Neutral / Negative breakdown)
- Rating distribution chart
- Fading 5-row preview table
- CSV and chart PNG download
- Pre-cached dataset — app runs instantly without re-scraping or re-categorization

## Requirements
- Python 3.12+
- Google Gemini API key (free tier)

## Installation
```
pip install -r requirements.txt
```

## How to Run
```
streamlit run app.py
```
The app runs at `http://localhost:8501`.

## Pipeline

| Step | Script | Input             | Output |
|------|--------|-------------------|--------|
| 1 | `scraper.py` | Website URL       | `data/reviews_raw.csv` |
| 2 | `categorize.py` | `reviews_raw.csv` | `data/reviews.csv` |
| 3 | `app.py` | `reviews.csv`     | Interactive dashboard |

A committed `data/reviews.csv` is included so the app runs immediately without re-scraping or re-categorization.

## AI Categorization

Review body text is sent to Gemini with a structured prompt. The model returns a category and sentiment label. The body text is then discarded — it never appears in the final CSV.

**Categories:** Onboarding & Setup · Customer Support · Pricing & Value · Product UX & Design · Missing Features · Reliability & Bugs · Other

**Sentiments:** Positive · Neutral · Negative

## Project Structure
```
voicescope/
├── app.py                  # Streamlit dashboard
├── scraper.py              # One-time web scraper
├── categorize.py           # One-time Gemini categorization script
├── requirements.txt
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
├── .streamlit/
│   └── config.toml         # Theme — matches portfolio palette
└── data/
    └── reviews.csv         # Final dataset: date, rating, category, sentiment
```

## Environment Variables
```
GEMINI_API_KEY=your_key_here
BASE_URL=website_url_here
WEBSITE_URL=website_url_with_reviews_here
```

## Limitations
- Some websites cap unauthenticated access entirely or after a certain page/review number — respect /robots.txt
- Scraper ran fine initially but now is currently blocked by Cloudflare bot protection — see open issues for migration plan
- Gemini free tier: 15 RPM, 500 RPD on `gemini-3.1-flash-lite-preview`
- Pre-cached dataset does not auto-refresh — re-run the pipeline to update

## Author
Ghaleb Khadra