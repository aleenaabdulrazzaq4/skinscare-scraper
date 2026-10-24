"""
Day 6: Clean the review data.

Input:  data/raw/reviews.csv          (straight from the scraper)
Output: data/processed/reviews_clean.csv

Cleaning steps:
1. Remove reviews with no text, and duplicate reviews
2. Keep English reviews only
3. Fill in missing details (skin type, age) with "Not given"
4. Simplify messy values (skin types, product category)
5. Make two text columns:
   - "text":       title + review, as written (used for sentiment analysis,
                   because VADER understands capitals, "!!!" and emojis)
   - "clean_text": lowercase, no punctuation/numbers/links, no stopwords
                   (used for word counts and word clouds)
6. Add helper columns: review length, year-month, brand display name

Run it from the project folder:
    python src/clean.py
"""

import re
import pandas as pd
from wordcloud import STOPWORDS   # a ready-made list of common English words

INPUT_FILE = "data/raw/reviews.csv"
OUTPUT_FILE = "data/processed/reviews_clean.csv"

BRAND_LABELS = {"glow_recipe": "Glow Recipe", "kravebeauty": "KraveBeauty"}

# Extra words that appear in almost every review and tell us nothing
EXTRA_STOPWORDS = {
    "product", "products", "skin", "use", "used", "using", "will", "one", "really",
    "also", "get", "got", "im", "ive", "dont", "doesnt", "didnt", "cant", "it's",
    "would", "even", "much", "make", "makes", "made", "day", "days", "time", "go",
    "glow", "recipe", "krave", "kravebeauty", "glowrecipe", "watermelon", "just",
    "still", "thing", "bit", "way", "since", "first", "now", "us", "well",
    "face", "feel", "feels", "felt",
    "star", "stars",   # many titles are auto-filled as "5 Stars" / "1 Star"
}
STOP = set(w.replace("'", "") for w in STOPWORDS) | EXTRA_STOPWORDS

SKIN_TYPES = ["Combination", "Oily", "Dry", "Normal", "Sensitive"]

# Product category from keywords in the product name / type (first match wins)
CATEGORIES = [
    ("Accessories / gifts", ["keychain", "tote", "pillow pouch", "puffy pouch", "gift box", "birthday gift"]),
    ("Body care", ["body"]),
    ("Mask", ["sheet mask"]),
    ("Set / Kit", ["set", "kit", "duo", "trio", "bundle", "vault", "calendar", "collection", "routine", "double cleanse"]),
    ("Cleanser", ["cleanser", "cleanse", "wash", "makeup re"]),
    ("Sunscreen", ["spf", "sunscreen"]),
    ("Eye care", ["eye"]),
    ("Lip care", ["lip"]),
    ("Mask", ["mask", "sleeping"]),
    ("Serum / treatment", ["serum", "drops", "dewy flush", "mucin", "relief", "ampoule", "treatment",
                           "retinal", "retinol", "tamanu", "oil la la"]),
    ("Toner / exfoliant", ["toner", "pads", "essence", "mist", "aha"]),
    ("Moisturizer", ["moistur", "cream", "jelly", "gel", "lotion", "butter"]),
]


def is_english(text):
    """Rough check: mostly plain English letters (A-Z)."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for c in letters if c.isascii())
    return ascii_letters / len(letters) >= 0.9


def skin_types(value):
    """'Dry, Sensitive' -> 'Dry;Sensitive'. Reviewers can tick several skin types,
    so we keep ALL of them (a reviewer is counted in every group they ticked)."""
    if not isinstance(value, str) or not value.strip():
        return "Not given"
    found = [skin for skin in SKIN_TYPES if skin.lower() in value.lower()]
    return ";".join(found) if found else "Other"


def product_category(row):
    """Group product names into a few clear categories.
    The product NAME is checked first; the store's own product type is only a
    fallback, because it is sometimes wrong (e.g. a toner tagged as "Serum")."""
    for text in [str(row["product"]).lower(), str(row["product_type"]).lower()]:
        for category, keywords in CATEGORIES:
            if any(k in text for k in keywords):
                return category
    return "Other"


def clean_text(text):
    """Lowercase, remove links/numbers/punctuation/emojis, remove stopwords."""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)   # links
    text = text.replace("'", "").replace("’", "")   # don't -> dont
    text = re.sub(r"[^a-z\s]", " ", text)                # keep letters only
    words = [w for w in text.split() if w not in STOP and len(w) > 2]
    return " ".join(words)


if __name__ == "__main__":
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} reviews")
    steps = []

    # 1. Empty and duplicate reviews
    df["title"] = df["title"].fillna("").astype(str)
    df["body"] = df["body"].fillna("").astype(str)
    before = len(df)
    df = df[df["body"].str.strip() != ""]
    steps.append(("Empty reviews removed", before - len(df)))

    before = len(df)
    df = df.drop_duplicates(subset="review_id")
    # same product + same text + same time = the same review posted twice
    # (two people both writing "Love it!" are NOT duplicates, so date is included)
    df = df.drop_duplicates(subset=["product", "body", "date"])
    steps.append(("Duplicate reviews removed", before - len(df)))

    # 2. English only
    df["text"] = (df["title"] + ". " + df["body"]).str.strip(". ")
    before = len(df)
    df = df[df["text"].apply(is_english)]
    steps.append(("Non-English reviews removed", before - len(df)))

    # 3 + 4. Missing values and simpler categories
    print("\nMissing values before filling:")
    for col in ["skin_type", "age_range", "skin_concern"]:
        missing = df[col].isna().sum() + (df[col].astype(str).str.strip() == "").sum()
        print(f"  {col}: {missing} ({missing / len(df):.0%})")

    df["skin_types"] = df["skin_type"].apply(skin_types)
    df["age_range"] = df["age_range"].fillna("Not given").replace("", "Not given")
    df["skin_concern"] = df["skin_concern"].fillna("Not given").replace("", "Not given")
    df["product_type"] = df["product_type"].fillna("")
    df["category"] = df.apply(product_category, axis=1)
    df["brand_name"] = df["brand"].map(BRAND_LABELS)

    # 5. Text for word analysis
    df["clean_text"] = df["text"].apply(clean_text)

    # 6. Helper columns
    df["word_count"] = df["body"].str.split().str.len()
    # dates come in two formats (with and without milliseconds); ISO8601 reads both
    df["date"] = pd.to_datetime(df["date"], format="ISO8601", utc=True)
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["rating"] = df["rating"].astype(int)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\nCleaning steps:")
    for step, n in steps:
        print(f"  {step}: {n}")
    print(f"\nSaved {len(df)} clean reviews to {OUTPUT_FILE}")
    print("\nExample of cleaned text:")
    example = df.iloc[0]
    print(f"  Before: {example['text'][:120]}")
    print(f"  After:  {example['clean_text'][:120]}")
