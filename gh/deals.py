"""Wöchentliche Top-Technik-Deals über /bestprice_development.

Eigenes Ranking (Deal-Score): prozentuale Preissenkung, gewichtet mit Preisniveau
(große Ersparnis in € zählt), Beliebtheit (Anzahl Angebote) und Allzeit-Bestpreis.
Pro Unterkategorie max. N Deals, damit die Liste abwechslungsreich bleibt.
"""
import math
import re

from . import config
from .catalog import product_url


def deal_score(d):
    pct = abs(d.get("change_in_percent") or 0)
    price = float(d.get("best_price") or 0)
    offers = float(d.get("offer_count") or 1)
    s = pct * math.log10(price + 10) * (1 + min(offers, 60) / 60)
    if d.get("alltime_best"):
        s *= 1.35
    return s


def collect(catalog, api):
    s = config.DEAL_SETTINGS
    raw = {}
    for m, title in catalog.top_categories():
        if m is None or not re.search(config.DEAL_TOPCATS, title, re.I):
            continue
        for top_deal in (True, False):
            resp = api.bestprice_development(
                m=m, interval=s["interval"], pricemin=s["pricemin"],
                drop_percentmin=s["drop_percentmin"], v=2, sort="pp",
                limit=s["per_topcat"], top_deal=top_deal)
            deals = resp.get("deals") or []
            for d in deals:
                d["_top"] = title
                raw.setdefault(d["id"], d)
            if len(deals) >= 20:
                break  # genug Top-Deals, kein Fallback nötig
    ranked = sorted(raw.values(), key=deal_score, reverse=True)
    per_mid, out = {}, []
    for d in ranked:
        mid = d.get("middle_category_name") or d.get("cat")
        if per_mid.get(mid, 0) >= s["max_per_midcat"]:
            continue
        per_mid[mid] = per_mid.get(mid, 0) + 1
        price = float(d["best_price"])
        pct = float(d.get("change_in_percent") or 0)
        out.append({
            "id": d["id"], "name": d["product"], "price": round(price, 2),
            "old_price": round(price / (1 + pct / 100), 2) if -100 < pct < 0 else None,
            "percent": d.get("change_in_percent"), "alltime_best": bool(d.get("alltime_best")),
            "category": d.get("category_path") or d.get("cat_name"), "section": d["_top"],
            "merchant": d.get("hname"), "image": d.get("image_thumb"), "url": product_url(d["id"]),
            "score": round(deal_score(d), 1),
        })
        if len(out) >= s["top_n"]:
            break
    return out
