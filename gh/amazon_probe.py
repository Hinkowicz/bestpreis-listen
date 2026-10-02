"""Einmalige Diagnose (wird wieder entfernt)."""
import json
import re

from . import config


def probe(catalog, api, gha):
    tops = [(m, t) for m, t in catalog.top_categories() if m is not None and re.search(config.DEAL_TOPCATS, t, re.I)]
    m, title = tops[0]
    resp = api.bestprice_development(m=m, interval="31d", v=2, limit=3)
    mers = resp.get("merchants") or []
    gha("notice", f"PROBE {title}: keys={list(resp)} merchants={len(mers)} amazon={[x for x in mers if 'mazon' in json.dumps(x)]}")
    gha("notice", f"PROBE erster Deal: {json.dumps((resp.get('deals') or [{}])[0], ensure_ascii=False)[:900]}")
    for x in [x for x in mers if 'mazon' in json.dumps(x)][:3]:
        for params in ({"h_id": int(x["id"])}, {"h_id": str(x["id"])}, {"h_id": int(x["id"]), "interval": "7d"}):
            r = api.bestprice_development(m=m, v=2, limit=5, **{"interval": "31d", **params})
            d = r.get("deals") or []
            gha("notice", f"PROBE {params}: {len(d)} deals {[ (y.get('hname'), y.get('change_in_percent')) for y in d[:5]]}")
    # ohne Händlerfilter: wie oft ist Amazon günstigster Händler?
    r = api.bestprice_development(m=m, interval="31d", v=2, limit=100, drop_percentmin=10)
    d = r.get("deals") or []
    hn = {}
    for y in d:
        hn[y.get("hname")] = hn.get(y.get("hname"), 0) + 1
    gha("notice", f"PROBE ohne Filter: {len(d)} deals, Händler {sorted(hn.items(), key=lambda kv: -kv[1])[:12]} h_ids {[y.get('h_id') for y in d if 'mazon' in str(y.get('hname'))][:5]}")
    if d:
        r = api.post("query_product", {"query": str(d[0]["id"]), "type": "id", "params": {"add_asin": True}})
        gha("notice", f"PROBE query_product: {json.dumps(r, ensure_ascii=False)[:1500]}")
