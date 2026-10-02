"""Erzeugt die statischen Seiten (index, pc-<budget>, deals) + JSON für den Discord-Bot."""
import html
import re
import json
from pathlib import Path

from . import config, og
from .theme import BASE

CSS = BASE + r"""
.wrap{max-width:1000px;margin:0 auto;padding:calc(14px + env(safe-area-inset-top)) 16px 0}
.top{display:flex;flex-wrap:wrap;gap:12px 16px;align-items:center;justify-content:space-between;margin-bottom:16px}
.brand{display:flex;flex-direction:column;align-items:flex-start;gap:4px;text-decoration:none}
.brand small{font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
.navbar{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:5px;border-radius:999px;max-width:100%}
.navbar::-webkit-scrollbar{display:none}
.navbar .chip{border:1px solid transparent}
h1{font-size:clamp(26px,6vw,38px);margin:8px 0 6px}h2{font-size:20px;margin:28px 0 10px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.card{display:block;padding:16px;text-decoration:none}
.price{font-size:26px;font-weight:800;letter-spacing:-.02em}
.score{display:inline-block;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;font-weight:800;
  border-radius:999px;padding:2px 10px;font-size:13px;box-shadow:inset 0 1px 0 rgba(255,255,255,.45)}
.parts{overflow:hidden;padding:0}
.row{display:grid;grid-template-columns:60px 1fr auto;gap:14px;align-items:center;padding:12px 16px;border-top:1px solid var(--edge)}
.row:first-child{border-top:0}
.row img,.noimg{width:60px;height:60px;object-fit:contain;background:#fff;border-radius:14px;display:block}
.noimg{background:var(--chip)}
.slot{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--faint)}
.pname{font-weight:650;line-height:1.3;overflow-wrap:anywhere}
.right{text-align:right;white-space:nowrap}.right .btn{margin-top:6px}
.total{display:flex;justify-content:space-between;align-items:center;padding:16px;font-size:20px;font-weight:800;
  border-top:1px solid var(--edge);background:linear-gradient(90deg,color-mix(in srgb,var(--accent) 14%,transparent),color-mix(in srgb,var(--accent2) 14%,transparent))}
.tip{padding:12px 16px;margin-top:12px;border-radius:18px}
.up{color:var(--bad)}.down{color:var(--good)}
details.explain{padding:12px 16px;margin-top:12px;border-radius:18px}
details.explain summary{cursor:pointer;font-weight:750;color:var(--accent)}details.explain p{margin:8px 0 0;color:var(--muted)}
.deal .old{color:var(--faint);font-size:13px;margin-left:6px}
.pct{color:var(--accent2);font-weight:800}
.badge{font-size:10px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-radius:999px;padding:2px 8px;font-weight:800}
.deal img,.deal .noimg{width:100%;height:150px;object-fit:contain;background:#fff;border-radius:16px;margin-bottom:10px}
.deal .btn{margin-top:10px}
.toplist{list-style:none;padding:0;margin:0;display:grid;gap:8px}
.toplist a{display:flex;justify-content:space-between;gap:12px;padding:12px 16px;border-radius:18px;text-decoration:none}
@media (max-width:560px){.row{grid-template-columns:48px 1fr}.row img,.row .noimg{width:48px;height:48px}
  .right{grid-column:2;text-align:left}.wordmark{height:36px}}
"""


SCORE_EXPLAIN = """<details class="explain glass"><summary>Was bedeutet der Hinko-Score?</summary>
<p>Der Hinko-Score zeigt, wie viel Gaming-Leistung ein PC bringt – im Vergleich zu einem Referenz-PC mit
<b>Ryzen 7 9800X3D + GeForce RTX 5070 = 100 Punkte</b>. Ein PC mit 120 ist also rund 20&nbsp;% schneller,
einer mit 60 erreicht etwa 60&nbsp;% der Bildrate.</p>
<p>Grundlage sind eigene Auswertungen öffentlicher Benchmarks in WQHD. Die Grafikkarte zählt je nach Budget
70–80&nbsp;%, der Prozessor den Rest; 32&nbsp;GB RAM gibt einen kleinen Bonus. Jede Woche wird pro Budget die
Kombination mit dem höchsten Score gesucht, die ins Budget passt.</p></details>"""


ASSETS = Path("assets")


def asset(name):
    """Erste vorhandene Datei assets/<name>.(png|jpg|jpeg|webp|svg) oder None."""
    for ext in ("png", "jpg", "jpeg", "webp", "svg"):
        f = ASSETS / f"{name}.{ext}"
        if f.exists():
            return f"/assets/{f.name}"
    return None


def logo_html():
    if asset("logo-dark") and asset("logo-light"):
        return ('<picture><source srcset="/assets/logo-light.png" media="(prefers-color-scheme: light)">'
                '<img class="wordmark" src="/assets/logo-dark.png" alt="Hinkowicz" width="321" height="48"></picture>')
    return ""


