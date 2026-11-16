"""charts.py - report figures."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES, DATA, OUT = (os.path.join(HERE, "..", d) for d in ("results", "data", "charts"))
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
ROLE = {"Star": "#2a9d8f", "Awareness only": "#3b6fd4", "Hidden converter": "#e9a23b", "Rethink": "#d64545"}

# 1. content: attention vs buying signals
ct = pd.read_csv(os.path.join(RES, "content_performance.csv"))
fig, ax = plt.subplots(figsize=(7.5, 4.8))
for r in ct.itertuples():
    ax.errorbar(r.buying_signal_rate * 100, r.eng_index, yerr=[[r.eng_index - r.ci_low], [r.ci_high - r.eng_index]], fmt="o", ms=11, color=ROLE[r.role], capsize=3)
    ax.annotate(r.content_type, (r.buying_signal_rate * 100, r.eng_index), xytext=(8, 6), textcoords="offset points", fontsize=9)
ax.axhline(ct.eng_index.median(), color="#bbb", ls="--", lw=1); ax.axvline(ct.buying_signal_rate.median() * 100, color="#bbb", ls="--", lw=1)
ax.set_xlabel("Buying-signal comments (% of comments)"); ax.set_ylabel("Engagement index (1.0 = typical post)")
ax.set_title("Which content attracts attention and which drives buying signals")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "content_attention_vs_intent.png"), dpi=150); plt.close(fig)

# 2. audience needs
nd = pd.read_csv(os.path.join(RES, "audience_needs.csv")).sort_values("share")
tier_col = {"High intent": "#2a9d8f", "Possible inquiry": "#3b6fd4", "Service issue": "#d64545", "Product feedback": "#e9a23b", "No intent": "#9aa4b2", "Spam": "#7a5cc2"}
fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.barh(nd.need, nd.share * 100, color=[tier_col[t] for t in nd.intent_tier])
for y, v in enumerate(nd.share * 100): ax.text(v + .3, y, f"{v:.1f}%", va="center", fontsize=9)
ax.set_xlabel("% of comments"); ax.set_title("What the audience talks about (11 needs found without labels)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=t) for t, c in tier_col.items()], fontsize=8, frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "audience_needs.png"), dpi=150); plt.close(fig)

# 3. anomalies
A = pd.read_csv(os.path.join(DATA, "anomalies.csv")); P = pd.read_csv(os.path.join(DATA, "posts_features.csv"))
tr = pd.read_csv(os.path.join(DATA, "posts_truth.csv")).set_index("post_id").anomaly_truth
col = {"viral": "#2a9d8f", "flop": "#d64545", "complaint_storm": "#e9801f", "spam_bot": "#7a5cc2", "comment_surge": "#3b6fd4"}
import sys; sys.path.insert(0, HERE); import engine as E
AA = E.find_anomalies(P)
X = E._design(P)
r1, s1 = E._robust_resid(X, np.log1p(P.score.values))
r2, s2 = E._robust_resid(X, np.log((1 + P.comments_count.values) / (1 + P.likes.values)))
fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.scatter(r1 / s1, r2 / s2, s=4, color="#d0d5dd")
for k, c in col.items():
    g = AA[AA.anomaly_type == k]
    if len(g): ax.scatter(g.z_engagement, g.z_comment_ratio, s=22, color=c, label=k.replace("_", " "))
ax.axvline(3, color="#bbb", ls="--", lw=1); ax.axvline(-3, color="#bbb", ls="--", lw=1)
ax.set_xlabel("Engagement vs comparable posts (robust z)"); ax.set_ylabel("Comments-per-like vs comparable posts (robust z)")
ax.set_title("Unusual posts"); ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "unusual_posts.png"), dpi=150); plt.close(fig)

# 4. needs by campaign heatmap (lift vs overall)
mx = pd.read_csv(os.path.join(RES, "need_mix_by_campaign.csv"), index_col=0)
overall = pd.read_csv(os.path.join(DATA, "comments_scored.csv")).need.value_counts(normalize=True)
lift = mx / overall.reindex(mx.columns)
fig, ax = plt.subplots(figsize=(9.5, 3.8))
im = ax.imshow(lift.values, cmap="RdBu_r", vmin=.4, vmax=1.6, aspect="auto")
ax.set_xticks(range(lift.shape[1])); ax.set_xticklabels(lift.columns, rotation=35, ha="right", fontsize=8)
ax.set_yticks(range(lift.shape[0])); ax.set_yticklabels(lift.index)
for i in range(lift.shape[0]):
    for j in range(lift.shape[1]): ax.text(j, i, f"{mx.values[i, j] * 100:.0f}%", ha="center", va="center", fontsize=8,
                color="white" if (lift.values[i, j] > 1.4 or lift.values[i, j] < .65) else "black")
ax.set_title("Audience needs by campaign (share of comments; colour = vs overall average)")
fig.colorbar(im, ax=ax, fraction=.025); fig.tight_layout(); fig.savefig(os.path.join(OUT, "needs_by_campaign.png"), dpi=150); plt.close(fig)
print("charts written")
