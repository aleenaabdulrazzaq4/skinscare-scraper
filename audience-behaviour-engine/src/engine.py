"""
engine.py - Audience Behaviour Discovery Engine
===============================================
Answers five marketing questions from social-media posts + comments:

 Q1 Which content attracts attention?          -> content_performance()
 Q2 What does the audience want?               -> AudienceModel (unsupervised comment clustering)
 Q3 Which patterns are unusual?                -> find_anomalies()
 Q4 Which audience needs should be addressed?  -> need_mix(), city_demand()
 Q5 What should marketing do next?             -> recommendations()

The comment model is UNSUPERVISED: it never reads the `topic`, `sentiment` or `purchase_intent`
columns (those are used only afterwards, in validate.py, to check the clusters).
"""
import re

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import Normalizer

# ------------------------------------------------------------------------------ text handling
NORMALISE = [(r"\b(kitney|kitny)\b", "kitne"), (r"\b(bohot|boht|bahut)\b", "bohat"), (r"\b(pls|please)\b", "plz"),
             (r"\b(nai|nhi)\b", "nahi"), (r"\bhy\b", "hai"), (r"\bkia\b", "kya"), (r"\b(den|dain)\b", "dein"),
             (r"\b(piyara|pyara)\b", "pyara")]


def clean(text: str) -> str:
    t = str(text).lower()
    t = re.sub(r"[^\w\s\u0600-\u06FF]", " ", t)            # drop emojis / punctuation, keep Urdu script
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)                   # pleaseee -> pleasee
    t = re.sub(r"\b(\w*?)(ee|oo|aa)\b", lambda m: m.group(1) + m.group(2)[0], t)
    for pat, rep in NORMALISE:
        t = re.sub(pat, rep, t)
    return re.sub(r"\s+", " ", t).strip()


# Multilingual need lexicon (English + Roman Urdu + Urdu). Used for (a) hybrid features and (b) naming clusters.
LEX = {
 "price": r"price|rate|qeemat|how much|kitne ka|kitna|قیمت|ریٹ|mehnga|expensive|overpriced|zyada|ghalat|مہنگا|زیادہ|not worth|crazy",
 "fabric": r"fabric|quality|kapra|material|lawn|wash|faded|thin|patla|soft|کپڑا|کوالٹی|دھل|لان",
 "size": r"size|\bxl\b|medium|length|shrink|stitched|kameez|سائز|لمبائی|ایکس",
 "delivery": r"deliver|parcel|tracking|received|receive|courier|waiting|late|delayed|\bder\b|ڈیلیوری|ٹریکنگ|انتظار|ابھی تک|لیٹ|نہیں ملا|nahi aaya|abhi tak",
 "discount": r"discount|sale|offer|promo|\boff\b|bundle|code|ڈسکاؤنٹ|سیل|آفر|student",
 "availability": r"stock|available|sold out|outlet|online|mil jayega|دستیاب|اسٹاک",
 "intent": r"just ordered|ordered mine|maine order|order kar|aaj order|ordering|booking|\bbook\b|cart|inbox|\bdm\b|how do i order|order kaise|chahiye|i want|ان باکس|آرڈر کر|آرڈر کیسے|چاہیے|details",
 "praise": r"beautiful|gorgeous|love|stunning|elegant|masterpiece|favourite|khoobsurat|mashallah|pyara|zabardast|kamal|achi collection|خوبصورت|ماشاء|زبردست|پیارا|elegant",
 "spam": r"giveaway|follow|replica|followers|iphone|earn|click|link|paisay|profile|promotion|فالو|فری|پیسے|فالوورز|jeetein|kamayein",
}
COMPLAINT = r"late|still|waiting|not received|nahi aaya|nahi hua|abhi tak|worst|delayed|der kar|no reply|koi reply|tracking|لیٹ|انتظار|نہیں ملا|ابھی تک|zyada|mehnga|expensive|overpriced|ghalat|crazy|not worth|مہنگا|زیادہ|اتنا|barh|cheaper|kharab|faded|utar|pehle jaisa|cheap|خراب|اتر|جیسا نہیں|gone down|thin|patla|too high|غلط|last year"
LEX_RE = {k: re.compile(v) for k, v in LEX.items()}
COMPLAINT_RE = re.compile(COMPLAINT)
CATS = list(LEX)


