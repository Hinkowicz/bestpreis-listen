"""Einmalige Diagnose (wird wieder entfernt): Amazon-Angebote auf anderen Wegen finden."""
import json


def probe(catalog, api, gha):
    lines = []
    for key in ("gpu", "ssd"):
        try:
            cat = catalog.resolve(key)["cat"]
            for extra in ({"h_id": 4957}, {"merchant": 4957}):
                r = api.categorylist(cat, sort="p", limit=5, **extra)
                prods = r.get("products") or []
                lines.append(f"{key} {extra}: total={r.get('total')} n={len(prods)} keys={list(prods[0])[:25] if prods else []} "
                             f"h={[ (p.get('hname'), p.get('best_price')) for p in prods[:3]]}")
        except Exception as ex:
            lines.append(f"{key}: FEHLER {str(ex)[:150]}")
    gha("notice", "PROBE-A " + " | ".join(lines)[:3500])
    try:  # Suche per ASIN (ein Amazon-Produkt aus dem Setup)
        r = api.post("query_product", {"query": "B075S9ZRVZ", "type": "asin", "params": {"add_asin": True}})
        gha("notice", "PROBE-B " + json.dumps(r, ensure_ascii=False)[:1500])
    except Exception as ex:
        gha("notice", f"PROBE-B FEHLER {str(ex)[:300]}")
