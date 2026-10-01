"""Erzeugt die statischen Seiten (index, pc-<budget>, deals) + JSON für den Discord-Bot."""
import html
import json
from pathlib import Path

from . import config

CSS = """
:root{--bg:#0f1115;--card:#181b22;--line:#262a33;--text:#e8eaf0;--muted:#9aa1ae;
--accent:#ff6a3d;--accent2:#ffb347;--good:#3ecf8e;--bad:#ff5d5d;--chip:#232733}
@media (prefers-color-scheme: light){:root{--bg:#f6f7f9;--card:#fff;--line:#e3e6ec;--text:#14161b;
--muted:#5d6472;--chip:#f0f2f5}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:inherit}.wrap{max-width:980px;margin:0 auto;padding:16px}
nav,header,.wrap{min-width:0}.pname{overflow-wrap:anywhere}
header{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between;margin-bottom:12px}
.brand{font-weight:800;font-size:20px;text-decoration:none}.brand span{color:var(--accent)}
nav{display:flex;flex-wrap:wrap;gap:6px}nav a{padding:6px 10px;border-radius:999px;background:var(--chip);
text-decoration:none;font-size:13px;font-weight:600}nav a.on{background:var(--accent);color:#fff}
.ad{font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:8px 0 18px}
.ad b{color:var(--accent2)}h1{font-size:26px;margin:4px 0}h2{font-size:18px;margin:24px 0 8px}
.sub{color:var(--muted);margin:0 0 16px}.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;text-decoration:none;display:block}
.card:hover{border-color:var(--accent)}.price{font-size:24px;font-weight:800}.muted{color:var(--muted);font-size:13px}
.score{display:inline-block;background:linear-gradient(90deg,var(--accent),var(--accent2));color:#fff;font-weight:800;
border-radius:8px;padding:2px 8px;font-size:13px}
.parts{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.row{display:grid;grid-template-columns:56px 1fr auto;gap:12px;align-items:center;padding:10px 14px;border-top:1px solid var(--line)}
.row:first-child{border-top:0}.row img,.noimg{width:56px;height:56px;object-fit:contain;background:#fff;border-radius:8px}.noimg{background:var(--chip)}
.deal .noimg{width:100%;height:120px;margin-bottom:8px}
.slot{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}.pname{font-weight:600}
.right{text-align:right;white-space:nowrap}.btn{display:inline-block;margin-top:4px;padding:5px 10px;border-radius:8px;
background:var(--accent);color:#fff;text-decoration:none;font-weight:700;font-size:13px}
.total{display:flex;justify-content:space-between;align-items:center;padding:14px;font-size:18px;font-weight:800;
border-top:2px solid var(--accent)}.tip{background:var(--card);border-left:4px solid var(--accent2);border-radius:10px;
padding:10px 14px;margin-top:12px}.up{color:var(--bad)}.down{color:var(--good)}
.deal .old{text-decoration:line-through;color:var(--muted);font-size:13px;margin-left:6px}
.pct{color:var(--good);font-weight:800}.badge{font-size:11px;background:var(--good);color:#06291a;border-radius:6px;padding:1px 6px;font-weight:800}
.deal img{width:100%;height:120px;object-fit:contain;background:#fff;border-radius:10px;margin-bottom:8px}
footer{margin:32px 0 8px;color:var(--muted);font-size:12px}
@media (max-width:560px){.row{grid-template-columns:44px 1fr}.row img,.row .noimg{width:44px;height:44px}.right{grid-column:2;text-align:left}}
"""


def e(s):
    return html.escape(str(s if s is not None else ""))


