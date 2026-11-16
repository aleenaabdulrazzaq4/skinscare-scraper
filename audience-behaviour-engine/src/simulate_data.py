"""
simulate_data.py
----------------
Generates a SIMULATED social-media dataset for a Pakistani women's-lawn-suit market
(Brand A-E on Instagram, TikTok and Facebook), following Table A (posts) and Table B (comments)
of the project brief. Nothing here comes from real brands; every file carries data_source=simulated.

What is planted (the engine must rediscover it without being told):
  * content types differ: Sale Announcements attract price/discount talk, Styling Videos get shares, ...
  * audience needs differ by campaign (11.11 / 12.12 -> discount + late-delivery comments) and brand
    (Brand C has a delivery problem, Brand D has stock/availability gaps)
  * ~4% anomalous posts: viral, flop, complaint_storm, spam_bot (ground truth saved separately)
  * comments in English, Roman Urdu (with spelling variants) and Urdu script, with emojis and typos

Usage:  python simulate_data.py --posts 3000 --out ../data
"""
import argparse
import os
import re

import numpy as np
import pandas as pd

COLLECTION_DATE = pd.Timestamp("2026-11-15")
BRANDS = ["Brand A", "Brand B", "Brand C", "Brand D", "Brand E"]
PLATFORMS = ["Instagram", "TikTok", "Facebook"]
CAMPAIGNS = ["Eid Collection", "11.11 Sale", "12.12 Sale", "Summer Lawn", "Winter Collection"]
CONTENT = ["Reel", "Product Photo", "Influencer Post", "Styling Video", "Sale Announcement", "Eid Campaign"]
CITIES = ["Karachi", "Lahore", "Islamabad", "Multan", "Peshawar", "Faisalabad", "Quetta", "Rawalpindi", "Sialkot", "Hyderabad"]
CITY_W = [0.22, 0.20, 0.12, 0.09, 0.08, 0.08, 0.05, 0.07, 0.05, 0.04]
CITY_UR = {"Karachi": "کراچی", "Lahore": "لاہور", "Islamabad": "اسلام آباد", "Multan": "ملتان", "Peshawar": "پشاور",
           "Faisalabad": "فیصل آباد", "Quetta": "کوئٹہ", "Rawalpindi": "راولپنڈی", "Sialkot": "سیالکوٹ", "Hyderabad": "حیدرآباد"}
PRODUCTS = ["suit", "lawn suit", "dress", "3 piece", "unstitched suit"]

