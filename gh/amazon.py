"""Amazon-Deals (Prime Day, Black Friday …) aus Geizhals-Daten.

Echte Rabatte statt UVP-Streichpreisen: Geizhals vergleicht mit dem eigenen Bestpreis-Verlauf.
Nur Produkte, bei denen Amazon gerade der günstigste Händler ist. Links laufen über /a/?i=<ASIN>,
die Seite öffnet möglichst die Amazon-App und hängt den Partner-Tag an (assets/amazon.js).
"""
import json
import re
from pathlib import Path

from . import config, deals, og
from .render import e, eur, img, page
from .theme import BASE

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
REDIRECT_CSS = BASE + """
.go{min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:24px 16px}
.go .box{max-width:440px;width:100%;text-align:center;padding:30px 22px;border-radius:30px}
.go h1{font-size:26px;margin:10px 0 6px;letter-spacing:-.02em}
.go p{color:var(--muted);margin:0 0 16px;line-height:1.5}
.go .btn{display:flex;width:100%;margin-top:10px;padding:15px 18px;font-size:16px}
.go .ghost{background:var(--chip);color:var(--text);box-shadow:none;border:1px solid var(--edge)}
.go .hint{margin-top:18px;font-size:14px}.go .hint[hidden]{display:none}
.go .small{font-size:12px;color:var(--faint);margin:14px 0 0}
.go .wordmark{height:34px;width:auto}
"""
CACHE_URL = "https://hinkowicz.de/amazon/asins.json"  # ASINs ändern sich nicht -> vom letzten Lauf übernehmen


def amazon_url(asin):
    return f"https://www.amazon.de/dp/{asin}?tag={config.AMAZON_TAG}"


def link(asin):
    return f"/a/?i={asin}"


def merchant_id(catalog, api):
    """Geizhals-Händler-ID von Amazon aus den Händler-Zählern einer Deal-Abfrage."""
    for m, title in catalog.top_categories():
        if m is None or not re.search(config.DEAL_TOPCATS, title, re.I):
            continue
        resp = api.bestprice_development(m=m, interval=config.AMAZON_SETTINGS["interval"], v=2, limit=1)
        for mer in resp.get("merchants") or []:
            name = str(mer.get("name") or mer.get("hname") or mer.get("title") or "")
            if re.search(config.AMAZON_MERCHANT, name.strip(), re.I) and mer.get("id") is not None:
                return int(mer["id"])
    return None


def _find_asin(obj):
    """ASIN irgendwo in der query_product-Antwort finden (Feldname je nach API-Version)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "asin" in k.lower():
                for c in (v if isinstance(v, list) else [v]):
                    c = c.get("asin") if isinstance(c, dict) else c
                    if isinstance(c, str) and ASIN_RE.match(c.strip()):
                        return c.strip()
            found = _find_asin(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_asin(v)
            if found:
                return found
    return None


def load_cache(offline=False):
    if offline:
        return {}
    try:
        import requests
        r = requests.get(CACHE_URL, timeout=10)
        data = r.json() if r.status_code == 200 else {}
        return {str(k): v for k, v in data.items() if isinstance(v, str) and ASIN_RE.match(v)}
    except Exception:
        return {}


def collect(catalog, api, offline=False, active=True):
    """-> (deals, asin_cache, info)"""
    if not active:
        return [], load_cache(offline), "keine Aktion aktiv – übersprungen"  # ASIN-Speicher fürs nächste Mal behalten
    h_id = merchant_id(catalog, api)
    if h_id is None:
        return [], {}, "Amazon nicht unter den Geizhals-Händlern gefunden"
    cache = load_cache(offline)
    out, looked_up = [], 0
    raw = deals.collect(catalog, api, config.AMAZON_SETTINGS, h_id=h_id)
    names = sorted({str(d.get("merchant")) for d in raw})[:8]
    for d in raw:
        if not re.search(config.AMAZON_MERCHANT, str(d.get("merchant") or ""), re.I):
            continue  # Sicherheitsnetz: nur echte Amazon-Bestpreise
        key = str(d["id"])
        if key not in cache and looked_up < 80:
            looked_up += 1
            asin = _find_asin(api.post("query_product", {"query": key, "type": "id", "params": {"add_asin": True}}))
            if asin:
                cache[key] = asin
        if cache.get(key):
            d["asin"] = cache[key]
            d["url"] = link(cache[key])
            out.append(d)
    return out, cache, f"Händler-ID {h_id}, {len(raw)} Roh-Deals {names}, {len(out)} Deals, {looked_up} ASIN-Abfragen"


def load_event(path="content/amazon.json", today=None):
    """Aktionszeitraum (z. B. Black Friday): nur dann wird die Amazon-Liste berechnet und alle 3 Stunden erneuert."""
    from datetime import date, datetime
    from zoneinfo import ZoneInfo
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    today = today or datetime.now(ZoneInfo("Europe/Berlin")).date()

    def day(k):
        try:
            return date.fromisoformat(str(data.get(k) or ""))
        except ValueError:
            return None
    start, end = day("from"), day("until")
    active = bool(start and end and start <= today <= end)
    return {"event": str(data.get("event") or "").strip()[:40], "active": active, "from": start, "until": end}


def amazon_page(items, tiers, stamp, event, active=True):
    cards = "".join(f"""<a class="card deal glass press" href="{e(d['url'])}" rel="sponsored noopener">{img(d['image'])}
