"""Erzeugt die statischen Seiten (index, pc-<budget>, deals) + JSON für den Discord-Bot."""
import html
import json
from pathlib import Path

from . import config

CSS = """
:root{--bg:#0f1115;--card:#181b22;--line:#262a33;--text:#e8eaf0;--muted:#9aa1ae;
--accent:#22d3ee;--accent2:#e440d0;--on-accent:#04222a;--veil:rgba(15,17,21,.86);--good:#3ecf8e;--bad:#ff5d7a;--chip:#232733}
@media (prefers-color-scheme: light){:root{--bg:#f6f7f9;--card:#fff;--line:#e3e6ec;--text:#14161b;
--muted:#5d6472;--chip:#f0f2f5;--veil:rgba(246,247,249,.94);--accent:#0e7490;--accent2:#b0179c;--on-accent:#fff;--good:#0f7a4e;--bad:#c0264a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:inherit}.wrap{max-width:980px;margin:0 auto;padding:16px}
nav,header,.wrap{min-width:0}.pname{overflow-wrap:anywhere}
header{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between;margin-bottom:12px}
.brand{font-weight:800;font-size:19px;text-decoration:none;letter-spacing:.02em}
.brand small{display:block;font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
nav{display:flex;flex-wrap:wrap;gap:6px}nav a{padding:6px 10px;border-radius:999px;background:var(--chip);
text-decoration:none;font-size:13px;font-weight:600}nav a.on{background:var(--accent);color:var(--on-accent)}
.ad{font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:8px 0 18px}
.ad b{color:var(--accent2)}h1{font-size:26px;margin:4px 0}h2{font-size:18px;margin:24px 0 8px}
.sub{color:var(--muted);margin:0 0 16px}.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;text-decoration:none;display:block}
.card:hover{border-color:var(--accent2)}.price{font-size:24px;font-weight:800}.muted{color:var(--muted);font-size:13px}
.score{display:inline-block;background:linear-gradient(90deg,var(--accent),var(--accent2));color:#fff;font-weight:800;text-shadow:0 1px 1px #0004;
border-radius:8px;padding:2px 8px;font-size:13px}
.parts{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.row{display:grid;grid-template-columns:56px 1fr auto;gap:12px;align-items:center;padding:10px 14px;border-top:1px solid var(--line)}
.row:first-child{border-top:0}.row img,.noimg{width:56px;height:56px;object-fit:contain;background:#fff;border-radius:8px}.noimg{background:var(--chip)}
.deal .noimg{width:100%;height:120px;margin-bottom:8px}
.slot{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}.pname{font-weight:600}
.right{text-align:right;white-space:nowrap}.btn{display:inline-block;margin-top:4px;padding:5px 10px;border-radius:8px;
background:var(--accent);color:var(--on-accent);text-decoration:none;font-weight:700;font-size:13px}
.btn:hover{background:var(--accent2);color:#fff}
details.explain{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin-top:12px}
details.explain summary{cursor:pointer;font-weight:700;color:var(--accent)}details.explain p{margin:8px 0 0}
.total{display:flex;justify-content:space-between;align-items:center;padding:14px;font-size:18px;font-weight:800;
border-top:2px solid var(--accent)}.tip{background:var(--card);border-left:4px solid var(--accent2);border-radius:10px;
padding:10px 14px;margin-top:12px}.up{color:var(--bad)}.down{color:var(--good)}
.deal .old{color:var(--muted);font-size:13px;margin-left:6px}
.pct{color:var(--accent2);font-weight:800}.badge{font-size:11px;background:linear-gradient(90deg,var(--accent),var(--accent2));
color:#fff;text-shadow:0 1px 1px #0005;border-radius:6px;padding:1px 6px;font-weight:800}
.brand{display:flex;flex-direction:column;align-items:flex-start;gap:4px}.brand .wordmark{height:44px;width:auto;display:block}
@media (max-width:560px){.brand .wordmark{height:36px}}
body{background-color:var(--bg);background-image:linear-gradient(var(--veil),var(--veil)),url(assets/pattern.webp);
background-size:auto,520px auto;background-attachment:scroll}
.hero{display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center;background:var(--card);border:1px solid var(--line);
border-radius:16px;padding:16px;margin-bottom:16px;position:relative;overflow:hidden}
.hero.has-setup{grid-template-columns:auto 1fr;background:linear-gradient(90deg,var(--card) 45%,color-mix(in srgb,var(--card) 55%,transparent)),var(--hero) center/cover}
.hero .avatar{width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid var(--accent2)}
.hero .avatar.mono{object-fit:contain;padding:16px;background:#17181c}
.hero h1{margin:0}.socials{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.socials a{padding:4px 10px;border-radius:999px;border:1px solid var(--accent);text-decoration:none;font-size:13px;font-weight:600}
.socials a:hover{background:var(--accent);color:var(--on-accent)}
@media (max-width:560px){.hero{grid-template-columns:1fr}.hero.has-setup{background:var(--card)}}
.deal img{width:100%;height:120px;object-fit:contain;background:#fff;border-radius:10px;margin-bottom:8px}
footer{margin:32px 0 8px;color:var(--muted);font-size:12px}
@media (max-width:560px){.row{grid-template-columns:44px 1fr}.row img,.row .noimg{width:44px;height:44px}.right{grid-column:2;text-align:left}}
"""