def lex_features(texts) -> np.ndarray:
    """Binary need-category hits + one 'complaint tone' column (the last column)."""
    return np.array([[1.0 if LEX_RE[c].search(t) else 0.0 for c in CATS] + [1.0 if COMPLAINT_RE.search(t) else 0.0]
                     for t in texts])


NEED_BY_CAT = {"price": "Price", "fabric": "Fabric & quality", "size": "Size & fit", "delivery": "Delivery",
               "discount": "Discount seekers", "availability": "Availability / stock", "intent": "Ready to buy",
               "praise": "Fans & praise", "spam": "Spam / promotion"}
INTENT_TIER = {"Ready to buy": "High intent", "Price enquiries": "Possible inquiry", "Discount seekers": "Possible inquiry",
               "Availability / stock": "Possible inquiry", "Size & fit": "Possible inquiry", "Delivery enquiries": "Possible inquiry",
               "Delivery complaints": "Service issue", "Price complaints": "Service issue", "Fabric & quality": "Product feedback",
               "Fans & praise": "No intent", "Spam / promotion": "Spam"}


# ------------------------------------------------------------------------------ comment model
class AudienceModel:
    """Hybrid unsupervised comment segmenter: char/word TF-IDF -> SVD  +  multilingual lexicon features -> KMeans."""

    def __init__(self, k_range=range(8, 17), lex_weight=1.2, complaint_boost=2.2, seed=0):
        self.k_range, self.lex_weight, self.complaint_boost, self.seed = k_range, lex_weight, complaint_boost, seed

    def _features(self, clean_texts, fit=False):
        if fit:
            self.tf_c = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)
            self.tf_w = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
            X = sp.hstack([self.tf_c.fit_transform(clean_texts), self.tf_w.fit_transform(clean_texts)]).tocsr()
            self.svd = TruncatedSVD(60, random_state=self.seed)
            Z = self.svd.fit_transform(X)
            self.norm = Normalizer().fit(Z)
        else:
            X = sp.hstack([self.tf_c.transform(clean_texts), self.tf_w.transform(clean_texts)]).tocsr()
            Z = self.svd.transform(X)
        Z = self.norm.transform(Z)
        LF = lex_features(clean_texts)
        LF[:, -1] *= self.complaint_boost                      # complaint tone separates complaints from enquiries
        return np.hstack([Z, self.lex_weight * LF / np.sqrt(len(CATS) / 3)])

    def fit(self, texts):
        ct = [clean(t) for t in texts]
        F = self._features(ct, fit=True)
        rng = np.random.default_rng(self.seed)
        sample = rng.choice(len(F), size=min(6000, len(F)), replace=False)
        self.k_scores = {}
        for k in self.k_range:
            km = KMeans(k, n_init=3, random_state=self.seed).fit(F)
            self.k_scores[k] = float(silhouette_score(F[sample], km.labels_[sample]))
        self.k = max(self.k_scores, key=self.k_scores.get)
        self.km = KMeans(self.k, n_init=10, random_state=self.seed).fit(F)
        self.labels_ = self.km.labels_
        self._name_clusters(ct)
        return self

    def predict(self, texts):
        ct = [clean(t) for t in texts]
        return self.km.predict(self._features(ct))

    # -- cluster naming from member comments + lexicon enrichment
    def _name_clusters(self, ct):
        LF = lex_features(ct); L, comp = LF[:, :len(CATS)], LF[:, -1]
        overall = L.mean(0); names, meta = {}, {}
        cv = CountVectorizer(min_df=15, token_pattern=r"(?u)[\w\u0600-\u06FF]{2,}").fit(ct)
        B = (cv.transform(ct) > 0).tocsc(); vocab = np.array(cv.get_feature_names_out()); df_all = np.asarray(B.mean(0)).ravel()
        for c in range(self.k):
            m = self.labels_ == c
            cover = L[m].mean(0); enrich = cover - overall
            cat = CATS[int(np.argmax(enrich + 0.25 * cover))]
            base = NEED_BY_CAT[cat]
            cflag = comp[m].mean()
            if cat in ("price", "delivery"):
                base = base + (" complaints" if cflag >= 0.5 else " enquiries")
            names[c] = base
            p = np.asarray(B[m].mean(0)).ravel()
            score = p * np.log((p + 1e-6) / (df_all + 1e-6)); score[p < .06] = -1
            meta[c] = [vocab[i] for i in np.argsort(-score)[:6] if score[i] > 0]
        self.names, self.top_terms = names, meta
        self.tier = {c: INTENT_TIER.get(names[c], "No intent") for c in names}

    def enrich(self, comments: pd.DataFrame) -> pd.DataFrame:
        out = comments.copy()
        out["cluster"] = self.labels_
        out["need"] = out.cluster.map(self.names)
        out["intent_tier"] = out.cluster.map(self.tier)
        return out

    def classify(self, text: str) -> dict:
        c = int(self.predict([text])[0])
        d = np.linalg.norm(self.km.cluster_centers_ - self._features([clean(text)])[0], axis=1)
        return dict(cluster=c, need=self.names[c], intent=self.tier[c], top_terms=self.top_terms[c],
                    confidence=round(float(1 / (1 + np.exp(d[c] - np.sort(d)[1]))) * 2, 2))


