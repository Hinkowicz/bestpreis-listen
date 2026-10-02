"""Einmalige Diagnose (wird wieder entfernt)."""
import json
import re

from . import config


def probe(catalog, api, gha):
    tops = [(m, t) for m, t in catalog.top_categories() if m is not None and re.search(config.DEAL_TOPCATS, t, re.I)]
    m, title = tops[0]
    lines = []
    for params in ({"h_id": [4957]}, {"h_id": 4957, "top_deal": False}, {"h_id": 4957, "m": None}):
        p = {"m": m, "interval": "31d", "v": 2, "limit": 5, **params}
        p = {k: v for k, v in p.items() if v is not None}
        try:
            r = api.bestprice_development(**p)
            lines.append(f"{params}: total={r.get('total')} n={len(r.get('deals') or [])}")
        except Exception as ex:
            lines.append(f"{params}: FEHLER {ex}")
    for lim in (100, 500):
        try:
            r = api.bestprice_development(m=m, interval="31d", v=2, limit=lim)
            d = r.get("deals") or []
            am = [y for y in d if "mazon" in str(y.get("hname"))]
            lines.append(f"limit={lim}: total={r.get('total')} n={len(d)} amazon={len(am)} pager={r.get('pager')} h_ids={sorted({str(y.get('h_id')) for y in am})}")
        except Exception as ex:
            lines.append(f"limit={lim}: FEHLER {ex}")
    gha("notice", "PROBE1 " + " | ".join(lines))
    try:
        r = api.post("query_product", {"query": str(am[0]["id"] if am else d[0]["id"]), "type": "id", "params": {"add_asin": True}})
        gha("notice", f"PROBE2 query_product: {json.dumps(r, ensure_ascii=False)[:2500]}")
    except Exception as ex:
        gha("notice", f"PROBE2 FEHLER {ex}")