# ------------------------------------------------------------------ comment templates
# topic -> language -> list of (text, sentiment)
T = {
 "price_inquiry": {
  "English": ["Price please?", "What is the price of this {prod}?", "price?", "How much for this {prod}", "Kindly tell the price",
              "Can you share the price list?", "price pls", "How much is the 3 piece?"],
  "Roman Urdu": ["Price bataein?", "Iski price kya hai", "Rate kitna hai is suit ka?", "price btao", "Kitne ka hai ye?",
                 "Price list inbox karein", "Is ka rate bata dein plz"],
  "Urdu": ["قیمت کیا ہے؟", "اس کی قیمت بتائیں", "ریٹ کتنا ہے؟", "قیمت بتا دیں پلیز"]},
 "price_complaint": {
  "English": ["Price is too high for this quality", "Way too expensive", "Why so expensive? Last year it was cheaper",
              "Prices have gone crazy", "Not worth this price", "Overpriced honestly"],
  "Roman Urdu": ["Price bohat zyada hai", "Bohat mehnga hai ye to", "Itna mehnga kyun hai?", "Qeemat bohat zyada hai quality ke hisab se",
                 "Ye price to ghalat hai", "Har saal rate barh jata hai"],
  "Urdu": ["قیمت بہت زیادہ ہے", "بہت مہنگا ہے", "اتنا مہنگا کیوں ہے؟", "کوالٹی کے حساب سے قیمت غلط ہے"]},
 "fabric_pos": {
  "English": ["Fabric looks so soft and premium", "Love the lawn quality", "Quality is really good, bought last season"],
  "Roman Urdu": ["Kapra bohat acha hai", "Lawn ki quality zabardast hai", "Fabric bohat soft hai"],
  "Urdu": ["کپڑا بہت اچھا ہے", "لان کی کوالٹی زبردست ہے"]},
 "fabric_neg": {
  "English": ["Fabric quality has gone down", "The material felt cheap last time", "Color faded after one wash", "Fabric is too thin"],
  "Roman Urdu": ["Kapra pehle jaisa nahi raha", "Quality bohat kharab hai ab", "Rang ek wash mein utar gaya", "Kapra bohat patla hai"],
  "Urdu": ["کپڑا پہلے جیسا نہیں رہا", "کوالٹی بہت خراب ہے", "رنگ دھلنے پر اتر گیا"]},
 "sizing": {
  "English": ["What sizes are available?", "Is this available in XL?", "Size chart please", "Is the shirt length long?",
              "Do you have stitched in medium?", "Does it shrink after wash?"],
  "Roman Urdu": ["Size chart bhej dein", "XL size mil jayega?", "Medium size available hai?", "Kameez ki length kitni hai?",
                 "Wash ke baad shrink to nahi hota?", "Stitched mein kaun se size hain?"],
  "Urdu": ["سائز چارٹ بھیجیں", "ایکس ایل سائز مل جائے گا؟", "قمیض کی لمبائی کتنی ہے؟"]},
 "delivery_inquiry": {
  "English": ["How many days for delivery?", "Do you deliver to {city}?", "Delivery charges to {city}?", "Will it arrive before Eid?",
              "Is cash on delivery available?", "How long will delivery take?"],
  "Roman Urdu": ["Delivery kitne din mein hogi?", "{city} mein delivery hoti hai?", "Delivery charges kitne hain?", "Eid se pehle mil jayega?",
                 "Cash on delivery hai?", "Parcel kitne din mein pohnchega?"],
  "Urdu": ["ڈیلیوری کتنے دن میں ہوگی؟", "{city} میں ڈیلیوری ہوتی ہے؟", "ڈیلیوری چارجز کتنے ہیں؟"]},
 "delivery_complaint": {
  "English": ["Ordered {days} days ago still waiting", "Order not received yet", "Worst delivery service, very late",
              "Tracking not updating since a week", "Where is my order? No reply from support", "Parcel delayed again"],
  "Roman Urdu": ["{days} din pehle order kiya tha abhi tak nahi aaya", "Order abhi tak receive nahi hua", "Bohat late delivery hai",
                 "Tracking update nahi ho rahi", "Mera parcel kahan hai? Koi reply nahi", "Delivery mein bohat der kar di"],
  "Urdu": ["آرڈر ابھی تک نہیں ملا", "{days} دن پہلے آرڈر کیا تھا ابھی تک انتظار ہے", "ڈیلیوری بہت لیٹ ہے", "ٹریکنگ اپڈیٹ نہیں ہو رہی"]},
 "discount_request": {
  "English": ["Any discount on this suit?", "Is there a sale going on?", "Please give a discount code", "Will this go on sale soon?",
              "Any bundle offer?", "Do you have a student discount?", "Promo code please"],
  "Roman Urdu": ["Koi discount milega?", "Sale kab lag rahi hai?", "Discount code dein plz", "Kuch off milega is par?",
                 "Bundle offer hai koi?", "Sale mein ayega ye?", "Promo code bata dein"],
  "Urdu": ["کوئی ڈسکاؤنٹ ملے گا؟", "سیل کب لگے گی؟", "ڈسکاؤنٹ کوڈ دیں", "کوئی آفر ہے؟"]},
 "availability": {
  "English": ["Is this available in {city}?", "Is it in stock?", "Is this available in your {city} outlet?",
              "When will it be back in stock?", "Sold out already?", "Is this available online?"],
  "Roman Urdu": ["{city} mein available hai?", "Stock mein hai ye?", "{city} outlet mein mil jayega?",
                 "Dobara kab ayega stock?", "Sold out ho gaya?", "Online available hai ye?"],
  "Urdu": ["کیا یہ {city} میں دستیاب ہے؟", "اسٹاک میں ہے؟", "دوبارہ اسٹاک کب آئے گا؟"]},
 "purchase_intent": {
  "English": ["Just ordered mine!", "Ordering this today", "Inbox me details", "How do I order this?", "I want this, sending DM",
              "Booking 2 sets", "Adding to cart now"],
  "Roman Urdu": ["Maine order kar diya!", "Aaj order karti hoon", "Inbox me details send kar dein", "Order kaise karna hai?",
                 "Mujhe ye chahiye, DM kar rahi hoon", "2 suits book kar dein", "Cart mein add kar diya"],
  "Urdu": ["میں نے آرڈر کر دیا", "ان باکس میں تفصیل بھیجیں", "آرڈر کیسے کرنا ہے؟", "مجھے یہ چاہیے"]},
 "praise": {
  "English": ["Very beautiful dress!", "Gorgeous!!", "Love this collection", "Stunning colors", "Beautiful, my favourite",
              "So elegant", "Masterpiece"],
  "Roman Urdu": ["Bohat khoobsurat dress!", "Mashallah bohat piyara", "Boht pyara collection hai", "Rang kamal ke hain",
                 "Zabardast!", "Sab se achi collection", "Bohat hi elegant"],
  "Urdu": ["بہت خوبصورت!", "ماشاءاللہ بہت پیارا", "زبردست کلیکشن", "بہت ہی خوبصورت رنگ"]},
 "spam": {
  "English": ["Follow me for free giveaway", "Check my page for cheap replicas", "DM for promotion, 5000 followers in 1 day",
              "Win free iPhone click link", "Great post, visit my profile", "Earn money from home, message me"],
  "Roman Urdu": ["Free giveaway ke liye follow karein", "Sasti replica ke liye mera page dekhein", "Followers chahiye? DM karein",
                 "Link par click karke iphone jeetein", "Ghar baithe paisay kamayein, message karein"],
  "Urdu": ["فری گفٹ کے لیے فالو کریں", "فالوورز چاہیے؟ ڈی ایم کریں", "گھر بیٹھے پیسے کمائیں"]},
}
TOPIC_ORDER = ["price_inquiry", "price_complaint", "fabric_quality", "sizing", "delivery_inquiry", "delivery_complaint",
               "discount_request", "availability", "purchase_intent", "praise", "spam"]
