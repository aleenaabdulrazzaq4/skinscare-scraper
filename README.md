# Skincare Product Scraper & Price Analysis

A project that scrapes product data from international skincare brands
running on Shopify, cleans it, and analyzes pricing, discounts and product ranges.

## Brands studied

| Brand | Website | Data source |
|---|---|---|
| Glow Recipe | glowrecipe.com | `/products.json` |
| KraveBeauty | kravebeauty.com | `/products.json` |
| Summer Fridays | summerfridays.com | `/products.json` |

## Research questions

1. How do average prices differ between the three brands?
2. Which product categories (cleansers, serums, moisturizers, sets) are most common?
3. How many products are on sale, and how big are the discounts?
4. How much does price per ml/g vary across brands and categories?
5. Which ingredients appear most often in product descriptions?

## Project structure

```
skincare-scraper/
├── src/              # Python scripts (scraper, cleaning, analysis)
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
python src/scraper.py          # coming on Day 2
```

## Progress

See [`docs/PROGRESS_LOG.md`](docs/PROGRESS_LOG.md) for what was done each day.

## Ethics

Only publicly available product data is collected. The scraper waits between
requests, identifies itself honestly, and collects no personal information.
