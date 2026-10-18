"""
Day 3: Product scraper for BOTH brands.

What's new since Day 2:
- A list of brands instead of one store, so one script scrapes them all
- Skips items that aren't real products (free samples, $0 hidden items,
  gift cards, merch)
- Saves one file per brand: data/raw/<brand>_products.json

Why we need products: every customer review belongs to a product ID,
so this list tells the review scraper (Day 4) which products to look up.

Run it from the project folder:
    python src/scraper.py
"""

import json      # to save the data as a .json file
import time      # to wait between requests (polite scraping)
import requests  # to download web pages

# ---- Settings ----
# Each brand has its store URL and its Okendo review ID (used from Day 4).
BRANDS = [
    {
        "name": "glow_recipe",
        "url": "https://www.glowrecipe.com",
        "okendo_id": "41915e47-fb72-4109-81cf-25e1e3b73626",
    },
    {
        "name": "kravebeauty",
        "url": "https://www.kravebeauty.com",
        "okendo_id": "15b88ae5-59c1-4ae2-9f28-d45cc3ea4d35",
    },
]

PRODUCTS_PER_PAGE = 250   # the maximum Shopify allows per page
DELAY_SECONDS = 1         # wait 1 second between requests

# Product types that are not real skincare products
SKIP_TYPES = ["sachet", "sample", "merch", "gift card", "gift cards"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (university project: skincare review analysis)"
}


def get_page(store_url, page_number):
    """Download one page of products and return them as a Python list."""
    url = f"{store_url}/products.json?limit={PRODUCTS_PER_PAGE}&page={page_number}"
    print(f"  Downloading page {page_number}")

    response = requests.get(url, headers=HEADERS, timeout=30)

    if response.status_code != 200:
        print(f"  Error: the website answered with status {response.status_code}")
        return []

    return response.json().get("products", [])


def scrape_all_products(store_url):
    """Keep downloading pages until there are no more products."""
    all_products = []
    page = 1

    while True:
        products = get_page(store_url, page)
        if len(products) == 0:   # empty page = we've reached the end
            break
        all_products.extend(products)
        page += 1
        time.sleep(DELAY_SECONDS)

    return all_products


def is_real_product(product):
    """Return True if this is a real product a customer would buy and review."""
    product_type = (product.get("product_type") or "").lower()
    title = product.get("title", "").lower()

    # 1. Skip samples, merch and gift cards
    if product_type in SKIP_TYPES or "gift card" in title:
        return False

    # 2. Skip items where every variant costs less than $1 (free samples, hidden items)
    prices = [float(v["price"]) for v in product.get("variants", [])]
    if not prices or max(prices) < 1:
        return False

    return True


def save_to_file(products, filename):
    """Save the list of products to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


# This part runs when you type: python src/scraper.py
if __name__ == "__main__":
    for brand in BRANDS:
        print(f"\nScraping {brand['name']} ({brand['url']}) ...")

        products = scrape_all_products(brand["url"])
        real_products = [p for p in products if is_real_product(p)]
        skipped = len(products) - len(real_products)

        filename = f"data/raw/{brand['name']}_products.json"
        save_to_file(real_products, filename)

        print(f"  Found {len(products)} items, skipped {skipped} non-products")
        print(f"  Saved {len(real_products)} products to {filename}")

    print("\nDone!")