BASE_W = dict(zip(TOPIC_ORDER, [.12, .05, .08, .07, .07, .04, .08, .07, .07, .33, .02]))
INTENT = {"purchase_intent": "High intent", "delivery_complaint": "Post-purchase issue",
          **{t: "Possible inquiry" for t in ["price_inquiry", "sizing", "delivery_inquiry", "discount_request", "availability"]}}
SENT = {"price_inquiry": "Neutral", "sizing": "Neutral", "delivery_inquiry": "Neutral", "discount_request": "Neutral",
        "availability": "Neutral", "purchase_intent": "Positive", "praise": "Positive", "spam": "Neutral",
        "price_complaint": "Negative", "delivery_complaint": "Negative"}

# topic multipliers by content type / campaign / platform / brand
CONTENT_TOPIC = {
 "Sale Announcement": dict(price_inquiry=2.0, discount_request=3.5, availability=1.8, praise=.35, purchase_intent=1.2),
 "Product Photo": dict(fabric_quality=2.0, sizing=2.2, price_inquiry=1.4, praise=.8),
 "Reel": dict(praise=1.4, purchase_intent=1.2, spam=1.5),
 "Influencer Post": dict(praise=1.3, purchase_intent=1.6, price_inquiry=1.3, spam=2.0),
 "Styling Video": dict(sizing=1.8, fabric_quality=1.5, praise=1.2),
 "Eid Campaign": dict(delivery_inquiry=2.5, availability=1.8, purchase_intent=1.4, praise=1.1),
}
CAMPAIGN_TOPIC = {
 "11.11 Sale": dict(discount_request=1.8, delivery_complaint=2.0, price_inquiry=1.3),
 "12.12 Sale": dict(discount_request=1.8, delivery_complaint=2.2, price_inquiry=1.3),
 "Eid Collection": dict(delivery_inquiry=1.5, availability=1.5),
 "Winter Collection": dict(price_complaint=1.5, fabric_quality=1.3),
}
PLATFORM_TOPIC = {"TikTok": dict(praise=1.3, spam=2.5, price_complaint=.7), "Facebook": dict(price_complaint=1.8, delivery_complaint=1.4, praise=.7)}
BRAND_TOPIC = {"Brand C": dict(delivery_complaint=2.8), "Brand D": dict(availability=2.6), "Brand E": dict(price_complaint=1.8)}
LANG_W = {"Instagram": [.45, .42, .13], "TikTok": [.25, .62, .13], "Facebook": [.42, .38, .20]}   # English, Roman Urdu, Urdu
LANGS = ["English", "Roman Urdu", "Urdu"]

