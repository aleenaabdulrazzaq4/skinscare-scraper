# Skincare Customer Review Scraper & Sentiment Analysis

A university project that uses **web scraping** to collect customer reviews of
skincare products from two international brands, then evaluates them with
**EDA (Exploratory Data Analysis)** and **Sentiment Analysis**.

**Pipeline:** Web scraping → Data cleaning → EDA → Sentiment analysis → Report

## Brands studied

| Brand | Website | Products | Reviews |
|---|---|---|---|
| Glow Recipe | glowrecipe.com | Shopify `/products.json` | Okendo review feed |
| KraveBeauty | kravebeauty.com | Shopify `/products.json` | Okendo review feed |

## Research questions

1. What is the overall sentiment of customer reviews for each brand?
2. Does the sentiment of the review text match the star rating?
3. Which products are most loved, and which get the most complaints?
4. What words and topics appear most in positive vs negative reviews?
5. Do ratings differ by skin type (oily, dry, sensitive, combination)?

## Project structure

```
skincare-scraper/
├── src/              # Python scripts (scrapers, cleaning, sentiment)
├── data/
│   ├── raw/          # Data exactly as scraped
│   └── processed/    # Cleaned data ready for analysis
├── notebooks/        # Jupyter notebooks for exploration and charts
├── reports/
│   └── figures/      # Saved charts
├── docs/             # Project plan and daily progress log
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python src/scraper.py      # product list
```

## Progress

See [`docs/PROGRESS_LOG.md`](docs/PROGRESS_LOG.md) for what was done each day
and [`docs/10_DAY_PLAN.md`](docs/10_DAY_PLAN.md) for the full plan.

## Ethics

Only publicly visible product data and reviews are collected. Reviewer names
are not stored. The scraper waits between requests and identifies itself.