SCORE_EXPLAIN = """<details class="explain"><summary>Was bedeutet der Hinko-Score?</summary>
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
            return f"assets/{f.name}"
    return None


def logo_html():
    if asset("logo-dark") and asset("logo-light"):
        return ('<picture><source srcset="assets/logo-light.png" media="(prefers-color-scheme: light)">'
                '<img class="wordmark" src="assets/logo-dark.png" alt="Hinkowicz" width="321" height="48"></picture>')
    return ""


def head_icons():
    if not asset("favicon-32"):
        return ""
    return ('<link rel="icon" href="assets/favicon.ico" sizes="any">'
            '<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">'
            '<link rel="apple-touch-icon" href="assets/apple-touch-icon.png"><meta name="theme-color" content="#17181c">')


def hero_html():
    avatar, setup = asset("avatar"), asset("setup")
    mono = asset("monogram") if not avatar else None
    socials = "".join(f'<a href="{e(url)}" target="_blank" rel="noopener">{e(name)}</a>'
                      for name, url in config.SOCIALS.items() if url)
    style = f' style="--hero:url({setup})"' if setup else ""
    return f"""<section class="hero{' has-setup' if setup else ''}"{style}>
{f'<img class="avatar" src="{avatar}" alt="Hinkowicz">' if avatar else ''}{f'<img class="avatar mono" src="{mono}" alt="">' if mono else ''}
<div><h1>Gaming-PC Bestpreis-Listen</h1><p class="sub" style="margin:4px 0 0">{e(config.INTRO)}</p>
{f'<div class="socials">{socials}</div>' if socials else ''}</div></section>"""


def e(s):
    return html.escape(str(s if s is not None else ""))


def eur(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def img(url):
    if not url:
        return '<div class="noimg"></div>'
    url = "https:" + url if url.startswith("//") else url
    if not url.startswith("https://"):  # nur echte Bild-URLs, keine javascript:/data:-Tricks
        return '<div class="noimg"></div>'
    return f'<img src="{e(url)}" alt="" loading="lazy" referrerpolicy="no-referrer">'


def page(title, active, body, tiers, stamp):
    nav = "".join(
        f'<a href="pc-{t["id"]}.html" class="{"on" if active == t["id"] else ""}">{t["budget"]}{"+" if t is tiers[-1] else ""} €</a>'
        for t in tiers)
    nav += f'<a href="deals.html" class="{"on" if active == "deals" else ""}">🔥 Deals</a>'
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} – {e(config.SITE_TITLE)}</title>
<meta name="robots" content="index,follow">{head_icons()}
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' https: data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><style>{CSS}</style></head><body><div class="wrap">
<header><a class="brand" href="index.html">{logo_html() or '<span>Hinkowicz</span>'}<small>Bestpreis-Listen</small></a><nav>{nav}</nav></header>
<div class="ad"><b>Anzeige</b> · {e(config.AD_NOTICE)}</div>
{body}
<footer>Stand: {e(stamp)} · Preise inkl. MwSt. zzgl. Versand, Preisangaben über Geizhals.de, Änderungen möglich.
Zusammenstellung &amp; Bewertung: eigener Hinko-Score. · <a href="{e(config.SITE_URL)}">hinkowicz.com</a></footer>
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
        tip = f'<div class="tip">💡 <b>Hinko-Tipp:</b> Mit <b>+{u["extra"]} €</b> ({e(u["text"])}) gibt es rund <b>+{u["gain"]} %</b> mehr Gaming-Leistung.</div>'
    body = f"""<h1>Gaming-PC bis {b['budget']}{"+" if b['tier'] == tiers[-1]['id'] else ""} € – {e(b['name'])}</h1>
