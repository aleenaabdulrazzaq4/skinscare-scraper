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
| 3 | Product lists for both brands ✅ | src/scraper.py, data/raw/*_products.json | `Day 3: scrape product lists for both brands` |
| 4 | Review scraper (one product) ✅ | src/reviews.py, data/raw/sample_reviews.json | `Day 4: review scraper tested on one product` |
| 5 | Reviews for all products ✅ | src/reviews.py, data/raw/reviews.csv | `Day 5: scrape all reviews (10,037 reviews)` |
| 6 | Data cleaning ✅ | src/clean.py, data/processed/reviews_clean.csv | `Day 6: clean review data` |
| 7 | **EDA** (Exploratory Data Analysis) ✅ | src/style.py, src/eda.py, reports/figures/eda_*.png | `Day 7: EDA of customer reviews` |
| 8 | **Sentiment analysis** ✅ | src/sentiment.py, reports/figures/sent_*.png | `Day 8: VADER sentiment analysis, word and complaint analysis` |
| 9 | Report ✅ | reports/REPORT.md | `Day 9: project report` |
| 10 | Results + polish ✅ | README.md results, requirements.txt, docs | `Day 10: results summary and final polish` |

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

### Day 8 (continued) — Charts and words
- Bar chart: sentiment split per brand.
- Chart: average sentiment by star rating.
- Top 15 words in positive vs negative reviews.
- Word clouds for positive and negative reviews.
- Most common complaints (e.g. "breakout", "sticky", "smell").

### Day 9 — Report
- Write `reports/REPORT.md` with every chart and the findings for each research question.

### Day 10 — Results and polish
- Add a results summary with key charts to the README, update requirements, final progress log.

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
