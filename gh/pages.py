"""Weitere Seiten im Liquid-Glass-Design: „Mein Setup“ (/setup/) und die 404-Seite."""
import re
from pathlib import Path

from . import links
from .render import e, legal_links, logo_html
from .theme import BASE

CSS = r"""
.sub-page{max-width:1120px;margin:0 auto;padding:calc(16px + env(safe-area-inset-top)) 16px 0}
.sub-page .top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px}
.sub-page h1{font-size:clamp(30px,8vw,46px);margin:6px 0 6px}
.cats{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:5px;border-radius:999px;margin:14px 0 6px;
  position:sticky;top:calc(8px + env(safe-area-inset-top));z-index:5}
.cats::-webkit-scrollbar{display:none}
.cats a{border:1px solid transparent}
.cat{scroll-margin-top:80px}
.cat h2{font-size:20px;margin:26px 4px 12px}
.grid2{display:grid;gap:12px}
@media (min-width:760px){.grid2{grid-template-columns:1fr 1fr}}
@media (min-width:1080px){.grid2{grid-template-columns:1fr 1fr 1fr}}
.nf{min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:24px 16px}
.nf .box{max-width:460px;width:100%;text-align:center;padding:34px 24px;border-radius:30px}
.nf .big{font-size:96px;font-weight:900;letter-spacing:-.05em;line-height:1;margin:16px 0 4px;
  background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
.nf p{color:var(--muted)}
.nf .btn{margin-top:10px}
"""


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")).strip("-")


def setup_page(items):
    cats = []
    for it in items:
        c = it.get("category") or "Sonstiges"
        if c not in cats:
            cats.append(c)
    chips = "".join(f'<a class="chip" href="#{_slug(c)}">{e(c)}</a>' for c in cats)
    sections, n = [], 0
    for c in cats:
        cards = []
        for it in (i for i in items if (i.get("category") or "Sonstiges") == c):
            n += 1
            cards.append(links.card({**it, "featured": False}, min(n, 12)))
        sections.append(f'<section class="cat" id="{_slug(c)}"><h2>{e(c)}</h2><div class="grid2">{"".join(cards)}</div></section>')
    return f"""{links.head("Mein Setup – Hinkowicz", "Alles, was auf meinem Tisch steht: Monitore, Peripherie, Kabelmanagement, Licht und mehr – mit Rabattcodes.", "setup.png", "/setup/")}
<style>{BASE}{links.CSS}{CSS}</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<main class="sub-page">
<div class="top"><a href="/" aria-label="Startseite">{logo_html() or 'Hinkowicz'}</a><a class="chip glass press" href="/">← Zurück</a></div>
<h1>Mein Setup</h1>
<p class="sub">Alles, was auf meinem Tisch steht. Mit * markierte Links sind Werbung (Affiliate-Links).</p>
<nav class="cats glass" aria-label="Kategorien">{chips}</nav>
{"".join(sections)}
<footer><p>Anzeige: Kaufst du über einen mit * markierten Link, erhalte ich eine kleine Provision – für dich ändert sich am Preis nichts.
Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.</p><p>© Hinkowicz{legal_links()}</p></footer>
</main><script src="/assets/site.js" defer></script></body></html>"""


def not_found_page():
    return f"""{links.head("Seite nicht gefunden – Hinkowicz", "Diese Seite gibt es nicht (mehr).", "home.png", "/")}
<meta name="robots" content="noindex">
<style>{BASE}{CSS}</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<main class="nf"><div class="box glass rise">
{logo_html() or 'Hinkowicz'}
<div class="big">404</div>
<p>Diese Seite gibt es nicht (mehr). Vielleicht ist eine Aktion abgelaufen oder der Link hat sich geändert.</p>
<a class="btn" href="/">Zur Startseite</a>
</div></main></body></html>"""


def write(out_dir, setup_path="content/setup.json"):
    out = Path(out_dir)
    items = links.load(setup_path, key="items", extra=("category",))
    (out / "setup").mkdir(parents=True, exist_ok=True)
    (out / "setup" / "index.html").write_text(setup_page(items), encoding="utf-8")
    (out / "404.html").write_text(not_found_page(), encoding="utf-8")
