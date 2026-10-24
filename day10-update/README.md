# Skincare Customer Review Scraper & Sentiment Analysis

A university project that uses **web scraping** to collect customer reviews of
skincare products from two international brands, then evaluates them with
**EDA (Exploratory Data Analysis)** and **Sentiment Analysis**.

**Pipeline:** Web scraping → Data cleaning → EDA → Sentiment analysis → Report

📄 **Full report:** [`reports/REPORT.md`](reports/REPORT.md)

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

## Results at a glance

**10,018 reviews** of **120 products** (7,888 Glow Recipe, 2,130 KraveBeauty), July 2019 – October 2026.

| | Glow Recipe | KraveBeauty | All |
|---|---|---|---|
| Average rating | 4.72 ★ | 4.48 ★ | 4.67 ★ |
| Positive text (VADER) | 92.0% | 89.3% | 91.4% |
| Negative text (VADER) | 3.5% | 7.0% | 4.2% |

- **Customers are very satisfied:** 82% of reviews are 5 stars and 91% of review text is positive.
- **Glow Recipe outperforms KraveBeauty:** higher ratings (4% vs 8% of reviews are 1–2★) and half the share of negative text.
  7 of the 10 lowest-rated products are KraveBeauty's.
- **Unhappy customers write almost twice as much:** median 48 words for 1–2★ reviews vs 26 for 4–5★.
- **Top complaints:** irritation/burning (20% of negative reviews), smell (18%), breakouts (17%), packaging (17%).
- **Skin type barely matters:** every skin type averages 4.65–4.77 ★ and 93–96% positive text.
- **VADER misses polite complaints:** only 36% of 1–2★ reviews were labelled negative, because unhappy
  customers often add praise ("Allergic reaction. I love Glow Recipe though!") and use skincare words
  VADER doesn't know ("clogged pores").

![Sentiment by brand](reports/figures/sent_1_sentiment_by_brand.png)
![Star rating vs text sentiment](reports/figures/sent_3_rating_vs_sentiment.png)
![Complaints](reports/figures/sent_8_complaints.png)

## Project structure

```
skincare-scraper/
├── src/
│   ├── scraper.py      # Day 2-3: product lists from Shopify
│   ├── reviews.py      # Day 4-5: customer reviews from Okendo
│   ├── clean.py        # Day 6:   data cleaning
│   ├── style.py        #          shared chart style
│   ├── eda.py          # Day 7:   EDA charts
│   └── sentiment.py    # Day 8:   VADER sentiment, top words, complaints
├── data/
│   ├── raw/            # data exactly as scraped
│   └── processed/      # cleaned and scored data
├── reports/
│   ├── REPORT.md       # Day 9:   full project report
│   └── figures/        # all charts
├── docs/               # 10-day plan and daily progress log
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python src/scraper.py      # product lists        -> data/raw/*_products.json
python src/reviews.py      # customer reviews     -> data/raw/reviews.csv  (~15 min)
python src/clean.py        # cleaning             -> data/processed/reviews_clean.csv
python src/eda.py          # EDA charts           -> reports/figures/eda_*.png
python src/sentiment.py    # sentiment + charts   -> reports/figures/sent_*.png
```

Run every command from the main project folder.

## Progress

See [`docs/PROGRESS_LOG.md`](docs/PROGRESS_LOG.md) for what was done each day
and [`docs/10_DAY_PLAN.md`](docs/10_DAY_PLAN.md) for the plan.

## Ethics

Only publicly visible product data and reviews are collected. Reviewer names
are not stored. The scraper waits 1 second between requests, identifies itself,
and collects at most 200 reviews per product.