# engagement model: content -> (view mult, like rate, comment rate, share rate)
CONTENT_FX = {"Reel": (1.6, .045, .0035, .0040), "Product Photo": (.7, .060, .0030, .0015),
              "Influencer Post": (1.3, .040, .0060, .0030), "Styling Video": (1.0, .050, .0030, .0075),
              "Sale Announcement": (.9, .030, .0100, .0010), "Eid Campaign": (1.2, .052, .0045, .0035)}
PLAT_FX = {"Instagram": (1.0, 1.0, 1.0, 1.0), "TikTok": (3.0, .7, .9, 1.3), "Facebook": (.6, .6, .8, 1.2)}  # view, like, comment, share
CAMPAIGN_FX = {"Eid Collection": 1.25, "11.11 Sale": 1.2, "12.12 Sale": 1.2, "Summer Lawn": 1.0, "Winter Collection": .9}

RU_VARIANTS = [(r"\bkitne\b", ["kitne", "kitney", "kitny"]), (r"\bbohat\b", ["bohat", "bohot", "boht", "bahut"]),
               (r"\bplz\b", ["plz", "pls", "please"]), (r"\bnahi\b", ["nahi", "nai", "nhi"]), (r"\bhai\b", ["hai", "hy", "he"]),
               (r"\bmein\b", ["mein", "main", "me"]), (r"\bkya\b", ["kya", "kia"]), (r"\bdein\b", ["dein", "den", "dain"])]
EMOJI = ["😍", "❤️", "🔥", "😭", "🙏", "👌", "😊", "✨", "🥰", "😡", "🙄", "💕"]


def noisy(text, lang, rng):
    if lang == "Roman Urdu":
        for pat, opts in RU_VARIANTS:
            if rng.random() < .5:
                text = re.sub(pat, str(rng.choice(opts)), text, flags=re.I)
    if lang != "Urdu":
        r = rng.random()
        if r < .25: text = text.lower()
        elif r < .30: text = text.upper()
        if rng.random() < .10: text = text.rstrip("?!.")
        if rng.random() < .06: text = re.sub(r"(e|o|a)\b", r"\1\1\1", text, count=1)       # pleaseee / sooo
        if rng.random() < .05 and len(text) > 6:                                          # typo: swap two letters
            i = int(rng.integers(1, len(text) - 2)); text = text[:i] + text[i + 1] + text[i] + text[i + 2:]
    if rng.random() < .28:
        text += " " + "".join(rng.choice(EMOJI, size=int(rng.integers(1, 3))))
    return text


def topic_probs(content, campaign, platform, brand, days, mode=None):
    w = dict(BASE_W)
    for d in (CONTENT_TOPIC.get(content, {}), CAMPAIGN_TOPIC.get(campaign, {}), PLATFORM_TOPIC.get(platform, {}), BRAND_TOPIC.get(brand, {})):
        for k, v in d.items():
            w[k] *= v
    if "Sale" in campaign:
        w["delivery_complaint"] *= 1 + days / 30                        # late-delivery complaints build up over time
    if mode == "storm":
        w = {k: (60.0 if k == "delivery_complaint" else v * .15) for k, v in w.items()}
    elif mode == "spam":
        w = {k: (40.0 if k == "spam" else v * .25) for k, v in w.items()}
    p = np.array([w[t] for t in TOPIC_ORDER]); return p / p.sum()


