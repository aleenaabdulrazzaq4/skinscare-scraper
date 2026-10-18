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