<p class="sub">Wöchentlich neu berechnet aus aktuellen Geizhals-Bestpreisen. Plattform {e(b['platform'])} ·
Hinko-Score <span class="score">{b['score']}</span></p>
<div class="parts">{rows}<div class="total"><span>Gesamt</span><span>{eur(b['total'])}</span></div></div>
{tip}{delta}{SCORE_EXPLAIN}
<p class="muted">Hinweis: Windows-Lizenz, Peripherie und Versand sind nicht enthalten. Die Teile sind auf
Kompatibilität (Sockel, RAM-Typ, Netzteil-Leistung) abgestimmt – bitte vor dem Kauf trotzdem kurz prüfen.</p>"""
    return page(f"Gaming-PC bis {b['budget']} €", b["tier"], body, tiers, stamp)


def deals_page(deals, tiers, stamp):
    cards = "".join(f"""<a class="card deal" href="{e(d['url'])}" target="_blank" rel="sponsored noopener">{img(d['image'])}
<div class="muted">{e(d['category'])}</div><div class="pname">{e(d['name'])}</div>
<div><span class="price">{eur(d['price'])}</span>{f'<span class="old" title="Geizhals-Bestpreis vor der Preissenkung">vorher {eur(d["old_price"])}</span>' if d.get('old_price') else ''}</div>
<div><span class="pct">{e(d['percent'])} %</span> {'<span class="badge">Allzeit-Bestpreis</span>' if d['alltime_best'] else ''}
<span class="muted">· {e(d.get('merchant') or '')}</span></div><span class="btn">Zum Deal*</span></a>""" for d in deals)
    body = f"""<h1>🔥 Die besten Technik-Deals der Woche</h1>
<p class="sub">Größte Bestpreis-Senkungen der letzten 31 Tage auf Geizhals – nach eigenem Deal-Score sortiert
(Ersparnis, Preisniveau, Beliebtheit, Allzeit-Tiefstpreise). Nur lieferbare Produkte.
„vorher“ ist der bisherige Geizhals-Bestpreis – keine UVP, also echte Ersparnis.</p>
<div class="grid">{cards}</div>"""
    return page("Technik-Deals der Woche", "deals", body, tiers, stamp)


def index_page(builds, deals, tiers, stamp):
    cards = "".join(f"""<a class="card" href="pc-{b['tier']}.html"><div class="muted">bis {b['budget']}{"+" if b['tier'] == tiers[-1]['id'] else ""} € · {e(b['name'])}</div>
<div class="price">{eur(b['total'])}</div><div>{e(b['parts'][1]['note'])}</div><div class="muted">{e(b['parts'][0]['note'])}</div>
<div style="margin-top:6px"><span class="score">Score {b['score']}</span></div></a>""" for b in builds)
    top = "".join(f'<li><a href="{e(d["url"])}" target="_blank" rel="sponsored noopener">{e(d["name"])}</a>* – <b>{eur(d["price"])}</b> <span class="pct">{e(d["percent"])} %</span></li>'
                  for d in deals[:5])
    body = f"""{hero_html()}
<div class="grid">{cards}</div>{SCORE_EXPLAIN}
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
    built = {b["tier"] for b in builds}
    for t in tiers:
        if t["id"] not in built:
            body = (f"<h1>Gaming-PC bis {t['budget']} €</h1><p class='sub'>Diese Woche gibt es zu den aktuellen "
                    "Bestpreisen keine Zusammenstellung, die unseren Qualitätsansprüchen in diesem Budget genügt. "
                    "Schau dir solange die nächsthöhere Stufe an – nächste Woche wird neu gerechnet.</p>")
            (out / f"pc-{t['id']}.html").write_text(page(f"Gaming-PC bis {t['budget']} €", t["id"], body, tiers, stamp),
                                                     encoding="utf-8")
    (out / "deals.html").write_text(deals_page(deals, tiers, stamp), encoding="utf-8")
    if ASSETS.exists():
        import shutil
        shutil.copytree(ASSETS, out / "assets", dirs_exist_ok=True)
    (out / "index.html").write_text(index_page(builds, deals, tiers, stamp), encoding="utf-8")
    (out / "api" / "deals.json").write_text(json.dumps(deals, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "api" / "all.json").write_text(json.dumps({"updated": stamp, "builds": builds, "deals": deals},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
