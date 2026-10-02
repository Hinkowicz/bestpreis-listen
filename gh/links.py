"""Link-Seite im Link-in-Bio-Stil aus content/links.yml (bearbeitbar über /admin/)."""
import re
from pathlib import Path

import yaml

from . import config
from .render import CSS, e, head_icons, legal_links, logo_html

URL_RE = re.compile(r"^https://[^\s<>\"']+$")
IMG_RE = re.compile(r"^/?assets/(links/)?[A-Za-z0-9._-]+\.(png|jpe?g|webp|gif)$")

LINK_CSS = """
.bio{max-width:600px;margin:0 auto}.bio header{justify-content:center}.bio .brand{align-items:center}
.links{display:grid;gap:12px;margin-top:8px}
.lnk{display:grid;grid-template-columns:64px 1fr;gap:14px;align-items:center;background:var(--card);
border:1px solid var(--line);border-radius:16px;padding:12px;text-decoration:none;transition:border-color .15s,transform .15s}
.lnk:hover{border-color:var(--accent2);transform:translateY(-1px)}
.lnk img,.lnk .ph{width:64px;height:64px;border-radius:12px;object-fit:cover;background:var(--chip)}
.lnk .ph{display:grid;place-items:center;font-size:26px}
.lnk .t{font-weight:800;font-size:16px}.lnk .d{color:var(--muted);font-size:13px;margin-top:2px}
.tag{display:inline-block;font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
color:var(--accent2);margin-left:6px;vertical-align:middle}
"""


def load(path="content/links.yml"):
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    out = []
    for it in (data or {}).get("links") or []:
        if not isinstance(it, dict) or it.get("visible") is False:
            continue
        url, title = str(it.get("url") or "").strip(), str(it.get("title") or "").strip()
        if not title or not URL_RE.match(url):  # nur vollständige https-Links
            continue
        img = str(it.get("image") or "").strip()
        out.append({"title": title, "description": str(it.get("description") or "").strip(), "url": url,
                    "image": img.lstrip("/") if IMG_RE.match(img) else None, "ad": it.get("ad", True) is not False})
    return out


def page(links, stamp):
    items = "".join(
        f'<a class="lnk" href="{e(l["url"])}" target="_blank" rel="{"sponsored " if l["ad"] else ""}noopener">'
        + (f'<img src="{e(l["image"])}" alt="" loading="lazy">' if l["image"] else '<span class="ph">🔗</span>')
        + f'<span><span class="t">{e(l["title"])}{"*" if l["ad"] else ""}</span>'
        + (f'<span class="tag">Anzeige</span>' if l["ad"] else "")
        + (f'<div class="d">{e(l["description"])}</div>' if l["description"] else "")
        + "</span></a>"
        for l in links)
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Hinkowicz – Links</title>{head_icons()}
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<style>{CSS}{LINK_CSS}</style></head><body><div class="wrap bio">
<header><a class="brand" href="links.html">{logo_html() or '<span>Hinkowicz</span>'}</a></header>
<div class="ad"><b>Anzeige</b> · {e(config.AD_NOTICE)} Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.</div>
<div class="links">{items}</div>
<footer>Stand: {e(stamp)}{legal_links()}</footer></div></body></html>"""


def write(out_dir, stamp, path="content/links.yml"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "links.html").write_text(page(load(path), stamp), encoding="utf-8")
