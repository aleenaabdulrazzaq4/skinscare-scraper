# 10-Day Project Plan (updated)

**Project goal:** use web scraping to collect customer reviews of skincare products,
then evaluate them with **EDA (Exploratory Data Analysis)** and **Sentiment Analysis**.

**Pipeline:** Web scraping → Cleaning → EDA → Sentiment analysis → Report

**Brands:** Glow Recipe and KraveBeauty. Both are Shopify stores and both use the
**Okendo** review app, so one review scraper works for both.

Each day ends with one commit to GitHub and a short entry in `docs/PROGRESS_LOG.md`.

| Day | Focus | Files added / changed | Commit message |
|---|---|---|---|
| 1 | Setup ✅ | README.md, requirements.txt, .gitignore, folders, docs/ | `Day 1: project setup and plan` |
| 2 | Product scraper (one brand) ✅ | src/scraper.py | `Day 2: product scraper for Glow Recipe` |
| 3 | Product lists for both brands | src/scraper.py, data/raw/*_products.json | `Day 3: scrape product lists for both brands` |
| 4 | Review scraper (one product) | src/reviews.py | `Day 4: review scraper for one product` |
| 5 | Reviews for all products | src/reviews.py, data/raw/reviews.csv | `Day 5: scrape all reviews` |
| 6 | Clean review text | src/clean.py, data/processed/reviews_clean.csv | `Day 6: clean review text` |
| 7 | **EDA** (Exploratory Data Analysis) | notebooks/01_eda.ipynb | `Day 7: EDA of customer reviews` |
| 8 | **Sentiment analysis** | src/sentiment.py, notebook update | `Day 8: sentiment analysis` |
| 9 | Charts + word analysis | notebooks/02_charts.ipynb, reports/figures/*.png | `Day 9: charts and top words` |
| 10 | Report + polish | reports/REPORT.md, README results | `Day 10: final report` |

## Day-by-day detail

### Day 1 — Setup ✅
Repo, folders, README, requirements, progress log.

### Day 2 — Product scraper ✅
`src/scraper.py` downloads all Glow Recipe products from `/products.json`
(126 products). We need this list because every review belongs to a product ID.

### Day 3 — Product lists for both brands
- Loop over both stores and save `data/raw/glow_recipe_products.json` and
  `data/raw/kravebeauty_products.json`.
- Skip non-products (free sachets, $0 hidden items, gift cards, merch).

### Day 4 — Review scraper for ONE product
- Learn how the Okendo review feed works:
  `api.okendo.io/v1/stores/<store id>/products/shopify-<product id>/reviews`
- Download reviews for one product and print them.
- Handle pagination using the `nextUrl` field.

### Day 5 — Reviews for all products
- Loop over every product of both brands and collect all reviews.
- Save one row per review to `data/raw/reviews.csv`:
  brand, product, rating, title, review text, date, skin type, age range,
  verified buyer, recommended.
- **Privacy:** do not save reviewer names.

### Day 6 — Clean the text
- Remove empty/duplicate reviews, keep English only.
- Make lowercase, remove punctuation, links and emojis.
- Remove stopwords ("the", "and", "is"…).
- Save `data/processed/reviews_clean.csv`.

### Day 7 — EDA (Exploratory Data Analysis)
- How many reviews per brand and product?
- Star-rating distribution (how many 1★ … 5★).
- Average rating per brand, per product, per skin type.
- Review length vs rating.

### Day 8 — Sentiment analysis
- Use **VADER** (made for short, informal text) to score each review
  from −1 (very negative) to +1 (very positive).
- Label each review Positive / Neutral / Negative.
- Compare the sentiment label with the star rating: do they agree?
  Find reviews where they don't (e.g. 5★ but negative text).

### Day 9 — Charts and words
- Bar chart: sentiment split per brand.
- Chart: average sentiment by star rating.
- Top 15 words in positive vs negative reviews.
- Word clouds for positive and negative reviews.
- Most common complaints (e.g. "breakout", "sticky", "smell").

### Day 10 — Report and polish
- Write `reports/REPORT.md`, add key charts to the README, comment the code.

## Report structure
1. Introduction — web scraping and why customer reviews matter
2. Objectives — the research questions
3. Methodology — data sources, tools, scraping steps, cleaning, VADER
4. Ethical considerations — public data only, no reviewer names, polite delays
5. Results — charts with short explanations
6. Discussion — what customers love/complain about, limitations
   (VADER misses sarcasm; incentivised reviews; only two brands)
7. Conclusion and future work
8. References
