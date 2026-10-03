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

from gh import amazon, autoimg, config, deals, legal, links, og, pages, render, survey
from gh.builder import Builder
from gh.catalog import Catalog

HISTORY = Path("data/history.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Beispieldaten statt echter API")
    ap.add_argument("--out", default="site")
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

    print("→ Amazon-Deals")
    amazon_active = args.mock or amazon.load_event()["active"]  # nur im Aktionszeitraum (content/amazon.json)
    amazon_list, asins, info = amazon.collect(catalog, api, offline=args.mock, active=amazon_active)
    print("   " + info)
    gha("notice", "Amazon: " + info)

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
    dbg["tree"] = [(c, p) for c, p, _ in catalog.flat() if c and p.startswith("Hardware")]
    gha("notice", "Kategorien: " + "; ".join(f"{k}={v}" for k, v in catalog._cats.items()))
    gha("notice", "Produkte: " + "; ".join(f"{k}={v['count']}" for k, v in dbg["lists"].items()))
    for t, v in builder.debug.items():
        gha("notice", f"{t}: Basisteile {json.dumps(v.get('parts'), ensure_ascii=False)[:900]} | günstigste {v.get('cheapest', [])[:2]}")
    Path("data").mkdir(exist_ok=True)
    if not args.mock:
        Path("data/debug.json").write_text(json.dumps(dbg, ensure_ascii=False, indent=1), encoding="utf-8")

    localize_images(builds, deal_list + amazon_list, Path(args.out), offline=args.mock)

    history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() and not args.mock else None
    render.write_site(args.out, builds, deal_list, history, stamp + (" (BEISPIELDATEN)" if args.mock else ""))
    links.AUTO = autoimg.build(args.out, autoimg.load_groups(), offline=args.mock)  # Vorschaubilder für Links ohne Bild
    links.AUTO_TITLES = autoimg.build_titles(args.out, autoimg.load_groups(), offline=args.mock)  # Titel für Links ohne Titel
    gha("notice", f"Auto-Bilder: {len(links.AUTO)}")
    links.write(args.out, stamp)
    legal.write(args.out)
    pages.write(args.out)
    survey.write(args.out)  # versteckte Umfrage, nirgends verlinkt
    amazon.write(args.out, amazon_list, asins, config.TIERS, stamp, amazon_active, offline=args.mock, api=api)
    og.write_all(args.out, builds, deal_list, config.TIERS)
    import shutil
    for d in ("admin", "app"):  # Bearbeitungs-App + Ersatz-Editor
        if Path(d).exists():
            shutil.copytree(d, Path(args.out) / d, dirs_exist_ok=True)
    weekly = os.environ.get("WEEKLY_RUN", "true") == "true"  # nur der Wochenlauf schreibt den Vorwochen-Vergleich
    if not args.mock and builds and weekly:
        HISTORY.parent.mkdir(exist_ok=True)
        HISTORY.write_text(json.dumps({"updated": stamp, "builds": builds}, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"Fertig: {args.out}/ · API-Aufrufe: {api.calls}")
    return 0 if builds else 1


def localize_images(builds, deal_list, out, offline=False):
    """Produktbilder einmal herunterladen und selbst ausliefern.
    So bekommt kein fremder Server die IP-Adressen der Besucher mit."""
    import requests
    from urllib.parse import urlparse
    items = [p for b in builds for p in b["parts"]] + deal_list
    (out / "img").mkdir(parents=True, exist_ok=True)
    for it in items:
        url, it["image"] = it.get("image"), None
        if offline or not url or not it.get("id"):
            continue
        url = "https:" + url if url.startswith("//") else url
        host = urlparse(url).hostname or ""
        ext = Path(urlparse(url).path).suffix.lower()
        if not (host == "gzhls.at" or host.endswith(".gzhls.at")) or ext not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        target = out / "img" / f"{int(it['id'])}{ext}"
        try:
            if not target.exists():
                r = requests.get(url, timeout=20)
                if r.status_code != 200 or len(r.content) > 2_000_000:
                    continue
                target.write_bytes(r.content)
            it["image"] = f"/img/{target.name}"
        except requests.RequestException:
            continue


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