def eur(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def img(url):
    if not url:
        return '<div class="noimg"></div>'
    url = "https:" + url if url.startswith("//") else url
    return f'<img src="{e(url)}" alt="" loading="lazy">'


def page(title, active, body, tiers, stamp):
    nav = "".join(
        f'<a href="pc-{t["id"]}.html" class="{"on" if active == t["id"] else ""}">{t["budget"]}{"+" if t is tiers[-1] else ""} €</a>'
        for t in tiers)
    nav += f'<a href="deals.html" class="{"on" if active == "deals" else ""}">🔥 Deals</a>'
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} – {e(config.SITE_TITLE)}</title>
<meta name="robots" content="index,follow"><style>{CSS}</style></head><body><div class="wrap">
<header><a class="brand" href="index.html">Hinko<span>wicz</span> Bestpreise</a><nav>{nav}</nav></header>
<div class="ad"><b>Anzeige</b> · {e(config.AD_NOTICE)}</div>
{body}
<footer>Stand: {e(stamp)} · Preise inkl. MwSt. zzgl. Versand, Preisangaben über Geizhals.de, Änderungen möglich.
Zusammenstellung &amp; Bewertung: eigener Hinkowicz-Score. · <a href="{e(config.SITE_URL)}">hinkowicz.com</a></footer>
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
        delta = f'<div class="tip">📈 <b>Vorwoche:</b> Gesamtpreis <span class="{cls}">{"+" if diff > 0 else ""}{eur(diff)}</span>'
        delta += f' · neu gewählt: {e(", ".join(changed))}' if changed else " · gleiche Teile"
        delta += "</div>"
    tip = ""
    if b.get("upgrade"):
        u = b["upgrade"]
        tip = f'<div class="tip">💡 <b>Hinkowicz-Tipp:</b> Mit <b>+{u["extra"]} €</b> ({e(u["text"])}) gibt es rund <b>+{u["gain"]} %</b> mehr Gaming-Leistung.</div>'
    body = f"""<h1>Gaming-PC bis {b['budget']}{"+" if b['tier'] == tiers[-1]['id'] else ""} € – {e(b['name'])}</h1>
<p class="sub">Wöchentlich neu berechnet aus aktuellen Geizhals-Bestpreisen. Plattform {e(b['platform'])} ·
Hinkowicz-Score <span class="score">{b['score']}</span> <span class="muted">(RTX 5070 + Ryzen 7 9800X3D = 100)</span></p>
<div class="parts">{rows}<div class="total"><span>Gesamt</span><span>{eur(b['total'])}</span></div></div>
{tip}{delta}
<p class="muted">Hinweis: Windows-Lizenz, Peripherie und Versand sind nicht enthalten. Die Teile sind auf
Kompatibilität (Sockel, RAM-Typ, Netzteil-Leistung) abgestimmt – bitte vor dem Kauf trotzdem kurz prüfen.</p>"""
    return page(f"Gaming-PC bis {b['budget']} €", b["tier"], body, tiers, stamp)


def deals_page(deals, tiers, stamp):
    cards = "".join(f"""<a class="card deal" href="{e(d['url'])}" target="_blank" rel="sponsored noopener">{img(d['image'])}
<div class="muted">{e(d['category'])}</div><div class="pname">{e(d['name'])}</div>
<div><span class="price">{eur(d['price'])}</span>{f'<span class="old">{eur(d["old_price"])}</span>' if d.get('old_price') else ''}</div>
<div><span class="pct">{e(d['percent'])} %</span> {'<span class="badge">Allzeit-Bestpreis</span>' if d['alltime_best'] else ''}
<span class="muted">· {e(d.get('merchant') or '')}</span></div><span class="btn">Zum Deal*</span></a>""" for d in deals)
    body = f"""<h1>🔥 Die besten Technik-Deals der Woche</h1>
<p class="sub">Größte Bestpreis-Senkungen der letzten 31 Tage auf Geizhals – nach eigenem Deal-Score sortiert
(Ersparnis, Preisniveau, Beliebtheit, Allzeit-Tiefstpreise). Nur lieferbare Produkte.</p>
<div class="grid">{cards}</div>"""
    return page("Technik-Deals der Woche", "deals", body, tiers, stamp)


def index_page(builds, deals, tiers, stamp):
    cards = "".join(f"""<a class="card" href="pc-{b['tier']}.html"><div class="muted">bis {b['budget']}{"+" if b['tier'] == tiers[-1]['id'] else ""} € · {e(b['name'])}</div>
<div class="price">{eur(b['total'])}</div><div>{e(b['parts'][1]['note'])}</div><div class="muted">{e(b['parts'][0]['note'])}</div>
<div style="margin-top:6px"><span class="score">Score {b['score']}</span></div></a>""" for b in builds)
    top = "".join(f'<li><a href="{e(d["url"])}" target="_blank" rel="sponsored noopener">{e(d["name"])}</a>* – <b>{eur(d["price"])}</b> <span class="pct">{e(d["percent"])} %</span></li>'
                  for d in deals[:5])
    body = f"""<h1>Gaming-PC Bestpreis-Listen</h1>
<p class="sub">Jede Woche automatisch neu zusammengestellt – optimiert auf maximale Gaming-Leistung pro Euro.</p>
<div class="grid">{cards}</div>
<h2>🔥 Top-Deals der Woche</h2><ul>{top}</ul><p><a class="btn" href="deals.html">Alle Deals ansehen</a></p>"""
    return page("Übersicht", "index", body, tiers, stamp)


def write_site(out_dir, builds, deals, history, stamp):
    out = Path(out_dir)
    (out / "api").mkdir(parents=True, exist_ok=True)
    tiers = config.TIERS
    prev = {b["tier"]: b for b in (history or {}).get("builds", [])}
    for b in builds:
        (out / f"pc-{b['tier']}.html").write_text(pc_page(b, prev.get(b["tier"]), tiers, stamp), encoding="utf-8")
        (out / "api" / f"pc-{b['tier']}.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "deals.html").write_text(deals_page(deals, tiers, stamp), encoding="utf-8")
    (out / "index.html").write_text(index_page(builds, deals, tiers, stamp), encoding="utf-8")
    (out / "api" / "deals.json").write_text(json.dumps(deals, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "api" / "all.json").write_text(json.dumps({"updated": stamp, "builds": builds, "deals": deals},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
