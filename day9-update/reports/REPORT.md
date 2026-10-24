# What Customers Really Think: Web Scraping, EDA and Sentiment Analysis of Skincare Reviews

**Project:** Skincare Customer Review Scraper & Sentiment Analysis
**Brands studied:** Glow Recipe and KraveBeauty
**Data:** 10,018 customer reviews of 120 products, collected October 2026
**Tools:** Python, requests, pandas, matplotlib, VADER, WordCloud

---

## 1. Introduction

Online reviews are one of the main ways shoppers decide what skincare to buy, and
one of the best sources of honest feedback a brand has. But a popular product can
have thousands of reviews, far too many to read by hand.

**Web scraping** solves the collection problem: a program visits a website and
automatically extracts the information we want. **Exploratory Data Analysis (EDA)**
and **sentiment analysis** then turn thousands of reviews into a clear picture of
what customers like and dislike.

This project builds that full pipeline for two international skincare brands that
sell online through Shopify stores:

```
Web scraping  ->  Data cleaning  ->  EDA  ->  Sentiment analysis  ->  Findings
```

## 2. Objectives

1. Build a web scraper that collects products and customer reviews automatically.
2. Clean the raw data so it is ready for analysis.
3. Use **EDA** to understand the reviews: how ratings are spread, and how they differ
   by brand, product category and skin type.
4. Use **sentiment analysis** to measure how positive or negative each review's text is.
5. Answer five research questions:
   - **RQ1.** What is the overall sentiment of customer reviews for each brand?
   - **RQ2.** Does the sentiment of the text match the star rating?
   - **RQ3.** Which products are most loved, and which get the most complaints?
   - **RQ4.** What words and topics appear most in positive vs negative reviews?
   - **RQ5.** Do ratings differ by skin type?

## 3. Methodology

### 3.1 Data source

Both brands run on **Shopify**, which publishes every store's product list as
structured data at `<store>/products.json`. Neither store holds the reviews itself:
both use a review app called **Okendo**. When a shopper opens a product page, the
page quietly requests that product's reviews from Okendo's server in the background.
By inspecting the page we found this address:

```
https://api.okendo.io/v1/stores/<brand's Okendo ID>/products/shopify-<product ID>/reviews
```

It returns reviews as JSON, 25 at a time, with a `nextUrl` pointing to the next batch.

### 3.2 Scraping (Days 2–5)

| Step | Script | What it does |
|---|---|---|
| Products | `src/scraper.py` | Downloads every product from both stores, page by page (250 per page). Skips items that are not real products: free samples, $0 hidden items, merch and gift cards. |
| Reviews | `src/reviews.py` | For each product, follows Okendo's `nextUrl` links to collect its reviews. Keeps only the fields needed for analysis. |

**Polite scraping:** the scraper waits 1 second between requests and identifies itself
with a User-Agent header.

**Sampling:** to keep run time reasonable and stop a few bestsellers with thousands of
reviews from dominating the data, at most **200 reviews per product** (the most recent)
were collected.

| Stage | Glow Recipe | KraveBeauty | Total |
|---|---|---|---|
| Items found in store | 127 | 33 | 160 |
| Real products kept | 104 | 32 | 136 |
| Products with at least one review | 97 | 23 | 120 |
| Reviews collected | | | 12,750 |
| After removing reviews shared between products | 7,903 | 2,134 | 10,037 |

Okendo shows the same review on related products (for example, a serum's review also
appears on a gift set containing it), so 2,713 repeated reviews were removed using
each review's unique ID.

### 3.3 Data cleaning (Day 6, `src/clean.py`)

| Cleaning step | Reviews removed |
|---|---|
| Empty reviews | 2 |
| Duplicates (same product, text and time) | 9 |
| Non-English reviews | 8 |
| **Clean dataset** | **10,018 reviews** |

