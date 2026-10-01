#!/usr/bin/env python3
"""Wöchentlicher Lauf: PC-Listen + Deals berechnen und Seiten erzeugen.

  python run.py                 # echte API (GEIZHALS_USER / GEIZHALS_SECRET aus der Umgebung)
  python run.py --mock          # Vorschau mit Beispieldaten
  python run.py --out site      # Ausgabeordner (Standard: site)
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from gh import config, deals, render
from gh.builder import Builder
from gh.catalog import Catalog

HISTORY = Path("data/history.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Beispieldaten statt echter API")
    ap.add_argument("--out", default="site")
    ap.add_argument("--no-history", action="store_true", help="Vorwochen-Vergleich nicht aktualisieren")
    args = ap.parse_args()

    if args.mock:
        from gh.mock import MockAPI
        api = MockAPI()
    else:
        from gh.api import GeizhalsAPI
        api = GeizhalsAPI(os.environ.get("GEIZHALS_USER", "hinkowicz"), os.environ.get("GEIZHALS_SECRET"))

    catalog = Catalog(api)
    builder = Builder(catalog)
    stamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y, %H:%M Uhr")

    builds = []
    for tier in config.TIERS:
        print(f"→ PC bis {tier['budget']} €")
        b = builder.build_tier(tier)
        if b:
            msg = f"{tier['budget']} €: {b['total']:.0f} € · Score {b['score']} · {b['parts'][0]['note']} + {b['parts'][1]['note']}"
            print("   " + msg)
            gha("notice", msg)
            builds.append(b)
        else:
            print("   [warn] keine gültige Zusammenstellung gefunden")
            gha("warning", f"{tier['budget']} €: keine gültige Zusammenstellung")

    print("→ Deals")
    deal_list = deals.collect(catalog, api)
    print(f"   {len(deal_list)} Deals")
    gha("notice", f"{len(deal_list)} Deals, {api.calls} API-Aufrufe")

    # Diagnose-Daten (Preise je Kategorie, Kandidaten) fürs Feintuning
    dbg = {"tiers": builder.debug, "categories": catalog._cats, "lists": {}}
    for (key, sort, *_), prods in catalog._lists.items():
        cheap = sorted(prods, key=lambda p: float(p["best_price"]))
        dbg["lists"][f"{key}/{sort}"] = {"count": len(prods),
                                         "cheapest": [(p["product"], p["best_price"]) for p in cheap[:25]]}
    dbg["gpus"] = sorted([(g["chip"], g["vram"], float(p["best_price"]), p["product"]) for p, g in builder.gpus()],
                         key=lambda x: x[2])
    dbg["cpus"] = {plat: sorted([(c["chip"], float(p["best_price"]), p["product"]) for p, c in builder.cpus(plat)],
                                key=lambda x: x[1]) for plat in config.PLATFORMS}
    dbg["deals_sample"] = deal_list[:5]
    Path("data").mkdir(exist_ok=True)
    if not args.mock:
        Path("data/debug.json").write_text(json.dumps(dbg, ensure_ascii=False, indent=1), encoding="utf-8")

    history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() and not args.mock else None
    render.write_site(args.out, builds, deal_list, history, stamp + (" (BEISPIELDATEN)" if args.mock else ""))
    if not args.mock and not args.no_history:
        HISTORY.parent.mkdir(exist_ok=True)
        HISTORY.write_text(json.dumps({"updated": stamp, "builds": builds}, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"Fertig: {args.out}/ · API-Aufrufe: {api.calls}")
    return 0 if builds else 1


def gha(level, msg):
    """Meldung als GitHub-Annotation (im Actions-Run oben sichtbar)."""
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::{level}::" + str(msg).replace("%", "%25").replace("\r", "").replace("\n", "%0A"))


if __name__ == "__main__":
    import traceback
    try:
        code = main()
    except Exception as exc:
        gha("error", f"{type(exc).__name__}: {exc}\n" + "".join(traceback.format_exc()[-1500:]))
        raise
    sys.exit(code)
