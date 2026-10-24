"""
Day 5: Review scraper for ALL products of BOTH brands.

What's new since Day 4:
- Loops over both brands and every product saved on Day 3
- Saves everything into ONE table: data/raw/reviews.csv (one row per review)
- Keeps going if one product fails, instead of crashing
- Collects up to 200 reviews per product (see note below)

Why 200 per product?
Some bestsellers have thousands of reviews while most products have a few
dozen. Taking at most 200 from each product keeps the run time reasonable
(~15 minutes) and stops a few bestsellers from dominating the analysis.
This is called "sampling" and should be mentioned in the report.

Where the reviews come from:
Both brands use the Okendo review app, which serves reviews as JSON at:
  https://api.okendo.io/v1/stores/<brand's Okendo ID>/products/shopify-<product ID>/reviews

Privacy: reviewer names are NOT saved.

Run it from the project folder:
    python src/reviews.py
"""

import json
import time
import requests
import pandas as pd

# ---- Settings ----
OKENDO_API = "https://api.okendo.io/v1"
BRANDS = [
    {"name": "glow_recipe", "okendo_id": "41915e47-fb72-4109-81cf-25e1e3b73626"},
    {"name": "kravebeauty", "okendo_id": "15b88ae5-59c1-4ae2-9f28-d45cc3ea4d35"},
]
MAX_REVIEWS_PER_PRODUCT = 200
DELAY_SECONDS = 1
OUTPUT_FILE = "data/raw/reviews.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (university project: skincare review analysis)"
}


def load_products(brand_name):
    """Read the product list we saved on Day 3."""
    with open(f"data/raw/{brand_name}_products.json", encoding="utf-8") as f:
        return json.load(f)


def get_attribute(review, name):
    """Get a reviewer detail such as 'Skin Type' or 'Age Range' (blank if missing)."""
    attributes = review.get("reviewer", {}).get("attributes", []) or []
    for attr in attributes:
        if attr.get("title", "").lower() == name.lower():
            value = attr.get("value", "")
            if isinstance(value, list):          # some answers allow several choices
                value = ", ".join(str(v) for v in value)
            return value
    return ""


def simplify_review(review, product, brand_name):
    """Keep only the fields we need. Reviewer names are left out on purpose."""
    return {
        "review_id": review.get("reviewId", ""),
        "brand": brand_name,
        "product_id": product["id"],
        "product": product["title"],
        "product_type": product.get("product_type", ""),
        "rating": review.get("rating"),
        "title": review.get("title", ""),
        "body": review.get("body", ""),
        "date": review.get("dateCreated", ""),
        "skin_type": get_attribute(review, "Skin Type"),
        "age_range": get_attribute(review, "Age Range"),
        "skin_concern": get_attribute(review, "Skin Concern"),
        "verified": review.get("reviewer", {}).get("isVerified", False),
        "recommended": review.get("isRecommended"),
        "helpful_votes": review.get("helpfulCount", 0),
    }


def scrape_reviews(product, brand):
    """Download reviews for one product, following nextUrl page by page."""
    url = (f"{OKENDO_API}/stores/{brand['okendo_id']}/products/"
           f"shopify-{product['id']}/reviews?limit=25")
    reviews = []

    while url and len(reviews) < MAX_REVIEWS_PER_PRODUCT:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"    Error: status {response.status_code}")
            break

        data = response.json()
        for r in data.get("reviews", []):
            reviews.append(simplify_review(r, product, brand["name"]))

        next_url = data.get("nextUrl")
        url = OKENDO_API + next_url if next_url else None
        time.sleep(DELAY_SECONDS)

    return reviews[:MAX_REVIEWS_PER_PRODUCT]


if __name__ == "__main__":
    all_reviews = []

    for brand in BRANDS:
        products = load_products(brand["name"])
        print(f"\n=== {brand['name']}: {len(products)} products ===")

        for i, product in enumerate(products, start=1):
            try:
                reviews = scrape_reviews(product, brand)
            except Exception as error:      # one bad product shouldn't stop the whole run
                print(f"  [{i}/{len(products)}] {product['title']}: skipped ({error})")
                continue

            all_reviews.extend(reviews)
            print(f"  [{i}/{len(products)}] {product['title']}: {len(reviews)} reviews")

    # Put everything in a table and remove reviews that appear twice
    # (Okendo sometimes shows the same review on related products, e.g. sets)
    df = pd.DataFrame(all_reviews)
    before = len(df)
    df = df.drop_duplicates(subset="review_id")
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\nCollected {before} reviews, removed {before - len(df)} duplicates")
    print(f"Saved {len(df)} reviews to {OUTPUT_FILE}")

    print("\nReviews per brand:")
    print(df["brand"].value_counts().to_string())

    print("\nStar ratings:")
    print(df["rating"].value_counts().sort_index(ascending=False).to_string())