Other cleaning steps:
- **Missing values.** Skin type was left blank in 53% of reviews and age range in 39%.
  These were labelled "Not given" rather than deleted, so the reviews still count in
  every other part of the analysis.
- **Multiple choices kept.** Reviewers can tick several skin types (e.g. "Dry,
  Sensitive"), so each reviewer is counted in **every** skin type they ticked.
  (An earlier version kept only the first one, which wrongly hid most sensitive-skin
  reviewers inside "Dry" or "Combination". Checking the results caught this.)
- **Dates.** Dates came in two formats (with and without milliseconds) and were parsed
  with the ISO 8601 standard, so no review lost its date. Store product types were inconsistent
  (e.g. a toner tagged "Serum"), so products were grouped into 12 categories using
  keywords in the product **name**.
- **Two versions of the text were kept:**
  - `text` (title + review, as written) for sentiment analysis, because VADER uses
    capitals, punctuation and emojis as clues.
  - `clean_text` (lowercase, no punctuation, links or numbers, no stopwords) for word
    counts and word clouds. Stopwords are common words like "the" and "is", plus
    words that appear in almost every review ("product", "skin", "face"). Many titles
    are auto-filled as "5 Stars", so "star(s)" was removed too.

### 3.4 Sentiment analysis method (Day 8, `src/sentiment.py`)

We used **VADER** (Valence Aware Dictionary and sEntiment Reasoner; Hutto & Gilbert,
2014). VADER is a rule-based model designed for short, informal social-media text:
- a dictionary gives each word a feeling score ("love" is positive, "awful" negative)
- rules adjust for boosters ("very good"), negation ("not good"), CAPITALS and "!!!"
- each text receives a **compound score** from **−1** (very negative) to **+1** (very positive)

Labels follow the standard thresholds: compound ≥ 0.05 is **Positive**, ≤ −0.05 is
**Negative**, and anything in between is **Neutral**.

VADER was chosen because it needs no training data, runs in seconds on 10,000 reviews,
and every score can be explained word by word.

## 4. Ethical considerations

- **Public data only.** Every review collected is visible to anyone who opens the
  product page. No login was used and no paywall was bypassed.
- **Privacy.** Reviewer names were deliberately **not saved**. The dataset contains only
  the review, rating and optional details the reviewer chose to share (skin type, age range).
- **Polite scraping.** A 1-second delay between requests and a 200-review cap per product
  kept the load on both websites low.
- **Purpose.** Educational analysis only. The data is not resold or used to contact anyone.

---

## 5. Results: Exploratory Data Analysis (Day 7, `src/eda.py`)

### 5.1 Dataset overview

| | Glow Recipe | KraveBeauty | All |
|---|---|---|---|
| Reviews | 7,888 | 2,130 | **10,018** |
| Products with reviews | 97 | 23 | 120 |
| Average star rating | **4.72** | **4.48** | 4.67 |

- Reviews span **July 2019 to October 2026**. Most are recent: 74% were posted in 2024–2026.
- **68%** of reviews come from verified buyers.
- The largest age group is **25–34** (2,107 reviews), followed by 35–44 (1,405).

![Reviews per brand](figures/eda_1_reviews_per_brand.png)

Glow Recipe has a much larger catalogue (97 reviewed products vs 23), so it supplies
79% of the reviews. To compare the brands fairly, the rest of the analysis uses
**percentages within each brand** rather than raw counts.

### 5.2 Star ratings are extremely positive

![Rating distribution](figures/eda_2_rating_distribution.png)

**82.4%** of all reviews are 5 stars and only **4.6%** are 1–2 stars. This "J-shaped"
distribution is typical of reviews on a brand's own website. Happy customers are
encouraged to review, and brands may moderate what appears.

KraveBeauty has noticeably more low ratings: **8%** of its reviews are 1–2 stars,
compared with **4%** for Glow Recipe, about twice the share.

### 5.3 Ratings by product category

![Rating by category](figures/eda_3_rating_by_category.png)

Apart from accessories and gifts (4.81, mostly keychains and pouches), **toners/exfoliants
(4.80)** are the best-rated skincare category, followed by moisturizers and sets (both 4.71).
**Eye care (4.32)** is the lowest-rated named category (only "Other" is lower, at 4.30),
followed by lip care (4.51) and body care (4.53). The only eye product,
Guava Vitamin C Bright-Eye Gel Cream, is pulled down mainly by packaging: **19 of its 34
reviews with 3 stars or fewer mention the pump**.

### 5.4 Ratings by skin type

![Rating by skin type](figures/eda_4_rating_by_skin_type.png)

Skin type makes **very little difference**: every skin type averages between **4.65
(normal) and 4.77 (dry)**, a gap of only 0.12 stars. Sensitive-skin reviewers (1,228
reviews) rate products 4.75 on average, as high as anyone. Only 47% of reviewers gave
their skin type, and a reviewer who ticked two types is counted in both groups.

### 5.5 Unhappy customers write more

![Review length](figures/eda_5_length_by_rating.png)

The median 5-star review is **24 words**; the median 2-star review is **50 words**,
more than twice as long. Satisfied customers write "Love it!", while dissatisfied
customers explain what went wrong. Negative reviews are therefore rare but
**information-rich**.

### 5.6 Reviews over time

![Reviews over time](figures/eda_6_reviews_over_time.png)

Glow Recipe receives far more reviews each month. Review volume jumps in some months
(e.g. February and July 2026 at roughly double the usual level), which may reflect
product launches or sales. The data does not show the cause.

### 5.7 Lowest-rated products

![Lowest rated products](figures/eda_7_lowest_rated_products.png)

Even the lowest-rated products (50+ reviews) average above 4.1 stars. **7 of the 10
lowest-rated products are KraveBeauty's**, led by the Plumptuous Lip Jelly Refill
(4.16) and the Barrier On-The-Go Mini Kit (4.18).

---

## 6. Results: Sentiment Analysis (Days 8–9, `src/sentiment.py`)

### 6.1 RQ1: Overall sentiment by brand

![Sentiment by brand](figures/sent_1_sentiment_by_brand.png)

| | Positive | Neutral | Negative |
|---|---|---|---|
| **All reviews** | 91.4% | 4.3% | 4.2% |
| Glow Recipe | 92.0% | 4.5% | 3.5% |
| KraveBeauty | 89.3% | 3.7% | **7.0%** |

The text sentiment confirms the star ratings: both brands are overwhelmingly positive,
but **negative reviews are twice as common for KraveBeauty** (7.0% vs 3.5%).

### 6.2 RQ2: Do the words match the stars?

![Score by rating](figures/sent_2_score_by_rating.png)

The average sentiment score rises steadily with the star rating, from +0.02 for 1 star
to +0.76 for 5 stars. So VADER and the stars **agree on the overall direction**.

![Rating vs sentiment](figures/sent_3_rating_vs_sentiment.png)

Overall, the text label matches the star group for **88.5%** of reviews. The table
shows where they disagree:
- **4–5 star reviews are almost always positive text (94%).** VADER is reliable for happy reviews.
- **1–2 star reviews are a different story.** Only **36%** are labelled negative,
  and 244 low-star reviews were labelled *positive*.

Reading these mismatched reviews shows **why**:

| Review (shortened) | Stars | VADER score | Why VADER got it wrong |
|---|---|---|---|
| "Itchy Face. Allergic Reaction. I love glow recipe though! I'm also not trying to bash…" | 1 | +0.36 | Polite: "love" outweighs the complaint |
| "Clogged my pores! At first I thought it was super nice…" | 1 | +0.86 | "Clogged pores" isn't in VADER's dictionary; "super nice" is |
| "Contains fragrance though it claims not to… gives me allergies with itching and stinging" | 1 | +0.47 | Skincare-specific problems not recognised |
| "Not a huge fan of the smell, but after a few minutes it doesn't bother me" | 5 | −0.35 | "Not a fan" and "bother" read as negative |
| "Yaaayyyy!!!" / "loveeee this oil cleanser!!" | 5 | ~0.0 (Neutral) | Stretched-out slang isn't in the dictionary |

**Conclusion for RQ2:** star ratings and text sentiment measure slightly different things.
Unhappy skincare customers tend to be **polite and balanced**: they praise the brand or
another product while describing a bad reaction. A general-purpose model like VADER
misses domain words such as "breakout", "clogged" and "purging". **For low-star reviews,
the star rating is the more reliable signal, and the text is best used to find out
*why* the customer was unhappy.**

### 6.3 RQ3: Most loved and most complained-about products

Among products with 20+ reviews:

| Most loved (highest average sentiment) | Brand | Reviews | Avg score |
|---|---|---|---|
| Glow Recipe x Buldak Glass Balm Lip Duo | Glow Recipe | 25 | +0.97 |
| Watermelon Glass Skin Essentials Kit | Glow Recipe | 64 | +0.94 |
| Toner Pad Collection Kit | Glow Recipe | 24 | +0.93 |
| Best of Glow Hues Kit | Glow Recipe | 50 | +0.93 |
| Mini Glass Balm Lip Treatment Collection | Glow Recipe | 34 | +0.92 |

| Most complaints (highest % negative reviews) | Brand | Reviews | % negative |
|---|---|---|---|
| Oil La La | KraveBeauty | 103 | 13.6% |
| Great Body Relief | KraveBeauty | 200 | 10.5% |
| Clear Skin Essentials Kit | Glow Recipe | 72 | 9.7% |
| Fall Reset Kit | KraveBeauty | 44 | 9.1% |
| Makeup Re-Wined | KraveBeauty | 155 | 9.0% |

All five most-loved products are **gift sets, kits or collections**, where customers
review the overall value and experience. Four of the five most-complained-about products
are **KraveBeauty's**, including a facial oil (Oil La La) and an oil cleanser (Makeup Re-Wined).

### 6.4 RQ4: Words and topics

![Top words](figures/sent_5_top_words.png)

| Word cloud: positive reviews | Word cloud: negative reviews |
|---|---|
| ![Positive cloud](figures/sent_6_wordcloud_positive.png) | ![Negative cloud](figures/sent_7_wordcloud_negative.png) |

- **Positive reviews** talk about the experience: *love, great, amazing, perfect,
  soft, smells, routine, makeup*.
- **Negative reviews** talk about specific problems: *smell, dry, bottle, packaging,
  sensitive, acne, disappointed*. "Love" still appears in negative reviews, which
  supports the politeness finding in 6.2.

To measure complaint topics directly, each negative review was searched for keyword
groups:

![Complaints](figures/sent_8_complaints.png)

| Complaint topic | All negative (n = 422) | Glow Recipe (n = 273) | KraveBeauty (n = 149) |
|---|---|---|---|
| Irritation / burning | **20%** | 16% | **26%** |
| Smell / fragrance | 18% | 17% | 21% |
| Breakouts / acne | 17% | 13% | **25%** |
| Packaging (pump, bottle, leaks) | 17% | 16% | 19% |
| Sticky / greasy feel | 8% | 7% | 9% |
| Price / value | 6% | 7% | 5% |
| No results | 6% | 7% | 5% |

**Skin reactions** (irritation and breakouts) are the biggest problem, and they are far
more common in KraveBeauty's negative reviews (26% and 25%) than in Glow Recipe's
(16% and 13%). **Smell** is the second biggest complaint, even though "smells" is also
one of the top *positive* words. Fragrance divides customers.

### 6.5 RQ5: Skin type

![Positive by skin type](figures/sent_4_positive_by_skin_type.png)

The sentiment results agree with the star ratings in 5.4: the share of positive reviews
is between **93% and 96% for every skin type**. Oily skin is slightly the most positive
(96.4%), and sensitive (93.3%) and normal (93.4%) skin are slightly the least. **The answer
to RQ5 is that skin type barely matters.** Even though irritation is the most common
complaint, sensitive-skin reviewers are not noticeably less satisfied overall.

---

## 7. Discussion

**Key findings**
1. Customers of both brands are very satisfied: an average of 4.67★ and 91% positive text.
2. Glow Recipe outperforms KraveBeauty on the main measures: higher ratings, half the
   share of negative reviews, and fewer reports of skin reactions. Glow Recipe's
   complaints mention price and "no results" slightly more often (7% vs 5%).
3. Unhappy customers write almost twice as much as happy ones (median 48 words for
   1–2★ vs 26 for 4–5★), so the few negative reviews hold most of the useful feedback.
4. The main problems are **irritation, fragrance, breakouts and packaging**.
5. Skin type makes little difference: every skin type averages 4.65–4.77★.
6. VADER is accurate for positive reviews but misses many negative ones, because
   unhappy skincare customers are polite and use domain-specific language.

**Limitations**
- **Positivity bias.** Reviews come from the brands' own websites, where happy customers
  are encouraged to review and brands may filter content. Independent sites
  (e.g. Sephora, Reddit) might be more critical.
- **Sampling.** The 200-reviews-per-product cap means bestsellers are represented by
  their most recent reviews only.
- **Unbalanced brands.** Glow Recipe supplies 79% of the reviews; percentages were used
  to compare fairly, but KraveBeauty's results rest on fewer reviews.
- **VADER's limits.** It does not understand sarcasm, mixed opinions, or skincare words
  like "purging" or "clogged pores".
- **Missing details.** Only 47% of reviewers gave a skin type, so skin-type results
  cover about half the data.
- **Incentivised reviews.** Some reviews may come from free samples or giveaways, which
  tend to be more positive. This field was not collected, so it could not be checked.
- **One point in time.** The data was collected once (October 2026).

## 8. Conclusion and future work

This project showed that web scraping can turn two brands' websites into a dataset of
10,000+ customer reviews. EDA and sentiment analysis can then summarise that data into
clear, evidence-based findings. Both brands are well liked, but Glow Recipe is rated
higher. The clearest opportunities for both are **fewer skin reactions** (irritation and
breakouts, especially for KraveBeauty), **fragrance** that divides customers, and
**better packaging** (pumps, bottles and leaks).

**Future work**
- Use a transformer model fine-tuned on product reviews (e.g. a BERT-based model),
  or train one on these star ratings, to fix VADER's blind spots.
- Add skincare-specific words ("breakout", "purging", "clogged") to VADER's dictionary.
- Use topic modelling (LDA) to discover complaint topics automatically.
- Scrape independent review sites to compare against the brands' own pages.
- Re-run the scraper monthly to track how sentiment changes after product launches.

## 9. References

- Hutto, C.J. & Gilbert, E. (2014). *VADER: A Parsimonious Rule-based Model for
  Sentiment Analysis of Social Media Text.* Proceedings of the Eighth International
  AAAI Conference on Weblogs and Social Media (ICWSM-14).
- Glow Recipe online store: https://www.glowrecipe.com
- KraveBeauty online store: https://www.kravebeauty.com
- Okendo (customer review platform): https://www.okendo.io
- Python libraries: requests, pandas, matplotlib, vaderSentiment, wordcloud.

## Appendix: How to reproduce

```bash
pip install -r requirements.txt
python src/scraper.py      # 1. product lists       -> data/raw/*_products.json
python src/reviews.py      # 2. customer reviews    -> data/raw/reviews.csv
python src/clean.py        # 3. cleaning            -> data/processed/reviews_clean.csv
python src/eda.py          # 4. EDA charts          -> reports/figures/eda_*.png
python src/sentiment.py    # 5. sentiment + charts  -> reports/figures/sent_*.png
```
