"""
Day 8-9: Sentiment analysis of the customer reviews, plus word analysis.

Sentiment analysis = working out whether a piece of text is positive, negative
or neutral. We use VADER (Valence Aware Dictionary and sEntiment Reasoner):
- It has a dictionary of words with a feeling score ("love" +, "awful" -)
- It understands boosters ("very good"), negation ("not good"),
  CAPITALS ("GREAT") and punctuation ("great!!!")
- It gives each text a "compound" score from -1 (very negative) to +1 (very positive)
- Common rule: compound >= 0.05 -> Positive, <= -0.05 -> Negative, otherwise Neutral

Then we compare the text's sentiment with the star rating, and look at which
words appear most in positive vs negative reviews.

Input:  data/processed/reviews_clean.csv
Output: data/processed/reviews_sentiment.csv
        charts in reports/figures/ (sent_*.png)
        key numbers in reports/sentiment_summary.json

Run it from the project folder:
    python src/sentiment.py
"""

import json
import re
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from wordcloud import WordCloud

import style

INPUT_FILE = "data/processed/reviews_clean.csv"
OUTPUT_FILE = "data/processed/reviews_sentiment.csv"
SUMMARY_FILE = "reports/sentiment_summary.json"
MIN_REVIEWS = 20

# Common skincare complaints to look for in negative reviews
COMPLAINTS = {
    "Breakouts / acne": ["broke me out", "breakout", "break out", "broke out", "pimple", "acne", "clogged"],
    "Irritation / burning": ["irritat", "burn", "sting", "itch", "rash", "redness", "allerg", "react"],
    "Sticky / greasy feel": ["sticky", "greasy", "tacky", "too oily", "heavy"],
    "Smell / fragrance": ["smell", "scent", "fragrance", "odor"],
    "Drying": ["drying", "dried out", "dries out", "too dry", "made my skin dry", "dry patches"],
    "Price / value": ["expensive", "price", "overpriced", "not worth", "waste of money", "money"],
    "Packaging": ["packaging", "pump", "bottle", "leak", "broken", "dropper"],
    "Pilling": ["pill", "pilling"],
    "No results": ["no difference", "didnt do", "didn't do", "nothing", "no results", "not work"],
}

style.setup()
BRANDS = list(style.BRAND_COLORS)


def label_for(score):
    if score >= 0.05:
        return "Positive"
    if score <= -0.05:
        return "Negative"
    return "Neutral"


