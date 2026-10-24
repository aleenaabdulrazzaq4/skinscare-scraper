"""
Day 7: EDA (Exploratory Data Analysis) of the customer reviews.

EDA means getting to know the data before the main analysis: how much there is,
how it is spread out, what is missing, and any patterns worth testing later.

Input:  data/processed/reviews_clean.csv
Output: charts in reports/figures/ (eda_*.png)
        key numbers in reports/eda_summary.json

Run it from the project folder:
    python src/eda.py
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import style

INPUT_FILE = "data/processed/reviews_clean.csv"
SUMMARY_FILE = "reports/eda_summary.json"
MIN_REVIEWS = 20   # only compare groups that have at least this many reviews

style.setup()
BRANDS = list(style.BRAND_COLORS)


def label_bars(ax, bars, fmt="{:.0f}", horizontal=False):
    """Write the value at the end of each bar."""
    for bar in bars:
        if horizontal:
            value = bar.get_width()
            ax.annotate(fmt.format(value), (value, bar.get_y() + bar.get_height() / 2),
                        xytext=(4, 0), textcoords="offset points", va="center",
                        fontsize=9, color=style.INK_SECONDARY)
        else:
            value = bar.get_height()
            ax.annotate(fmt.format(value), (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 3), textcoords="offset points", ha="center",
                        fontsize=9, color=style.INK_SECONDARY)


def chart_reviews_per_brand(df):
    counts = df["brand_name"].value_counts().reindex(BRANDS)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(counts.index, counts.values, width=0.5,
                  color=[style.BRAND_COLORS[b] for b in counts.index])
    label_bars(ax, bars, "{:,.0f}")
    ax.set_title("Reviews collected per brand")
    ax.set_ylabel("Number of reviews")
    ax.grid(axis="x", visible=False)
    style.save(fig, "eda_1_reviews_per_brand")


def chart_rating_distribution(df):
    """Share of 1-5 star reviews for each brand (percent, so brands are comparable)."""
    share = (pd.crosstab(df["rating"], df["brand_name"], normalize="columns") * 100)
    share = share.reindex(index=[1, 2, 3, 4, 5], columns=BRANDS, fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.38
    for i, brand in enumerate(BRANDS):
        x = [s + (i - 0.5) * (width + 0.02) for s in share.index]
        bars = ax.bar(x, share[brand], width=width, color=style.BRAND_COLORS[brand], label=brand)
        label_bars(ax, bars, "{:.0f}%")
    ax.set_xticks([1, 2, 3, 4, 5], ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"])
    ax.set_title("Star rating distribution by brand")
    ax.set_ylabel("Share of the brand's reviews (%)")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    style.save(fig, "eda_2_rating_distribution")


def by_skin_type(df):
    """One row per (review, skin type ticked), so 'Dry;Sensitive' counts for both."""
    out = df.assign(skin_type_group=df["skin_types"].str.split(";")).explode("skin_type_group")
    return out[~out["skin_type_group"].isin(["Not given", "Other"])]


def chart_group_average(df, column, title, filename):
    """Average star rating per group (e.g. per skin type), largest groups only."""
    groups = df[df[column] != "Not given"].groupby(column)["rating"].agg(["mean", "count"])
    groups = groups[groups["count"] >= MIN_REVIEWS].sort_values("mean")
    if groups.empty:
        return groups
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(groups) + 1.5))
    bars = ax.barh(groups.index, groups["mean"], height=0.55, color=style.STAR_COLORS[4])
    label_bars(ax, bars, "{:.2f}", horizontal=True)
    ax.set_xlim(1, 5.3)
    ax.set_title(title)
    ax.set_xlabel(f"Average star rating (groups with {MIN_REVIEWS}+ reviews)")
    ax.grid(axis="y", visible=False)
    style.save(fig, filename)
    return groups


def chart_length_by_rating(df):
    """Do unhappy customers write longer reviews?"""
    median_len = df.groupby("rating")["word_count"].median().reindex([1, 2, 3, 4, 5])
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(median_len.index, median_len.values, width=0.55,
                  color=[style.STAR_COLORS[s] for s in median_len.index])
    label_bars(ax, bars, "{:.0f}")
    ax.set_xticks([1, 2, 3, 4, 5], ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"])
    ax.set_title("Review length by star rating")
    ax.set_ylabel("Median words per review")
    ax.grid(axis="x", visible=False)
    style.save(fig, "eda_5_length_by_rating")
    return median_len


def chart_reviews_over_time(df):
    monthly = df.dropna(subset=["year_month"]).groupby(["year_month", "brand_name"]).size()
    monthly = monthly.unstack(fill_value=0).reindex(columns=BRANDS, fill_value=0)
    monthly = monthly.tail(24)   # last two years keeps the chart readable
    fig, ax = plt.subplots(figsize=(10, 4))
    for brand in BRANDS:
        ax.plot(monthly.index, monthly[brand], color=style.BRAND_COLORS[brand],
                linewidth=2, label=brand)
    ax.set_title("Reviews posted per month (last 24 months)")
    ax.set_ylabel("Reviews")
    ticks = monthly.index[::3]
    ax.set_xticks(ticks, ticks, rotation=45, ha="right")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    style.save(fig, "eda_6_reviews_over_time")


def chart_lowest_rated(df, min_reviews=50):
    """The 10 products with the lowest average rating (only products with 50+ reviews)."""
    products = df.groupby(["product", "brand_name"])["rating"].agg(["mean", "count"]).reset_index()
    products = products[products["count"] >= min_reviews]
    low = products.sort_values("mean").head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    names = [p if len(p) <= 45 else p[:42] + "..." for p in low["product"]]
    bars = ax.barh(names, low["mean"], height=0.6,
                   color=[style.BRAND_COLORS[b] for b in low["brand_name"]])
    label_bars(ax, bars, "{:.2f}", horizontal=True)
    handles = [Patch(color=style.BRAND_COLORS[b], label=b) for b in BRANDS]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.set_xlim(1, 5.3)
    ax.set_title(f"10 lowest-rated products ({min_reviews}+ reviews)")
    ax.set_xlabel("Average star rating")
    ax.grid(axis="y", visible=False)
    style.save(fig, "eda_7_lowest_rated_products")
    return low


if __name__ == "__main__":
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} clean reviews\n")

    # ---- Basic facts ----
    print("Reviews per brand:")
    print(df["brand_name"].value_counts().to_string(), "\n")
    print("Average rating per brand:")
    print(df.groupby("brand_name")["rating"].mean().round(2).to_string(), "\n")
    print("Star ratings (all reviews):")
    print(df["rating"].value_counts().sort_index(ascending=False).to_string(), "\n")

    # ---- Charts ----
    print("Making charts...")
    chart_reviews_per_brand(df)
    chart_rating_distribution(df)
    by_category = chart_group_average(df, "category", "Average rating by product category",
                                      "eda_3_rating_by_category")
    by_skin = chart_group_average(by_skin_type(df), "skin_type_group",
                                  "Average rating by skin type", "eda_4_rating_by_skin_type")
    length = chart_length_by_rating(df)
    chart_reviews_over_time(df)
    lowest = chart_lowest_rated(df)

    # ---- Save key numbers for the report ----
    summary = {
        "total_reviews": int(len(df)),
        "products_with_reviews": int(df["product"].nunique()),
        "reviews_per_brand": df["brand_name"].value_counts().to_dict(),
        "products_per_brand": df.groupby("brand_name")["product"].nunique().to_dict(),
        "avg_rating_overall": round(df["rating"].mean(), 2),
        "avg_rating_per_brand": df.groupby("brand_name")["rating"].mean().round(2).to_dict(),
        "rating_counts": {int(k): int(v) for k, v in df["rating"].value_counts().items()},
        "pct_5_star": round((df["rating"] == 5).mean() * 100, 1),
        "pct_1_2_star": round((df["rating"] <= 2).mean() * 100, 1),
        "rating_by_category": by_category.round(2).to_dict("index"),
        "rating_by_skin_type": by_skin.round(2).to_dict("index"),
        "pct_skin_type_given": round((df["skin_types"] != "Not given").mean() * 100, 1),
        "pct_verified": round(df["verified"].astype(str).str.lower().eq("true").mean() * 100, 1),
        "median_words_by_rating": {int(k): float(v) for k, v in length.items() if pd.notna(v)},
        "lowest_rated_products": lowest.iloc[::-1].round(2).to_dict("records"),
        "date_range": [str(df["date"].min())[:10], str(df["date"].max())[:10]],
    }
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSaved key numbers to {SUMMARY_FILE}")