# ============================================================================== post-level features
CITY_RE = {"Karachi": r"karachi|کراچی", "Lahore": r"lahore|لاہور", "Islamabad": r"islamabad|اسلام آباد", "Multan": r"multan|ملتان",
           "Peshawar": r"peshawar|پشاور", "Faisalabad": r"faisalabad|فیصل آباد", "Quetta": r"quetta|کوئٹہ",
           "Rawalpindi": r"rawalpindi|راولپنڈی", "Sialkot": r"sialkot|سیالکوٹ", "Hyderabad": r"hyderabad|حیدرآباد"}
NEEDS = ["Fans & praise", "Price enquiries", "Discount seekers", "Availability / stock", "Fabric & quality", "Size & fit",
         "Delivery enquiries", "Ready to buy", "Delivery complaints", "Price complaints", "Spam / promotion"]
MATURE_DAYS = 7          # posts younger than this are still collecting engagement; excluded from format comparisons


def build_post_features(posts: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
    """Join post metrics with the need-mix of their (sampled) comments."""
    P = posts.copy()
    P["shares_f"] = P.shares.fillna(0)
    P["score"] = P.likes + 2 * P.comments_count + 3 * P.shares_f              # weighted engagement
    mature = P[P.days_since_post >= MATURE_DAYS]
    base = mature.groupby(["brand", "platform"]).score.median().rename("bp_median")   # brand/platform size
    P = P.join(base, on=["brand", "platform"])
    P["eng_index"] = P.score / P.bp_median                                      # 1.0 = typical post of that brand+platform
    P["eng_rate"] = (P.likes + P.comments_count + P.shares_f) / P.views          # only where views are public
    P["share_to_like"] = P.shares_f / P.likes.clip(lower=1)
    P["comments_per_1k_likes"] = 1000 * P.comments_count / P.likes.clip(lower=1)
    ct = pd.crosstab(comments.post_id, comments.need).reindex(columns=NEEDS, fill_value=0)
    ct["n_sampled"] = ct.sum(1)
    P = P.join(ct, on="post_id")
    P[NEEDS + ["n_sampled"]] = P[NEEDS + ["n_sampled"]].fillna(0)
    n = P.n_sampled.clip(lower=1)
    P["complaint_share"] = (P["Delivery complaints"] + P["Price complaints"]) / n
    P["spam_share"] = P["Spam / promotion"] / n
    P["buying_signals"] = P["Ready to buy"] + P["Price enquiries"] + P["Discount seekers"] + P["Availability / stock"] \
        + P["Size & fit"] + P["Delivery enquiries"]
    return P


# ============================================================================== Q1 content performance
def _boot_ci(x, rng, n=300):
    x = np.asarray(x.dropna()); 
    if len(x) < 8:
        return (np.nan, np.nan)
    meds = np.median(rng.choice(x, size=(n, len(x))), axis=1)
    return tuple(np.percentile(meds, [5, 95]))


def content_performance(P: pd.DataFrame, by=("content_type",), seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    M = P[P.days_since_post >= MATURE_DAYS]
    if M.empty:
        return pd.DataFrame()
    rows = []
    for key, g in M.groupby(list(by)):
        key = key if isinstance(key, tuple) else (key,)
        lo, hi = _boot_ci(g.eng_index, rng)
        rows.append(dict(zip(by, key), posts=len(g), eng_index=g.eng_index.median(), ci_low=lo, ci_high=hi,
                         eng_rate=g.eng_rate.median(), share_to_like=g.share_to_like.median(),
                         comments_per_1k_likes=g.comments_per_1k_likes.median(),
                         buying_signal_rate=g.buying_signals.sum() / max(g.n_sampled.sum(), 1),
                         discount_share=g["Discount seekers"].sum() / max(g.n_sampled.sum(), 1)))
    out = pd.DataFrame(rows)
    ref_i, ref_b = M.eng_index.median(), M.buying_signals.sum() / max(M.n_sampled.sum(), 1)
    hi_a, hi_b = out.eng_index >= ref_i, out.buying_signal_rate >= ref_b
    out["role"] = np.select([hi_a & hi_b, hi_a & ~hi_b, ~hi_a & hi_b], ["Star", "Awareness only", "Hidden converter"], "Rethink")
    return out.sort_values("eng_index", ascending=False).reset_index(drop=True)


# ============================================================================== Q3 unusual posts
def _design(P):
    D = pd.concat([pd.get_dummies(P.brand + "|" + P.platform, prefix="bp"), pd.get_dummies(P.platform + "|" + P.content_type, prefix="pc"),
                   pd.get_dummies(P.campaign, prefix="cm"),
                   pd.get_dummies(pd.cut(P.days_since_post, [0, 3, 7, 14, 30, 60, 999], labels=False), prefix="age")], axis=1)
    return D.astype(float).values


def _robust_resid(X, y, trim=3.0):
    keep = np.ones(len(y), bool)
    for _ in range(3):                                                         # fit, drop outliers, refit
        beta = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
        r = y - X @ beta
        s = 1.4826 * np.median(np.abs(r[keep] - np.median(r[keep])))
        keep = np.abs(r / s) < trim
    return r, s


def find_anomalies(P: pd.DataFrame, z_cut=3.0, min_comments=5) -> pd.DataFrame:
    """Compare every post with what comparable posts (same brand/platform/format/campaign/age) normally get."""
    X = _design(P)
    r_eng, s_eng = _robust_resid(X, np.log1p(P.score.values))
    r_ratio, s_ratio = _robust_resid(X, np.log((1 + P.comments_count.values) / (1 + P.likes.values)))
    A = P.copy()
    A["z_engagement"], A["z_comment_ratio"] = r_eng / s_eng, r_ratio / s_ratio
    A["x_expected"] = np.exp(r_eng)                                            # multiple of the expected engagement
    ok = A.n_sampled >= min_comments
    n_s = A.n_sampled.clip(lower=1)
    z_share = {}
    for col in ("complaint_share", "spam_share"):                              # expected share for comparable posts
        r_c, _ = _robust_resid(X, A[col].values)
        exp = np.clip(A[col].values - r_c, .02, .9)
        A["expected_" + col] = exp
        z_share[col] = (A[col].values - exp) / np.sqrt(exp * (1 - exp) / n_s.values)
    A["z_complaints"], A["z_spam"] = z_share["complaint_share"], z_share["spam_share"]
    kind = np.full(len(A), "", dtype=object)
    kind[(A.z_comment_ratio >= z_cut)] = "comment_surge"
    kind[(A.z_engagement <= -z_cut)] = "flop"
    kind[(A.z_engagement >= z_cut)] = "viral"
    kind[ok & (A.complaint_share >= .4) & (A.z_complaints >= 4)] = "complaint_storm"
    kind[ok & (A.spam_share >= .3) & (A.z_spam >= 4)] = "spam_bot"
    A["anomaly_type"] = kind
    A["severity"] = np.maximum.reduce([A.z_engagement.abs(), A.z_comment_ratio.abs(), A.z_complaints.clip(lower=0), A.z_spam.clip(lower=0)])

    def why(r):
        t = r.anomaly_type
        if t == "viral": return f"Engagement is {r.x_expected:.1f}x what comparable {r.content_type}s on {r.platform} get."
        if t == "flop": return f"Engagement is only {r.x_expected:.2f}x the expected level for comparable {r.content_type}s on {r.platform}."
        if t == "complaint_storm": return f"{r.complaint_share:.0%} of sampled comments are delivery/price complaints; comparable posts normally have about {r.expected_complaint_share:.0%}."
        if t == "spam_bot": return f"{r.spam_share:.0%} of sampled comments are spam or promotion (comparable posts: {r.expected_spam_share:.0%}), with {r.comments_count:,} comments in total."
        return f"{r.comments_count:,} comments on {r.likes:,} likes: far more conversation than comparable posts."
    out = A[A.anomaly_type != ""].copy()
    out["why"] = out.apply(why, axis=1)
    return out.sort_values("severity", ascending=False)


# ============================================================================== Q4 audience needs
def need_mix(C: pd.DataFrame, P: pd.DataFrame, by: str) -> pd.DataFrame:
    """Share of comments per need for each value of `by` (campaign / brand / platform / content_type) + lift vs overall."""
    J = C.merge(P[["post_id", by]], on="post_id")
    share = pd.crosstab(J[by], J.need, normalize="index").reindex(columns=NEEDS, fill_value=0)
    overall = J.need.value_counts(normalize=True).reindex(NEEDS).fillna(0)
    return share, share / overall.replace(0, np.nan)


def city_demand(C: pd.DataFrame, P: pd.DataFrame) -> pd.DataFrame:
    sub = C[C.need.isin(["Availability / stock", "Delivery enquiries"])]
    rows = []
    for city, rx in CITY_RE.items():
        m = sub.comment_text.str.lower().str.contains(rx, regex=True)
        rows.append(dict(city=city, mentions=int(m.sum()),
                         availability=int((m & (sub.need == "Availability / stock")).sum()),
                         delivery_enquiries=int((m & (sub.need == "Delivery enquiries")).sum())))
    out = pd.DataFrame(rows).sort_values("mentions", ascending=False)
    out["share"] = out.mentions / max(out.mentions.sum(), 1)
    return out.reset_index(drop=True)


# ============================================================================== Q5 recommendations
def _n_per_arm(sd, lift=.25):
    return int(np.ceil(2 * (1.96 + 0.84) ** 2 * sd ** 2 / np.log(1 + lift) ** 2))


def recommendations(P, C, anomalies, sd_log=0.5):
    """Evidence-based actions. Every item carries the numbers that triggered it."""
    recs, tot = [], max(len(C), 1)
    shares = C.need.value_counts(normalize=True).reindex(NEEDS).fillna(0)
    M = P[P.days_since_post >= MATURE_DAYS]
    J = C.merge(P[["post_id", "brand", "platform", "campaign", "content_type"]], on="post_id")

    def hot(dim, need, lift=1.4, min_n=150):
        t = pd.crosstab(J[dim], J.need == need); n = t.sum(1); s = t[True] / n
        base = (J.need == need).mean()
        return [(k, s[k], s[k] / base) for k in s.index if n[k] >= min_n and s[k] / base >= lift and s[k] > .03]

    # --- content
    pc = content_performance(P, ("platform", "content_type"))
    if not pc.empty:
        for plat, g in pc.groupby("platform"):
            g = g[g.posts >= 10].sort_values("eng_index", ascending=False)
            if len(g) < 2:
                continue
            b = g.iloc[0]
            low = g[(g.role == "Rethink")]                       # low attention AND low buying signals
            w = low.iloc[-1] if len(low) else None
            conv = g[(g.role == "Hidden converter")]
            ref = w if w is not None else g.iloc[-1]
            strong = b.ci_low > ref.ci_high
            ev = f"Median engagement index {b.eng_index:.2f} for {b.content_type} (90% CI {b.ci_low:.2f}-{b.ci_high:.2f}) vs {ref.eng_index:.2f} for {ref.content_type} ({int(b.posts)} vs {int(ref.posts)} posts). Evidence: {'strong (intervals do not overlap)' if strong else 'moderate (intervals overlap)'}."
            if w is not None:
                title = f"{plat}: lead with {b.content_type}s, cut back {w.content_type}s"
                act = f"Shift about 15-20% of {plat} posting slots from {w.content_type}s (low attention and few buying signals) to {b.content_type}s for the next campaign and re-measure."
            else:
                keep = ", ".join(conv.content_type) if len(conv) else ref.content_type
                title = f"{plat}: lead with {b.content_type}s, keep {keep} for conversion"
                act = f"Use {b.content_type}s for reach, but do not drop {keep}: they get less attention yet carry more buying-signal comments."
            recs.append(dict(area="Content", points=(28 if strong else 14) * (P.platform == plat).mean(),
                             title=title, evidence=ev, action=act, metric="Engagement index per post; buying-signal rate"))
    ct = content_performance(P, ("content_type",))
    if not ct.empty:
        for _, r in ct[ct.role == "Hidden converter"].iterrows():
            recs.append(dict(area="Content", points=9, title=f"{r.content_type}s convert better than they attract",
                evidence=f"Buying-signal comments are {r.buying_signal_rate:.0%} of comments (all posts: {M.buying_signals.sum() / max(M.n_sampled.sum(), 1):.0%}) but engagement index is only {r.eng_index:.2f}.",
                action=f"Give {r.content_type}s paid reach or influencer cross-posting; they reach fewer people but the ones reached want to buy.", metric="Buying-signal comments per 1,000 likes"))
        for _, r in ct[ct.role == "Awareness only"].iterrows():
            recs.append(dict(area="Content", points=7, title=f"{r.content_type}s get attention but little buying intent",
                evidence=f"Engagement index {r.eng_index:.2f} (above typical) but only {r.buying_signal_rate:.0%} of comments show buying signals.",
                action=f"Add a clear call to action on {r.content_type}s (price in caption, 'DM to order', shop link in bio).", metric="Buying-signal rate"))

    # --- promotions
    ds = shares["Discount seekers"]
    cam = need_mix(C, P, "campaign")[1]["Discount seekers"].dropna().sort_values(ascending=False) if len(C) else pd.Series(dtype=float)
    if ds > .03:
        topc = J[J.need == "Discount seekers"].content_type.value_counts(normalize=True)
        extra = f" Most of them comment on {topc.index[0]}s ({topc.iloc[0]:.0%})." if len(topc) else ""
        lead = f" Highest in {cam.index[0]} ({cam.iloc[0]:.1f}x average)." if len(cam) and cam.iloc[0] > 1.15 else ""
        recs.append(dict(area="Promotions", points=ds * 100 * 1.3, title="Answer discount requests before they are asked",
            evidence=f"{ds:.0%} of comments ask about discounts, codes or sales.{lead}{extra}",
            action="Put the offer or code in the caption and pinned comment of sale posts, and test a bundle offer against a flat percentage discount.",
            metric="Discount-request share; conversion on promo code"))

    # --- customer service
    dc = shares["Delivery complaints"]
    if dc > .02:
        spots = []
        for dim in ("brand", "platform", "campaign"):
            spots += [f"{k} ({s:.0%}, {l:.1f}x)" for k, s, l in hot(dim, "Delivery complaints")]
        storms = anomalies[anomalies.anomaly_type == "complaint_storm"] if len(anomalies) else anomalies
        recs.append(dict(area="Customer service", points=dc * 100 * 1.6 + 2 * min(len(storms), 10),
            title="Fix late-delivery complaints; reply on storm posts first",
            evidence=f"{dc:.0%} of comments are delivery complaints." + (f" Hot spots: {', '.join(spots[:4])}." if spots else "") + f" {len(storms)} posts are complaint storms (far more complaints than comparable posts).",
            action="Assign support to reply within 2 hours on storm posts, pin a delivery-timeline note on sale posts, and review courier performance for the hot-spot brands/campaigns.",
            metric="Delivery-complaint share; first-reply time"))
    de = shares["Delivery enquiries"]
    if de > .03:
        recs.append(dict(area="Customer service", points=de * 100 * .8, title="Publish delivery times and charges up front",
            evidence=f"{de:.0%} of comments ask how long delivery takes, what it costs or whether it arrives before Eid.",
            action="Add delivery days by city and the cash-on-delivery option to captions and highlights.", metric="Delivery-enquiry share"))

    # --- availability
    av = shares["Availability / stock"]
    cd = city_demand(C, P)
    if av > .03:
        tops = ", ".join(f"{r.city} ({r.share:.0%})" for r in cd.head(3).itertuples()) if cd.mentions.sum() else "n/a"
        spots = [f"{k} ({s:.0%})" for k, s, l in hot("brand", "Availability / stock")]
        recs.append(dict(area="Product & stock", points=av * 100, title="Close stock and city-availability gaps",
            evidence=f"{av:.0%} of comments ask if the item is available. Most-named cities: {tops}." + (f" Brands above average: {', '.join(spots)}." if spots else ""),
            action="Show 'in stock / sold out' and city availability on posts; restock the sizes and cities named most; consider a waitlist or pre-order.", metric="Availability-enquiry share"))

    # --- price
    pcmp = shares["Price complaints"]
    if pcmp > .02:
        spots = [f"{k} ({s:.0%}, {l:.1f}x)" for dim in ("platform", "brand") for k, s, l in hot(dim, "Price complaints")]
        recs.append(dict(area="Promotions", points=pcmp * 100 * 1.1, title="Reframe value where price pushback is high",
            evidence=f"{pcmp:.0%} of comments say the price is too high." + (f" Strongest: {', '.join(spots[:3])}." if spots else ""),
            action="Test value framing (fabric details, cost per wear, instalment or bundle pricing) against the current price-only caption.", metric="Price-complaint share"))

    # --- spam
    sp = shares["Spam / promotion"]
    sb = anomalies[anomalies.anomaly_type == "spam_bot"] if len(anomalies) else anomalies
    if sp > .02 or len(sb):
        top = J[J.need == "Spam / promotion"].platform.value_counts(normalize=True)
        recs.append(dict(area="Customer service", points=sp * 100 * .6 + len(sb) * .1, title="Filter spam and fake-giveaway comments",
            evidence=f"{sp:.0%} of comments are spam/promotion" + (f", {top.iloc[0]:.0%} of them on {top.index[0]}" if len(top) else "") + f"; {len(sb)} posts are spam-flooded.",
            action="Turn on keyword filters (giveaway, follow, replica, DM for) and hide flagged comments so they do not bury real buyer questions.", metric="Spam share of comments"))

    # --- campaign testing
    n = _n_per_arm(sd_log)
    pcs = ct[ct.content_type == "Product Photo"] if not ct.empty else ct
    pe = J[J.content_type == "Product Photo"].need.eq("Price enquiries").mean() if len(J) else 0
    tests = [("Price in caption vs no price on Product Photos", f"{pe:.0%} of Product Photo comments just ask 'price?'", "Price-enquiry share, buying-signal rate"),
             ("'DM to order' / shop-link call to action vs none on Reels", "Reels attract praise but fewer buying signals than Sale Announcements", "Buying-signal comments per 1,000 likes"),
             ("Offer code in caption vs offer in image only on Sale Announcements", "Discount requests are the largest buying-signal group on sale posts", "Discount-request share, promo-code redemptions")]
    recs.append(dict(area="Campaign testing", points=6, title="Run three A/B tests next campaign",
        evidence="; ".join(f"{t} ({e})" for t, e, _ in tests) + ".",
        action=f"To detect a 25% lift in engagement you need about {n} posts per arm (log-engagement spread {sd_log:.2f}); for smaller teams, run each test across 3-4 weeks and several brands/platforms.",
        metric="; ".join(m for *_, m in tests)))

    recs.sort(key=lambda r: -r["points"])
    for i, r in enumerate(recs):
        r["priority"] = "High" if i < 3 else "Medium" if i < 6 else "Low"
    return recs


# ============================================================================== dashboard wrapper
def apply_filters(P, C, brand=None, platform=None, campaign=None):
    f = pd.Series(True, index=P.index)
    for col, v in (("brand", brand), ("platform", platform), ("campaign", campaign)):
        if v:
            f &= P[col] == v
    Pf = P[f]
    return Pf, C[C.post_id.isin(Pf.post_id)]
CONTENT_ORDER = ["Reel", "Styling Video", "Influencer Post", "Product Photo", "Sale Announcement", "Eid Campaign"]
