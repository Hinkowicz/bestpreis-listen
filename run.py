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
            print(f"   {b['total']:.0f} € · Score {b['score']} · {b['parts'][0]['note']} + {b['parts'][1]['note']}")
            builds.append(b)
        else:
            print("   [warn] keine gültige Zusammenstellung gefunden")

    print("→ Deals")
    deal_list = deals.collect(catalog, api)
    print(f"   {len(deal_list)} Deals")

    history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() and not args.mock else None
    render.write_site(args.out, builds, deal_list, history, stamp + (" (BEISPIELDATEN)" if args.mock else ""))
    if not args.mock and not args.no_history:
        HISTORY.parent.mkdir(exist_ok=True)
        HISTORY.write_text(json.dumps({"updated": stamp, "builds": builds}, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"Fertig: {args.out}/ · API-Aufrufe: {api.calls}")
    return 0 if len(builds) == len(config.TIERS) else 1


if __name__ == "__main__":
    sys.exit(main())
