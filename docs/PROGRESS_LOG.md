# Daily Progress Log

## Day 1 — Project setup

**What I did**

- Chose the topic: international skincare brands.
- Checked which brands expose a public Shopify `products.json` feed.
  Glow Recipe, KraveBeauty and Summer Fridays work; Youth To The People returns 404.
- Created the GitHub repository and folder structure.
- Wrote the README, requirements.txt and .gitignore.

**What I learned**

- What web scraping is and how a request → HTML/JSON → extract → save pipeline works.
- Shopify stores often publish their catalog as JSON, which is easier than parsing HTML.

**Next**

- Day 2: write the scraper for one brand.

## Day 2 — First scraper

**What I did**

- Wrote src/scraper.py to download all Glow Recipe products from /products.json.
- Handled pagination (250 products per page) and added a 1-second delay between requests.
- Saved the raw data to data/raw/glow_recipe.json (126 products).
- Project scope updated: the focus is now customer reviews, evaluated with
  EDA (Exploratory Data Analysis) and Sentiment Analysis.
- Found that Glow Recipe and KraveBeauty both use the Okendo review app,
  which provides reviews as clean data. Summer Fridays was dropped because
  its review source could not be identified.

**What I learned**

- How to send a request with the requests library and check the status code.
- How Shopify splits products into pages and how a while loop collects them all.
- Found free samples ($0.38) and hidden products ($0.00) that will need cleaning later.

**Next**

- Day 3: get the product lists for both brands.

## Day 3 — Product lists for both brands

**What I did**

- Updated src/scraper.py to loop over a list of brands (Glow Recipe and KraveBeauty).
- Added a filter that skips items that aren't real products: free samples,
  $0 hidden items, merch and gift cards.
- Saved one file per brand: data/raw/glow_recipe_products.json (104 products,
  23 non-products skipped)
  and data/raw/kravebeauty_products.json (32 products,
  1 non-product skipped).
- Stored each brand's Okendo review ID in the script, ready for Day 4.

**What I learned**

- How to use a list of dictionaries so one script can handle many websites.
- Why filtering matters: samples and hidden items would distort the analysis.

**Next**

- Day 4: write the review scraper and test it on one product.

## Day 4 — Review scraper (one product)

**What I did**

- Found where the reviews come from: both brands use the Okendo review app, which
  serves reviews as JSON at api.okendo.io/v1/stores/<store id>/products/shopify-<product id>/reviews
- Wrote src/reviews.py and tested it on one product
  (Watermelon Glow Niacinamide Dew Drops), collecting 100 reviews.
- Kept only the useful fields: rating, title, review text, date, skin type,
  age range, skin concern, verified buyer, recommended, helpful votes.
- Did not save reviewer names, to protect customer privacy.
- Saved the result to data/raw/sample_reviews.json.

**What I learned**

- Many websites load reviews from a separate service in the background.
- How "nextUrl" pagination works: each answer tells you where the next batch is.
- - First look at star ratings: 90 five-star reviews out of 100 (90 five, 9 four,
    0 three, 1 two, 0 one). Reviews are very positive, which matters for the analysis.
- Some reviewers leave skin type and age blank, so those fields will have gaps.
  **Next**
- Day 5: collect reviews for every product of both brands.
