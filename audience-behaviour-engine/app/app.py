"""
Audience Behaviour Discovery - small web app.

    pip install flask pandas numpy scikit-learn
    python app.py          ->  http://127.0.0.1:5000

Filters (brand / platform / campaign) re-compute every table. The "Try a comment" box classifies any
new comment (English, Roman Urdu or Urdu) with the trained model.
"""
import json
import os
import pickle
import sys

import pandas as pd
from flask import Flask, jsonify, render_template, request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import engine as E  # noqa: E402  (pickle needs the module importable)

DATA, RES = os.path.join(ROOT, "data"), os.path.join(ROOT, "results")
app = Flask(__name__)

P = pd.read_csv(os.path.join(DATA, "posts_features.csv"))
C = pd.read_csv(os.path.join(DATA, "comments_scored.csv"))
A = pd.read_csv(os.path.join(DATA, "anomalies.csv"))
EXAMPLES = json.load(open(os.path.join(DATA, "examples.json")))
VALIDATION = json.load(open(os.path.join(RES, "validation.json")))
with open(os.path.join(DATA, "audience_model.pkl"), "rb") as f:
    MODEL = pickle.load(f)

TYPE_LABEL = {"viral": "Viral", "flop": "Flop", "complaint_storm": "Complaint storm", "spam_bot": "Spam flood", "comment_surge": "Comment surge"}


def build_context(brand=None, platform=None, campaign=None):
    Pf, Cf = E.apply_filters(P, C, brand, platform, campaign)
    Af = A[A.post_id.isin(Pf.post_id)]
    ctx = dict(brand=brand or "", platform=platform or "", campaign=campaign or "",
               brands=sorted(P.brand.unique()), platforms=sorted(P.platform.unique()), campaigns=sorted(P.campaign.unique()),
               n_posts=len(Pf), n_comments=len(Cf), validation=VALIDATION, type_label=TYPE_LABEL, needs_order=E.NEEDS)
    # Q1
    ctx["content"] = E.content_performance(Pf).to_dict("records")
    pc = E.content_performance(Pf, ("platform", "content_type"))
    ctx["matrix"] = {(r["content_type"], r["platform"]): r for r in pc.to_dict("records")} if len(pc) else {}
    ctx["matrix_platforms"] = sorted(Pf.platform.unique())
    ctx["matrix_contents"] = list(E.CONTENT_ORDER) if hasattr(E, "CONTENT_ORDER") else sorted(Pf.content_type.unique())
    # Q2
    needs = []
    if len(Cf):
        vc = Cf.need.value_counts()
        for need, n in vc.items():
            g = Cf[Cf.need == need]
            cl = [c for c, nm in MODEL.names.items() if nm == need]
            terms = []
            for c in cl:
                terms += [t for t in MODEL.top_terms[c] if t not in terms]
            needs.append(dict(need=need, comments=int(n), share=n / len(Cf), tier=E.INTENT_TIER.get(need, "No intent"),
                              lang=(g.language_type.value_counts(normalize=True)).round(2).to_dict(), terms=terms[:6],
                              examples=EXAMPLES.get(need, [])))
    ctx["needs"] = needs
    ctx["tiers"] = (Cf.intent_tier.value_counts(normalize=True).to_dict() if len(Cf) else {})
    # Q3
    ctx["anom_counts"] = Af.anomaly_type.value_counts().to_dict()
    ctx["anomalies"] = Af.head(25).to_dict("records")
    ctx["anom_total"] = len(Af)
    # Q4
    for by in ("campaign", "brand", "platform"):
        if len(Cf):
            sh, lift = E.need_mix(Cf, Pf, by)
            ctx[f"mix_{by}"] = [dict(key=k, n=int((Pf[by] == k).sum()), share=sh.loc[k].to_dict(), lift=lift.loc[k].fillna(1).to_dict()) for k in sh.index]
        else:
            ctx[f"mix_{by}"] = []
    ctx["cities"] = E.city_demand(Cf, Pf).head(6).to_dict("records") if len(Cf) else []
    # Q5
    ctx["recs"] = E.recommendations(Pf, Cf, Af) if len(Cf) > 100 else []
    return ctx


@app.template_global("pct")
@app.template_filter("pct")
def pct(v, d=0):
    return "-" if v is None or pd.isna(v) else f"{v * 100:.{d}f}%"


@app.template_filter("heat")
def heat(lift):
    """Background colour for a need-share cell: orange = above average, blue = below."""
    if lift is None or pd.isna(lift):
        return "transparent"
    if lift >= 1:
        return f"rgba(234,120,40,{min((lift - 1) / 1.6, .75):.2f})"
    return f"rgba(60,120,200,{min((1 - lift) / 1.2, .45):.2f})"


@app.route("/")
def index():
    return render_template("dashboard.html", static=False,
                           **build_context(request.args.get("brand") or None, request.args.get("platform") or None,
                                           request.args.get("campaign") or None))


@app.route("/api/classify", methods=["POST"])
def classify():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify(error="Please enter a comment"), 400
    return jsonify(MODEL.classify(text))


if __name__ == "__main__":
    app.run(debug=False, port=5000)