def make_comment(topic, lang, rng):
    key = topic
    sentiment = SENT.get(topic)
    if topic == "fabric_quality":
        pos = rng.random() < .6
        key, sentiment = ("fabric_pos", "Positive") if pos else ("fabric_neg", "Negative")
    text = str(rng.choice(T[key][lang]))
    city = str(rng.choice(CITIES, p=CITY_W))
    text = text.replace("{prod}", str(rng.choice(PRODUCTS))).replace("{days}", str(int(rng.integers(5, 21))))
    text = text.replace("{city}", CITY_UR[city] if lang == "Urdu" else city)
    return noisy(text, lang, rng), sentiment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=3000)
    ap.add_argument("--out", default="../data")
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)

    followers = {(b, p): rng.lognormal(np.log({"Instagram": 400e3, "TikTok": 300e3, "Facebook": 600e3}[p]), .5)
                 for b in BRANDS for p in PLATFORMS}
    n = a.posts
    anomaly_kind = np.array(["normal"] * n, dtype=object)
    idx = rng.permutation(n)
    k = int(n * .04)
    for kind, share in [("viral", .33), ("flop", .25), ("complaint_storm", .21), ("spam_bot", .21)]:
        m = int(k * share); anomaly_kind[idx[:m]] = kind; idx = idx[m:]

    posts, comments = [], []
    for i in range(n):
        brand = str(rng.choice(BRANDS)); platform = str(rng.choice(PLATFORMS, p=[.45, .30, .25]))
        campaign = str(rng.choice(CAMPAIGNS, p=[.22, .20, .15, .23, .20]))
        pool = [c for c in CONTENT if not (platform == "TikTok" and c == "Product Photo")]
        w = np.array([{"Reel": .24, "Product Photo": .22, "Influencer Post": .15, "Styling Video": .13,
                       "Sale Announcement": .16, "Eid Campaign": .10}[c] for c in pool])
        if campaign != "Eid Collection":
            w[pool.index("Eid Campaign")] = 0.0
        else:
            w[pool.index("Eid Campaign")] *= 5
        content = str(rng.choice(pool, p=w / w.sum()))
        days = int(rng.integers(1, 91))
        vm, lr, cr, sr = CONTENT_FX[content]; pv, pl, pc, ps = PLAT_FX[platform]
        age = 1 - np.exp(-days / 4)
        views = followers[(brand, platform)] * .25 * vm * pv * CAMPAIGN_FX[campaign] * rng.lognormal(0, .55) * (.4 + .6 * age)
        likes = views * lr * pl * rng.lognormal(0, .25)
        ncom = views * cr * pc * rng.lognormal(0, .30)
        shares = views * sr * ps * rng.lognormal(0, .30)
        kind = anomaly_kind[i]
        if kind == "viral":
            f = rng.uniform(6, 12); views, likes, ncom, shares = views * f, likes * f, ncom * f * .8, shares * f * 1.2
        elif kind == "flop":
            f = rng.uniform(.04, .12); views, likes, ncom, shares = views * f, likes * f, ncom * f, shares * f
        elif kind == "complaint_storm":
            ncom *= rng.uniform(4, 6)
        elif kind == "spam_bot":
            ncom *= rng.uniform(4, 7)
        likes, ncom, shares, views = int(likes), max(int(ncom), 1), int(shares), int(views)
        video = content in ("Reel", "Styling Video") or platform == "TikTok" or (platform == "Facebook" and content == "Sale Announcement")
        has_views = video or rng.random() < .25
        pid = f"P{i + 1:04d}"
        posts.append(dict(post_id=pid, brand=brand, platform=platform, campaign=campaign, content_type=content,
                          product_category="Lawn suit", likes=likes, comments_count=ncom,
                          shares=shares if (platform != "Instagram" or rng.random() < .7) else np.nan,
                          views=views if has_views else np.nan, days_since_post=days,
                          post_date=(COLLECTION_DATE - pd.Timedelta(days=days)).date().isoformat(),
                          collection_date=COLLECTION_DATE.date().isoformat(), data_source="simulated"))
        mode = {"complaint_storm": "storm", "spam_bot": "spam"}.get(kind)
        nc = min(ncom, int(rng.integers(8, 16)) if mode else int(rng.integers(3, 13)))
        probs = topic_probs(content, campaign, platform, brand, days, mode)
        topics = rng.choice(TOPIC_ORDER, size=nc, p=probs)
        for t in topics:
            lang = str(rng.choice(LANGS, p=LANG_W[platform]))
            text, sent = make_comment(str(t), lang, rng)
            comments.append(dict(post_id=pid, comment_text=text, language_type=lang, topic=str(t), sentiment=sent,
                                 purchase_intent=INTENT.get(str(t), "No intent"), data_source="simulated"))
    posts = pd.DataFrame(posts)
    comments = pd.DataFrame(comments); comments.insert(0, "comment_id", [f"C{j + 1:06d}" for j in range(len(comments))])
    posts.to_csv(os.path.join(a.out, "posts.csv"), index=False)
    comments.to_csv(os.path.join(a.out, "comments.csv"), index=False)
    pd.DataFrame(dict(post_id=posts.post_id, anomaly_truth=anomaly_kind)).to_csv(os.path.join(a.out, "posts_truth.csv"), index=False)
    print(f"posts {len(posts):,}  comments {len(comments):,}  planted anomalies {(anomaly_kind != 'normal').sum()}")


if __name__ == "__main__":
    main()