def chart_sentiment_by_brand(df):
    """100% stacked bar: share of positive / neutral / negative reviews per brand."""
    share = pd.crosstab(df["brand_name"], df["sentiment"], normalize="index") * 100
    share = share.reindex(index=BRANDS, columns=style.SENTIMENT_ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 3))
    left = pd.Series(0.0, index=share.index)
    for label in style.SENTIMENT_ORDER:
        bars = ax.barh(share.index, share[label], left=left, height=0.5,
                       color=style.SENTIMENT_COLORS[label], label=label,
                       edgecolor=style.SURFACE, linewidth=2)
        for bar, value in zip(bars, share[label]):
            if value >= 3:   # only label segments big enough to read
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                        f"{value:.0f}%", ha="center", va="center", fontsize=10,
                        color="#0b0b0b" if label == "Neutral" else "white")
        left += share[label]
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.set_title("Sentiment of review text by brand")
    ax.set_xlabel("Share of reviews (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3)
    ax.grid(visible=False)
    style.save(fig, "sent_1_sentiment_by_brand")
    return share


def chart_score_by_rating(df):
    """Average VADER score for each star rating: do words and stars agree?"""
    avg = df.groupby("rating")["compound"].mean().reindex([1, 2, 3, 4, 5])
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [style.SENTIMENT_COLORS["Positive"] if v >= 0.05 else
              style.SENTIMENT_COLORS["Negative"] if v <= -0.05 else
              style.SENTIMENT_COLORS["Neutral"] for v in avg.values]
    bars = ax.bar(avg.index, avg.values, width=0.55, color=colors)
    for bar, v in zip(bars, avg.values):
        ax.annotate(f"{v:+.2f}", (bar.get_x() + bar.get_width() / 2, v),
                    xytext=(0, 3 if v >= 0 else -12), textcoords="offset points",
                    ha="center", fontsize=9, color=style.INK_SECONDARY)
    ax.axhline(0, color=style.AXIS, linewidth=1)
    ax.set_ylim(-1, 1)
    ax.set_xticks([1, 2, 3, 4, 5], ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"])
    ax.set_title("Average sentiment score by star rating")
    ax.set_ylabel("Average VADER compound score\n(-1 negative ... +1 positive)")
    ax.grid(axis="x", visible=False)
    style.save(fig, "sent_2_score_by_rating")
    return avg


def chart_rating_vs_sentiment(df):
    """Heatmap-style table: star rating (rows) vs text sentiment (columns), row %."""
    table = pd.crosstab(df["rating"], df["sentiment"], normalize="index") * 100
    table = table.reindex(index=[5, 4, 3, 2, 1], columns=style.SENTIMENT_ORDER, fill_value=0)
    counts = pd.crosstab(df["rating"], df["sentiment"]).reindex(
        index=[5, 4, 3, 2, 1], columns=style.SENTIMENT_ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.imshow(table.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            v = table.values[i, j]
            ax.text(j, i, f"{v:.0f}%\n({counts.values[i, j]})", ha="center", va="center",
                    fontsize=9, color="white" if v > 55 else style.INK)
    ax.set_xticks(range(3), style.SENTIMENT_ORDER)
    ax.set_yticks(range(5), [f"{s} stars" if s > 1 else "1 star" for s in table.index])
    ax.set_xlabel("Sentiment of the review text (VADER)")
    ax.set_title("Star rating vs text sentiment")
    ax.grid(visible=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    style.save(fig, "sent_3_rating_vs_sentiment")
    return table


def by_skin_type(df):
    """One row per (review, skin type ticked), so 'Dry;Sensitive' counts for both."""
    out = df.assign(skin_type_group=df["skin_types"].str.split(";")).explode("skin_type_group")
    return out[~out["skin_type_group"].isin(["Not given", "Other"])]


def chart_group_sentiment(df, column, title, filename):
    groups = df[df[column] != "Not given"].groupby(column).agg(
        positive=("sentiment", lambda s: (s == "Positive").mean() * 100),
        count=("sentiment", "size"))
    groups = groups[groups["count"] >= MIN_REVIEWS].sort_values("positive")
    if groups.empty:
        return groups
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(groups) + 1.5))
    bars = ax.barh(groups.index, groups["positive"], height=0.55,
                   color=style.SENTIMENT_COLORS["Positive"])
    for bar, v in zip(bars, groups["positive"]):
        ax.annotate(f"{v:.0f}%", (v, bar.get_y() + bar.get_height() / 2), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=style.INK_SECONDARY)
    ax.set_xlim(0, 108)
    ax.set_title(title)
    ax.set_xlabel(f"Positive reviews (%), groups with {MIN_REVIEWS}+ reviews")
    ax.grid(axis="y", visible=False)
    style.save(fig, filename)
    return groups


def top_words(texts, n=15):
    counter = Counter()
    for t in texts.dropna():
        counter.update(t.split())
    return counter.most_common(n)


def chart_top_words(df):
    pos = top_words(df.loc[df["sentiment"] == "Positive", "clean_text"])
    neg = top_words(df.loc[df["sentiment"] == "Negative", "clean_text"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    for ax, words, label in [(axes[0], pos, "Positive"), (axes[1], neg, "Negative")]:
        if not words:
            continue
        w, c = zip(*reversed(words))
        ax.barh(w, c, height=0.6, color=style.SENTIMENT_COLORS[label])
        ax.set_title(f"Top words in {label.lower()} reviews", fontsize=12)
        ax.set_xlabel("Times mentioned")
        ax.grid(axis="y", visible=False)
    fig.tight_layout(w_pad=4)
    style.save(fig, "sent_5_top_words")
    return pos, neg


def word_cloud(texts, label, filename):
    text = " ".join(texts.dropna())
    if not text.strip():
        return
    base = style.SENTIMENT_COLORS[label]
    cloud = WordCloud(width=1200, height=600, background_color=style.SURFACE,
                      max_words=80, collocations=False, random_state=1,
                      color_func=lambda *a, **k: base).generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(cloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(f"Word cloud: {label.lower()} reviews")
    style.save(fig, filename)


def complaint_counts(df):
    negative = df[df["sentiment"] == "Negative"]["text"].str.lower()
    results = {}
    for topic, keywords in COMPLAINTS.items():
        # \b = start of a word, so "pill" matches "pilling" but "red" can't match "ordered"
        pattern = r"\b(?:" + "|".join(re.escape(k) for k in keywords) + ")"
        results[topic] = int(negative.str.contains(pattern, regex=True).sum())
    return dict(sorted(results.items(), key=lambda x: x[1], reverse=True)), len(negative)


def chart_complaints(complaints, total_negative):
    items = [(k, v) for k, v in complaints.items() if v > 0]
    if not items:
        return
    items.reverse()
    names, values = zip(*items)
    pct = [v / total_negative * 100 for v in values]
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(names) + 1.5))
    bars = ax.barh(names, pct, height=0.55, color=style.SENTIMENT_COLORS["Negative"])
    for bar, v, n in zip(bars, pct, values):
        ax.annotate(f"{v:.0f}% ({n})", (v, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=9,
                    color=style.INK_SECONDARY)
    ax.set_xlim(0, max(pct) * 1.25)
    ax.set_title("What do unhappy customers complain about?")
    ax.set_xlabel(f"Share of negative reviews mentioning the topic (n = {total_negative})")
    ax.grid(axis="y", visible=False)
    style.save(fig, "sent_8_complaints")


if __name__ == "__main__":
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} clean reviews")

    # ---- 1. Score every review with VADER ----
    analyzer = SentimentIntensityAnalyzer()
    scores = df["text"].astype(str).apply(analyzer.polarity_scores)
    df["compound"] = scores.apply(lambda s: s["compound"])
    df["sentiment"] = df["compound"].apply(label_for)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved scored reviews to {OUTPUT_FILE}\n")

    print("Sentiment split (all reviews):")
    print((df["sentiment"].value_counts(normalize=True) * 100).round(1).to_string(), "\n")

    # ---- 2. Do stars and words agree? ----
    df["star_group"] = pd.cut(df["rating"], bins=[0, 2, 3, 5], labels=["Negative", "Neutral", "Positive"])
    agree = (df["star_group"].astype(str) == df["sentiment"]).mean() * 100
    happy_stars_sad_words = df[(df["rating"] >= 4) & (df["sentiment"] == "Negative")]
    sad_stars_happy_words = df[(df["rating"] <= 2) & (df["sentiment"] == "Positive")]
    print(f"Stars and text sentiment agree for {agree:.1f}% of reviews")
    print(f"4-5 star reviews with negative text: {len(happy_stars_sad_words)}")
    print(f"1-2 star reviews with positive text: {len(sad_stars_happy_words)}\n")

    # ---- 3. Charts ----
    print("Making charts...")
    by_brand = chart_sentiment_by_brand(df)
    by_rating = chart_score_by_rating(df)
    matrix = chart_rating_vs_sentiment(df)
    by_skin = chart_group_sentiment(by_skin_type(df), "skin_type_group",
                                    "Positive reviews by skin type", "sent_4_positive_by_skin_type")
    pos_words, neg_words = chart_top_words(df)
    word_cloud(df.loc[df["sentiment"] == "Positive", "clean_text"], "Positive", "sent_6_wordcloud_positive")
    word_cloud(df.loc[df["sentiment"] == "Negative", "clean_text"], "Negative", "sent_7_wordcloud_negative")
    complaints, total_negative = complaint_counts(df)
    chart_complaints(complaints, total_negative)

    # ---- 4. Best and worst products by sentiment ----
    products = df.groupby(["product", "brand_name"]).agg(
        reviews=("compound", "size"), avg_rating=("rating", "mean"),
        avg_sentiment=("compound", "mean"),
        pct_negative=("sentiment", lambda s: (s == "Negative").mean() * 100)).reset_index()
    products = products[products["reviews"] >= MIN_REVIEWS]
    best = products.sort_values("avg_sentiment", ascending=False).head(5)
    worst = products.sort_values("pct_negative", ascending=False).head(5)
    print("\nMost loved products (highest average sentiment):")
    print(best[["product", "brand_name", "reviews", "avg_sentiment"]].round(2).to_string(index=False))
    print("\nMost complained-about products (highest % negative):")
    print(worst[["product", "brand_name", "reviews", "pct_negative"]].round(1).to_string(index=False))

    # ---- 5. Example reviews for the report ----
    def examples(frame, n=3):
        return [{"rating": int(r.rating), "compound": round(r.compound, 2), "product": r.product,
                 "text": r.text[:300]} for r in frame.head(n).itertuples()]

    summary = {
        "sentiment_pct_overall": (df["sentiment"].value_counts(normalize=True) * 100).round(1).to_dict(),
        "sentiment_pct_by_brand": by_brand.round(1).to_dict("index"),
        "avg_compound_by_brand": df.groupby("brand_name")["compound"].mean().round(3).to_dict(),
        "avg_compound_by_rating": {int(k): round(v, 3) for k, v in by_rating.items() if pd.notna(v)},
        "rating_vs_sentiment_row_pct": {int(k): v for k, v in matrix.round(1).to_dict("index").items()},
        "agreement_pct": round(agree, 1),
        "n_high_stars_negative_text": int(len(happy_stars_sad_words)),
        "n_low_stars_positive_text": int(len(sad_stars_happy_words)),
        "positive_pct_by_skin_type": by_skin.round(1).to_dict("index"),
        "top_positive_words": pos_words,
        "top_negative_words": neg_words,
        "complaints": complaints,
        "total_negative": int(total_negative),
        "best_products": best.round(3).to_dict("records"),
        "worst_products": worst.round(1).to_dict("records"),
        "examples_high_stars_negative_text": examples(happy_stars_sad_words.sort_values("compound")),
        "examples_low_stars_positive_text": examples(sad_stars_happy_words.sort_values("compound", ascending=False)),
        "examples_most_negative": examples(df.sort_values("compound")),
    }
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSaved key numbers to {SUMMARY_FILE}")
