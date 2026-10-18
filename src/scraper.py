"""
Day 2: Scraper for ONE skincare brand (Glow Recipe).

How it works:
1. Shopify stores publish their products at <store>/products.json
2. We request that page (250 products at a time, page by page)
3. We keep going until a page comes back empty
4. We save everything to data/raw/glow_recipe.json

Run it from the project folder:
    python src/scraper.py
"""

import json   # to save the data as a .json file
import time   # to wait between requests (polite scraping)
import requests  # to download web pages

# ---- Settings ----
STORE_URL = "https://www.glowrecipe.com"
BRAND_NAME = "glow_recipe"
OUTPUT_FILE = f"data/raw/{BRAND_NAME}.json"
PRODUCTS_PER_PAGE = 250   # the maximum Shopify allows per page
DELAY_SECONDS = 1         # wait 1 second between pages so we don't overload the site

# Tell the website who we are (some sites block requests without this)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (university project: skincare price analysis)"
}


def get_page(page_number):
    """Download one page of products and return them as a Python list."""
    url = f"{STORE_URL}/products.json?limit={PRODUCTS_PER_PAGE}&page={page_number}"
    print(f"Downloading page {page_number}: {url}")

    response = requests.get(url, headers=HEADERS, timeout=30)

    # 200 means "OK". Anything else means something went wrong.
    if response.status_code != 200:
        print(f"  Error: the website answered with status {response.status_code}")
        return []

    data = response.json()          # turn the JSON text into a Python dictionary
    return data.get("products", []) # the products are stored under the key "products"


def scrape_all_products():
    """Keep downloading pages until there are no more products."""
    all_products = []
    page = 1

    while True:
        products = get_page(page)

        if len(products) == 0:   # an empty page means we've reached the end
            break

        all_products.extend(products)
        print(f"  Found {len(products)} products (total so far: {len(all_products)})")

        page += 1
        time.sleep(DELAY_SECONDS)

    return all_products


def save_to_file(products, filename):
    """Save the list of products to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(products)} products to {filename}")


# This part runs when you type: python src/scraper.py
if __name__ == "__main__":
    print(f"Scraping {STORE_URL} ...\n")
    products = scrape_all_products()

    if products:
        save_to_file(products, OUTPUT_FILE)

        # Show a small preview so we can check the data looks right
        print("\nFirst 5 products:")
        for p in products[:5]:
            price = p["variants"][0]["price"]
            print(f"  - {p['title']}  (${price})")
    else:
        print("No products found.")
