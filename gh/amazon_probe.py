"""Einmalige Diagnose (wird wieder entfernt)."""
import json
import re

from . import config


def probe(catalog, api, gha):
    tops = [(m, t) for m, t in catalog.top_categories() if m is not None and re.search(config.DEAL_TOPCATS, t, re.I)]
    m, title = tops[0]
    lines = []
    variants = [{}, {"v": 2}, {"v": 2, "sort": "pp"}, {"page": 1}, {"v": 2, "limit": 100}, {"v": 2, "sort": "pp", "limit": 100, "drop_percentmin": 10, "pricemin": 15},
                {"loc": "de"}, {"hloc": ["de"]}]
    for extra in variants:
        p = {"m": m, "interval": "31d", "h_id": 4957, "limit": 20, **extra}
        try:
            r = api.post("bestprice_development", {"params": p}).get("response", {})
            lines.append(f"{extra}: total={r.get('total')} n={len(r.get('deals') or [])} iop={r.get('items_on_page')}")
        except Exception as ex:
            lines.append(f"{extra}: FEHLER {str(ex)[:120]}")
    gha("notice", "PROBE1 " + " | ".join(lines))