def head_icons():
    if not asset("favicon-32"):
        return ""
    return ('<link rel="icon" href="/assets/favicon.ico" sizes="any">'
            '<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">'
            '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><meta name="theme-color" content="#06070a">')


def legal_links():
    links = [(n, u) for n, u in (("Impressum", config.IMPRINT_URL), ("Datenschutz", config.PRIVACY_URL)) if u]
    return "".join(f' · <a href="{e(u)}">{n}</a>' for n, u in links)


def e(s):
    return html.escape(str(s if s is not None else ""))


def eur(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def img(url):
    if not url:
        return '<div class="noimg"></div>'
    if not re.fullmatch(r"/img/\d+\.(jpg|jpeg|png|webp)", url):  # nur selbst gehostete Bilder
        return '<div class="noimg"></div>'
    return f'<img src="{e(url)}" alt="" loading="lazy">'


def page(title, active, body, tiers, stamp, og_image="pc.png", path="/pc/", description=None):
    chips = [("/pc/", "Übersicht", "index")] + [
        (f"/pc/{t['id']}.html", f"{t['budget']}{'+' if t is tiers[-1] else ''} €", t["id"]) for t in tiers]
    chips.append(("/deals/", "Deals", "deals"))
    nav = "".join(f'<a href="{u}" class="chip{" on" if active == k else ""}">{n}</a>' for u, n, k in chips)
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{e(title)} – {e(config.SITE_TITLE)}</title>
<meta name="robots" content="index,follow">{head_icons()}<meta name="color-scheme" content="dark light">
<meta name="description" content="{e(description or title)}">{og.meta(f"{title} – Hinkowicz", description or title, og_image, path)}
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><style>{CSS}</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<div class="wrap">
<header class="top"><a class="brand" href="/">{logo_html() or '<span>Hinkowicz</span>'}<small>Bestpreis-Listen</small></a>
<nav class="navbar glass">{nav}</nav></header>
<div class="ad glass"><b>Anzeige</b> · {e(config.AD_NOTICE)}</div>
{body}
<footer>Stand: {e(stamp)} · Preise inkl. MwSt. zzgl. Versand, Preisangaben über Geizhals.de, Änderungen möglich.
Zusammenstellung &amp; Bewertung: eigener Hinko-Score. · <a href="/">hinkowicz.de</a>{legal_links()}</footer>
</div></body></html>"""


def pc_page(b, prev, tiers, stamp):
    rows = "".join(f"""<div class="row">{img(p['image'])}<div><div class="slot">{e(p['slot'])}</div>
<div class="pname">{e(p['name'])}</div><div class="muted">{e(' · '.join(x for x in (p['note'], 'bei ' + p['merchant'] if p.get('merchant') else '') if x))}</div></div>
<div class="right"><div><b>{eur(p['price']) if p['price'] else 'inklusive'}</b></div>{f'<a class="btn" href="{e(p["url"])}" target="_blank" rel="sponsored noopener">Zum Angebot*</a>' if p.get('url') else ''}</div></div>"""
                   for p in b["parts"])
    delta = ""
    if prev:
        diff = b["total"] - prev["total"]
        changed = [p["slot"] for p in b["parts"]
                   if p["id"] not in {q["id"] for q in prev["parts"]}]
        cls = "up" if diff > 0 else "down"
        delta = f'<div class="tip glass">📈 <b>Vorwoche:</b> Gesamtpreis <span class="{cls}">{"+" if diff > 0 else ""}{eur(diff)}</span>'
        delta += f' · neu gewählt: {e(", ".join(changed))}' if changed else " · gleiche Teile"
        delta += "</div>"
    tip = ""
    if b.get("upgrade"):
        u = b["upgrade"]
        tip = f'<div class="tip glass">💡 <b>Hinko-Tipp:</b> Mit <b>+{u["extra"]} €</b> ({e(u["text"])}) gibt es rund <b>+{u["gain"]} %</b> mehr Gaming-Leistung.</div>'
    body = f"""<h1>Gaming-PC bis {b['budget']}{"+" if b['tier'] == tiers[-1]['id'] else ""} € – {e(b['name'])}</h1>
<p class="sub">Wöchentlich neu berechnet aus aktuellen Geizhals-Bestpreisen. Plattform {e(b['platform'])} ·
Hinko-Score <span class="score">{b['score']}</span></p>
<div class="parts glass">{rows}<div class="total"><span>Gesamt</span><span>{eur(b['total'])}</span></div></div>
{tip}{delta}{SCORE_EXPLAIN}
<p class="muted">Hinweis: Windows-Lizenz, Peripherie und Versand sind nicht enthalten. Die Teile sind auf
Kompatibilität (Sockel, RAM-Typ, Netzteil-Leistung) abgestimmt – bitte vor dem Kauf trotzdem kurz prüfen.</p>"""
    return page(f"Gaming-PC bis {b['budget']} €", b["tier"], body, tiers, stamp, f"pc-{b['tier']}.png", f"/pc/{b['tier']}.html",
                f"Diese Woche für {eur(b['total'])}: {b['parts'][0]['note']} + {b['parts'][1]['note']}. Wöchentlich neu berechnet aus Geizhals-Bestpreisen.")


def deals_page(deals, tiers, stamp):
    cards = "".join(f"""<a class="card deal glass press" href="{e(d['url'])}" target="_blank" rel="sponsored noopener">{img(d['image'])}
<div class="muted">{e(d['category'])}</div><div class="pname">{e(d['name'])}</div>
<div><span class="price">{eur(d['price'])}</span>{f'<span class="old" title="Geizhals-Bestpreis vor der Preissenkung">vorher {eur(d["old_price"])}</span>' if d.get('old_price') else ''}</div>
<div><span class="pct">{e(d['percent'])} %</span> {'<span class="badge">Allzeit-Bestpreis</span>' if d['alltime_best'] else ''}
<span class="muted">· {e(d.get('merchant') or '')}</span></div><span class="btn">Zum Deal*</span></a>""" for d in deals)
    body = f"""<h1>Die besten Technik-Deals des Tages</h1>
<p class="sub">Jeden Tag neu: die größten Bestpreis-Senkungen der letzten 7 Tage auf Geizhals – nach eigenem Deal-Score sortiert
(Ersparnis, Preisniveau, Beliebtheit, Allzeit-Tiefstpreise). Nur lieferbare Produkte.
„vorher“ ist der bisherige Geizhals-Bestpreis – keine UVP, also echte Ersparnis.</p>
<div class="grid">{cards}</div>"""
    return page("Technik-Deals des Tages", "deals", body, tiers, stamp, "deals.png", "/deals/",
                "Jeden Tag neu: die größten Bestpreis-Senkungen auf Geizhals – nach eigenem Deal-Score sortiert.")


def index_page(builds, deals, tiers, stamp):
    cards = "".join(f"""<a class="card glass press" href="/pc/{b['tier']}.html"><div class="muted">bis {b['budget']}{"+" if b['tier'] == tiers[-1]['id'] else ""} € · {e(b['name'])}</div>
<div class="price">{eur(b['total'])}</div><div>{e(b['parts'][1]['note'])}</div><div class="muted">{e(b['parts'][0]['note'])}</div>
<div style="margin-top:6px"><span class="score">Score {b['score']}</span></div></a>""" for b in builds)
    top = "".join(f'<li><a class="glass press" href="{e(d["url"])}" target="_blank" rel="sponsored noopener"><span>{e(d["name"])}*</span><span><b>{eur(d["price"])}</b> <span class="pct">{e(d["percent"])} %</span></span></a></li>'
                  for d in deals[:5])
    body = f"""<h1>Gaming-PC Bestpreis-Listen</h1>
<p class="sub">Jede Woche neu berechnet – die beste Gaming-Leistung pro Euro für dein Budget.</p>
<div class="grid">{cards}</div>{SCORE_EXPLAIN}
<h2>Top-Deals des Tages</h2><ul class="toplist">{top}</ul><p><a class="btn" href="/deals/">Alle Deals ansehen</a></p>"""
    return page("Gaming-PC Bestpreis-Listen", "index", body, tiers, stamp, "pc.png", "/pc/",
                "Die beste Gaming-Leistung pro Euro für 800, 1.000, 1.500 und 2.000+ € – jede Woche neu berechnet.")


def write_site(out_dir, builds, deals, history, stamp):
    out = Path(out_dir)
    pc, dl, api = out / "pc", out / "deals", out / "api"
    for d in (pc, dl, api):
        d.mkdir(parents=True, exist_ok=True)
    tiers = config.TIERS
    prev = {b["tier"]: b for b in (history or {}).get("builds", [])}
    for b in builds:
        (pc / f"{b['tier']}.html").write_text(pc_page(b, prev.get(b["tier"]), tiers, stamp), encoding="utf-8")
        (api / f"pc-{b['tier']}.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    built = {b["tier"] for b in builds}
    for t in tiers:
        if t["id"] not in built:
            body = (f"<h1>Gaming-PC bis {t['budget']} €</h1><p class='sub'>Diese Woche gibt es zu den aktuellen "
                    "Bestpreisen keine Zusammenstellung, die unseren Qualitätsansprüchen in diesem Budget genügt. "
                    "Schau dir solange die nächsthöhere Stufe an – nächste Woche wird neu gerechnet.</p>")
            (pc / f"{t['id']}.html").write_text(page(f"Gaming-PC bis {t['budget']} €", t["id"], body, tiers, stamp),
                                                encoding="utf-8")
    (dl / "index.html").write_text(deals_page(deals, tiers, stamp), encoding="utf-8")
    (pc / "index.html").write_text(index_page(builds, deals, tiers, stamp), encoding="utf-8")
    if ASSETS.exists():
        import shutil
        shutil.copytree(ASSETS, out / "assets", dirs_exist_ok=True)
    (api / "deals.json").write_text(json.dumps(deals, ensure_ascii=False, indent=1), encoding="utf-8")
    (api / "all.json").write_text(json.dumps({"updated": stamp, "builds": builds, "deals": deals},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
