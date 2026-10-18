"""
Day 4: Review scraper, tested on ONE product.

Where the reviews come from:
Both brands use a review app called Okendo. When you open a product page,
the page quietly asks Okendo for the reviews at a link like:

  https://api.okendo.io/v1/stores/<brand's Okendo ID>/products/shopify-<product ID>/reviews

That link returns the reviews as clean JSON (like products.json did).
Each answer contains up to 25 reviews plus a "nextUrl" that points to the
next batch, so we keep following nextUrl until there isn't one.

Privacy: we do NOT save reviewer names, only the review and its details.

Run it from the project folder:
    python src/reviews.py
"""

import json
import time
import requests

# ---- Settings ----
OKENDO_API = "https://api.okendo.io/v1"
BRAND_NAME = "glow_recipe"
OKENDO_ID = "41915e47-fb72-4109-81cf-25e1e3b73626"      # Glow Recipe's Okendo ID
PRODUCTS_FILE = "data/raw/glow_recipe_products.json"
TEST_PRODUCT = "watermelon-glow-niacinamide-dew-drops"  # the product we test on
MAX_REVIEWS = 100       # just a test today; Day 5 collects everything
DELAY_SECONDS = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (university project: skincare review analysis)"
}


def load_products(filename):
    """Read the product list we saved on Day 3."""
    with open(filename, encoding="utf-8") as f:
        return json.load(f)


def find_product(products, handle):
    """Find a product by its handle (the name in its web address)."""
    for p in products:
        if p["handle"] == handle:
            return p
    print(f"'{handle}' not found, using the first product instead.")
    return products[0]


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


def simplify_review(review, product):
    """Keep only the fields we need. Reviewer names are left out on purpose."""
    return {
        "brand": BRAND_NAME,
        "product_id": product["id"],
        "product": product["title"],
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


def scrape_reviews(product, max_reviews):
    """Download reviews for one product, following nextUrl page by page."""
    url = (f"{OKENDO_API}/stores/{OKENDO_ID}/products/"
           f"shopify-{product['id']}/reviews?limit=25")
    reviews = []

    while url and len(reviews) < max_reviews:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"  Error: status {response.status_code}")
            break

        data = response.json()
        batch = data.get("reviews", [])
        reviews.extend(simplify_review(r, product) for r in batch)
        print(f"  Got {len(batch)} reviews (total: {len(reviews)})")

        # nextUrl looks like "/stores/.../reviews?...", so add the API address in front
        next_url = data.get("nextUrl")
        url = OKENDO_API + next_url if next_url else None
        time.sleep(DELAY_SECONDS)

    return reviews[:max_reviews]


if __name__ == "__main__":
    products = load_products(PRODUCTS_FILE)
    product = find_product(products, TEST_PRODUCT)
    print(f"Scraping reviews for: {product['title']}\n")

    reviews = scrape_reviews(product, MAX_REVIEWS)

    output = "data/raw/sample_reviews.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(reviews)} reviews to {output}")

    # Quick look at the data
    print("\nFirst 3 reviews:")
    for r in reviews[:3]:
        stars = "*" * int(r["rating"] or 0)
        print(f"\n  {stars}  {r['title']}")
        print(f"  Skin type: {r['skin_type'] or '-'}  |  Age: {r['age_range'] or '-'}")
        print(f"  \"{r['body'][:150]}\"")

    # Count how many reviews have each star rating
    print("\nStar ratings:")
    for star in [5, 4, 3, 2, 1]:
        count = sum(1 for r in reviews if r["rating"] == star)
        print(f"  {star} stars: {count}")
