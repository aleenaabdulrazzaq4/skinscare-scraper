"""
build_results.py - fit the audience model, run all five analyses, validate against the simulator's hidden truth,
and save everything the web app needs.

    python build_results.py            (about 30 seconds)
"""
import json
import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

import engine as E

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA, RES = os.path.join(HERE, "..", "data"), os.path.join(HERE, "..", "results")
os.makedirs(RES, exist_ok=True)


def main():
    posts = pd.read_csv(os.path.join(DATA, "posts.csv"))
    comments = pd.read_csv(os.path.join(DATA, "comments.csv"))
    tpath = os.path.join(DATA, "posts_truth.csv")
    truth = pd.read_csv(tpath) if os.path.exists(tpath) else None
    print(f"{len(posts):,} posts, {len(comments):,} comments")

    # ---- Q2 audience model (text only; labels never used for fitting)
    model = E.AudienceModel().fit(comments.comment_text.tolist())
    C = model.enrich(comments)
    P = E.build_post_features(posts, C)
    A = E.find_anomalies(P)

    # ---- examples per need: comments closest to their cluster centre, one per language where possible
    F = model._features([E.clean(t) for t in C.comment_text])
    d = np.linalg.norm(F - model.km.cluster_centers_[C.cluster.values], axis=1)
    C = C.assign(_d=d)
    examples = {}
    for need, g in C.groupby("need"):
        pick = []
        for lang in ("English", "Roman Urdu", "Urdu"):
            h = g[g.language_type == lang].sort_values("_d").drop_duplicates("comment_text")
            if len(h):
                pick.append(h.iloc[0].comment_text)
        examples[need] = pick
    C = C.drop(columns="_d")

    # ---- validation against hidden labels
    val = dict(n_posts=len(posts), n_comments=len(comments), k_clusters=model.k, k_silhouette={str(k): round(v, 3) for k, v in model.k_scores.items()},
               n_needs=int(C.need.nunique()))
    has_truth = os.path.exists(os.path.join(DATA, "posts_truth.csv")) and "topic" in comments.columns
    if has_truth:
        ct = pd.crosstab(C.need, C.topic)
        val["comment_clustering"] = dict(ARI=round(adjusted_rand_score(C.topic, C.need), 3),
                                         NMI=round(normalized_mutual_info_score(C.topic, C.need), 3),
                                         purity=round(ct.max(axis=1).sum() / ct.values.sum(), 3))
        val["purity_by_language"] = {}
        for lang, g in C.groupby("language_type"):
            c2 = pd.crosstab(g.need, g.topic); val["purity_by_language"][lang] = round(c2.max(axis=1).sum() / c2.values.sum(), 3)
        hi_pred, hi_true = C.intent_tier == "High intent", C.purchase_intent == "High intent"
        val["high_intent_detection"] = dict(precision=round((hi_pred & hi_true).sum() / hi_pred.sum(), 3), recall=round((hi_pred & hi_true).sum() / hi_true.sum(), 3))
        flag, real = set(A.post_id), set(truth[truth.anomaly_truth != "normal"].post_id)
        an = dict(overall_precision=round(len(flag & real) / len(flag), 3), overall_recall=round(len(flag & real) / len(real), 3), by_type={})
        for k in ["viral", "flop", "complaint_storm", "spam_bot"]:
            tk, got = set(truth[truth.anomaly_truth == k].post_id), set(A[A.anomaly_type == k].post_id)
            an["by_type"][k] = dict(planted=len(tk), flagged=len(got), recall=round(len(tk & got) / len(tk), 2), precision=round(len(tk & got) / max(len(got), 1), 2))
        val["anomaly_detection"] = an
    val["note"] = ("Validation uses the simulator's hidden labels (topic, purchase_intent, anomaly_truth); none were used to fit the engine."
                   if has_truth else "No hidden labels found, so validation was skipped.")
    json.dump(val, open(os.path.join(RES, "validation.json"), "w"), indent=2)

    # ---- save tables
    needs = (C.groupby("need").agg(comments=("comment_id", "size")).assign(share=lambda d: d.comments / d.comments.sum()).reset_index()
             .sort_values("comments", ascending=False))
    needs["intent_tier"] = needs.need.map(lambda n: E.INTENT_TIER.get(n, "No intent"))
    needs["top_terms"] = needs.need.map(lambda n: ", ".join(sorted({t for c, nm in model.names.items() if nm == n for t in model.top_terms[c]})[:8]))
    needs["examples"] = needs.need.map(lambda n: " | ".join(examples[n]))
    needs.to_csv(os.path.join(RES, "audience_needs.csv"), index=False)
    E.content_performance(P).to_csv(os.path.join(RES, "content_performance.csv"), index=False)
    E.content_performance(P, ("platform", "content_type")).to_csv(os.path.join(RES, "content_by_platform.csv"), index=False)
    A[["post_id", "brand", "platform", "campaign", "content_type", "likes", "comments_count", "shares", "views", "anomaly_type", "severity", "why"]] \
        .to_csv(os.path.join(RES, "unusual_posts.csv"), index=False)
    for by in ("campaign", "brand", "platform"):
        sh, lift = E.need_mix(C, P, by); sh.to_csv(os.path.join(RES, f"need_mix_by_{by}.csv"))
    E.city_demand(C, P).to_csv(os.path.join(RES, "city_demand.csv"), index=False)
    recs = E.recommendations(P, C, A)
    json.dump(recs, open(os.path.join(RES, "recommendations.json"), "w"), indent=2)

    # ---- artefacts for the web app
    C.to_csv(os.path.join(DATA, "comments_scored.csv"), index=False)
    P.to_csv(os.path.join(DATA, "posts_features.csv"), index=False)
    A.to_csv(os.path.join(DATA, "anomalies.csv"), index=False)
    json.dump(examples, open(os.path.join(DATA, "examples.json"), "w"), ensure_ascii=False)
    with open(os.path.join(DATA, "audience_model.pkl"), "wb") as f:
        pickle.dump(model, f)

    print(json.dumps({k: val[k] for k in ("k_clusters", "comment_clustering", "high_intent_detection", "anomaly_detection") if k in val}, indent=1))
    print(needs[["need", "comments", "share", "intent_tier"]].round(3).to_string(index=False))
    print(f"{len(recs)} recommendations; top: ", [r['title'] for r in recs[:3]])


if __name__ == "__main__":
    main()
