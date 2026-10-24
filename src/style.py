"""
Shared chart style so every figure in the project looks consistent.

Colours have one job each:
- BRAND colours tell the two brands apart (always the same colour per brand)
- SENTIMENT colours show polarity: blue = positive, grey = neutral, red = negative
- STAR colours are one blue, light (1 star) to dark (5 stars), because stars are ordered
"""

import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

BRAND_COLORS = {"Glow Recipe": "#2a78d6", "KraveBeauty": "#eb6834"}
BRAND_LABELS = {"glow_recipe": "Glow Recipe", "kravebeauty": "KraveBeauty"}

SENTIMENT_COLORS = {"Positive": "#2a78d6", "Neutral": "#b5b3ab", "Negative": "#e34948"}
SENTIMENT_ORDER = ["Positive", "Neutral", "Negative"]

STAR_COLORS = {1: "#86b6ef", 2: "#5598e7", 3: "#2a78d6", 4: "#1c5cab", 5: "#104281"}

FIGURE_DIR = "reports/figures"


def setup():
    """Apply the shared look to every matplotlib chart."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"],
        "font.size": 11,
        "text.color": INK,
        "axes.labelcolor": INK_SECONDARY,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.edgecolor": AXIS,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_SECONDARY,
        "ytick.labelcolor": INK_SECONDARY,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    })


def save(fig, name):
    """Save a chart into reports/figures and close it."""
    path = f"{FIGURE_DIR}/{name}.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved chart: {path}")