<div class="muted">{e(d['category'])}</div><div class="pname">{e(d['name'])}</div>
<div><span class="price">{eur(d['price'])}</span>{f'<span class="old" title="Geizhals-Bestpreis vor der Preissenkung">vorher {eur(d["old_price"])}</span>' if d.get('old_price') else ''}</div>
<div><span class="pct">{e(d['percent'])} %</span> {'<span class="badge">Allzeit-Bestpreis</span>' if d['alltime_best'] else ''}</div>
<span class="btn">Bei Amazon ansehen*</span></a>""" for d in items)
    head = f"{event}: " if event else ""
    if not active:
        items = []
    body = f"""<h1>{e(head)}Die besten Amazon-Deals</h1>
<p class="sub">Alle 3 Stunden neu: echte Preissenkungen bei Amazon – verglichen mit dem Geizhals-Bestpreis der letzten 31 Tage,
nicht mit UVP-Streichpreisen. Nur Produkte, bei denen Amazon gerade der günstigste Händler ist. Tippen öffnet die Amazon-App.</p>
<p class="sub"><b>Preise laut Geizhals, Stand {e(stamp)}.</b> Der aktuelle Preis bei Amazon kann abweichen – maßgeblich ist der Preis auf Amazon.
Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.</p>
{f'<div class="grid">{cards}</div>' if items else ('<p class="sub">Gerade keine passenden Deals – schau in ein paar Stunden wieder vorbei.</p>' if active else '<p class="sub">Gerade läuft keine Aktion. Zum nächsten Prime Day und Black Friday gibt es hier wieder die besten Amazon-Deals.</p>')}"""
    title = f"{head}Amazon-Deals"
    html = page(title, "amazon", body, tiers, stamp, "amazon.png", "/amazon/",
                "Echte Amazon-Preissenkungen, alle 3 Stunden neu – verglichen mit dem Geizhals-Bestpreis, nicht mit der UVP.")
    return html.replace('<meta name="robots" content="index,follow">', '<meta name="robots" content="noindex,follow">')


def redirect_page():
    return """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Weiter zu Amazon – Hinkowicz</title>
<meta name="robots" content="noindex"><meta name="referrer" content="no-referrer"><meta name="color-scheme" content="dark light">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'self'; base-uri 'none'; form-action 'none'">
<style>""" + REDIRECT_CSS + """</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<main class="go"><div class="box glass">
<img class="wordmark" src="/assets/logo-dark.png" alt="Hinkowicz" width="196" height="48">
<div class="tag">Anzeige</div>
<h1 id="t">Amazon wird geöffnet …</h1>
<p id="s">Einen Moment – du wirst zur Amazon-App weitergeleitet.</p>
<a class="btn big" id="app" href="https://www.amazon.de/">In der Amazon-App öffnen</a>
<a class="btn ghost" id="web" href="https://www.amazon.de/">Im Browser öffnen</a>
<p class="hint" id="h">Öffnet sich nichts? Tippe oben rechts auf <b>•••</b> und wähle <b>„Im Browser öffnen“</b> – dann klappt es mit der App.</p>
<p class="small">Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Für dich ändert sich am Preis nichts.</p>
</div></main><script src="/assets/amazon.js"></script></body></html>"""


def write(out_dir, items, cache, tiers, stamp, active=True):
    out = Path(out_dir)
    (out / "amazon").mkdir(parents=True, exist_ok=True)
    (out / "a").mkdir(parents=True, exist_ok=True)
    ev = load_event()
    (out / "amazon" / "index.html").write_text(amazon_page(items, tiers, stamp, ev["event"], active), encoding="utf-8")
    (out / "amazon" / "asins.json").write_text(json.dumps(cache, indent=0), encoding="utf-8")
    (out / "a" / "index.html").write_text(redirect_page(), encoding="utf-8")
    top = [f"{d['percent']} %  {d['name'][:46]}" for d in items[:3]]
    og.card(out / "og" / "amazon.png", "Alle 3 Stunden neu", "Amazon-Deals", top or ["Echte Rabatte statt UVP"])
