"""Startseite (hinkowicz.de): Link-Liste im Liquid-Glass-Design aus content/links.json.

Die Inhalte werden über die Hinko-App (/app/) gepflegt.
"""
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import config, icons, og
from .render import e, head_icons, legal_links, logo_html
from .theme import BASE

URL_RE = re.compile(r"^https://[^\s<>\"']+$")
IMG_RE = re.compile(r"^/?assets/((links|setup)/)?[A-Za-z0-9._-]+\.(png|jpe?g|webp|gif)$")

CSS = r"""
.home{max-width:1120px;margin:0 auto;padding:calc(18px + env(safe-area-inset-top)) 16px 0;
  display:grid;gap:18px}
.profile{padding:22px 18px 18px;text-align:center;display:grid;justify-items:center;gap:12px}
.profile .tagline{margin:0;font-size:13px;font-weight:650;letter-spacing:.14em;text-transform:uppercase;
  background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
.socials{display:flex;flex-wrap:wrap;justify-content:center;gap:10px}
.soc{width:48px;height:48px;display:grid;place-items:center;border-radius:16px;text-decoration:none;color:var(--text)}
.soc svg{transition:transform .45s var(--spring)}
@media (hover:hover){.soc:hover svg{transform:scale(1.12)}}
.list{display:grid;gap:12px;align-content:start}
.lnk{display:grid;grid-template-columns:60px 1fr 22px;gap:14px;align-items:center;padding:12px 14px 12px 12px;
  text-decoration:none;border-radius:22px}
.lnk .thumb{width:60px;height:60px;border-radius:16px;object-fit:cover;background:var(--chip);display:block}
.lnk .ph{display:grid;place-items:center;background:linear-gradient(135deg,var(--accent),var(--accent2))}
.lnk .ph img{width:30px;height:30px}
.lnk .t{display:block;font-weight:750;font-size:16px;letter-spacing:-.01em;line-height:1.25}
.lnk .d{display:block;color:var(--muted);font-size:13.5px;margin-top:3px;line-height:1.35}
.lnk .arr{color:var(--faint);transition:transform .45s var(--spring),color .3s}
@media (hover:hover){.lnk:hover .arr{transform:translateX(3px);color:var(--text)}}
.lnk .tag,.feat .tag{display:block;font-size:9.5px;margin-bottom:2px;opacity:.9}
.feat{display:block;padding:0;overflow:hidden;border-radius:28px;text-decoration:none}
.feat .art{aspect-ratio:16/8;display:grid;place-items:center;position:relative;overflow:hidden;
  background:radial-gradient(120% 120% at 0% 0%,color-mix(in srgb,var(--accent) 70%,transparent),transparent 60%),
             radial-gradient(120% 120% at 100% 100%,color-mix(in srgb,var(--accent2) 70%,transparent),transparent 60%),#0b0d12}
.feat .art img.cover{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.feat .art img.mono{width:64px;height:64px;filter:drop-shadow(0 8px 24px rgba(0,0,0,.4))}
.feat .body{padding:14px 18px 16px;display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center}
.feat .t{font-size:19px;font-weight:800;letter-spacing:-.02em;display:block}
.feat .d{color:var(--muted);font-size:14px;display:block;margin-top:2px}
.feat .go{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;box-shadow:0 8px 20px -8px var(--accent2)}
.lnk,.feat{position:relative}
.hit{position:absolute;inset:0;z-index:1;border-radius:inherit}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.code{position:relative;z-index:2;display:inline-flex;align-items:center;gap:6px;margin-top:8px;padding:6px 11px;
  border-radius:999px;border:1px dashed color-mix(in srgb,var(--accent) 70%,transparent);background:color-mix(in srgb,var(--accent) 12%,transparent);
  color:var(--text);font:inherit;font-size:13px;cursor:pointer;transition:transform .35s var(--spring),background .2s}
.code b{letter-spacing:.06em}.code .lbl{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.code:active{transform:scale(.95)}.code.ok{border-style:solid;border-color:var(--good);background:color-mix(in srgb,var(--good) 18%,transparent)}
.adnote{font-size:12px;color:var(--faint);text-align:center;margin:2px 0 0}
.home footer{grid-column:1/-1;text-align:center}
.home footer p{margin:6px 0}
@media (min-width:960px){
  .home{grid-template-columns:340px 1fr;gap:28px;padding-top:48px}
  .profile{position:sticky;top:32px;align-self:start;padding:34px 26px 26px}
  .wordmark{height:52px}
  .list{grid-template-columns:1fr 1fr;gap:14px;grid-auto-flow:row dense}
  .feat{grid-column:1/-1}
  .feat .art{aspect-ratio:16/6}
  .home footer{text-align:left}
}
"""

ARROW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>'
COPY = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="3"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>'
ARROW_UP = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg>'


def today():
    return datetime.now(ZoneInfo("Europe/Berlin")).date()


def clean(it, extra=()):
    """Ein Eintrag aus links.json/setup.json -> sicherer, normalisierter Datensatz (oder None)."""
    if not isinstance(it, dict) or it.get("visible") is False:
        return None
    url, title = str(it.get("url") or "").strip(), str(it.get("title") or "").strip()
    if not title or not URL_RE.match(url):  # nur vollständige https-Links
        return None
    until = str(it.get("until") or "").strip()
    if until:
        try:
            if date.fromisoformat(until) < today():  # abgelaufen -> ausblenden
                return None
        except ValueError:
            pass
    img = str(it.get("image") or "").strip()
    code = re.sub(r"\s+", " ", str(it.get("code") or "").strip())[:40]
    fm = re.match(r"^(\d{1,3}) (\d{1,3})$", str(it.get("focus") or "").strip())
    focus = f"{min(int(fm[1]), 100)}% {min(int(fm[2]), 100)}%" if fm else ""
    out = {"title": title, "description": str(it.get("description") or "").strip(), "url": url,
           "image": "/" + img.lstrip("/") if IMG_RE.match(img) else None, "focus": focus, "code": code,
           "ad": it.get("ad", True) is not False, "featured": it.get("featured") is True}
    for k in extra:
        out[k] = str(it.get(k) or "").strip()
    return out


def load(path="content/links.json", key="links", extra=()):
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return [c for c in (clean(it, extra) for it in (data or {}).get(key) or []) if c]


def load_site(path="content/site.json"):
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    socials = [s for s in data.get("socials") or [] if s.get("name") in icons.PATHS and URL_RE.match(s.get("url") or "")]
    return {"tagline": data.get("tagline") or "", "contact": data.get("contact") or "", "socials": socials}


def _rel(l):
    return ("sponsored " if l["ad"] else "") + "noopener"


def _code(l):
    if not l["code"]:
        return ""
    return (f'<button class="code" type="button" data-code="{e(l["code"])}" aria-label="Rabattcode {e(l["code"])} kopieren">'
            f'<span class="lbl">Code</span> <b>{e(l["code"])}</b> {COPY}</button>')


def _pos(l):
    """Bildausschnitt aus der App (Fokuspunkt), nur Zahlen – siehe clean()."""
    return f' style="object-position:{l["focus"]}"' if l.get("focus") else ""


def card(l, i):
    """Karte als Block mit unsichtbarem Voll-Link; der Code-Button liegt darüber und bleibt eigenständig klickbar."""
    star = "*" if l["ad"] else ""
    tag = '<span class="tag">Anzeige</span>' if l["ad"] else ""
    desc = f'<span class="d">{e(l["description"])}</span>' if l["description"] else ""
    cover = (f'<a class="hit" href="{e(l["url"])}" target="_blank" rel="{_rel(l)}">'
             f'<span class="sr">{e(l["title"])}</span></a>')
    if l["featured"]:
        art = (f'<img class="cover" src="{e(l["image"])}"{_pos(l)} alt="" loading="lazy">' if l["image"]
               else '<img class="mono" src="/assets/monogram-white.png" alt="">')
        return (f'<div class="feat glass press rise" style="--i:{i}">{cover}'
                f'<div class="art">{art}</div><div class="body"><span>{tag}<span class="t">{e(l["title"])}{star}</span>{desc}'
                f'{_code(l)}</span><span class="go">{ARROW_UP}</span></div></div>')
    thumb = (f'<img class="thumb" src="{e(l["image"])}"{_pos(l)} alt="" loading="lazy">' if l["image"]
             else '<span class="thumb ph"><img src="/assets/monogram-white.png" alt=""></span>')
    return (f'<div class="lnk glass press rise" style="--i:{i}">{cover}'
            f'{thumb}<span>{tag}<span class="t">{e(l["title"])}{star}</span>{desc}{_code(l)}</span>'
            f'<span class="arr">{ARROW}</span></div>')


def head(title, description, og_image, path):
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(description)}">
{head_icons()}<meta name="color-scheme" content="dark light">{og.meta(title, description, og_image, path)}
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'self'; base-uri 'none'; form-action 'none'">"""


def page(links, site, stamp):
    socials = "".join(f'<a class="soc glass press" href="{e(s["url"])}" target="_blank" rel="noopener me" '
                      f'aria-label="{e(s["name"])}">{icons.svg(s["name"])}</a>' for s in site["socials"])
    cards = "".join(card(l, i + 1) for i, l in enumerate(links))
    contact = (f'<p>Geschäftliche Anfragen: <a href="mailto:{e(site["contact"])}">{e(site["contact"])}</a></p>'
               if site["contact"] else "")
    return f"""{head("Hinkowicz", "Links, Kooperationen, Rabattcodes, mein Setup, Gaming-PC Bestpreis-Listen und Technik-Deals von Hinkowicz.", "home.png", "/")}
<style>{BASE}{CSS}</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<main class="home">
<aside class="profile glass rise">
{logo_html() or '<h1>Hinkowicz</h1>'}
{f'<p class="tagline">{e(site["tagline"])}</p>' if site["tagline"] else ''}
<nav class="socials" aria-label="Social Media">{socials}</nav>
<p class="adnote">Mit * markierte Links sind Werbung (Affiliate-Links).</p>
</aside>
<section class="list" aria-label="Links">{cards}</section>
<footer>
<p>Anzeige: {e(config.AD_NOTICE)} Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.</p>
{contact}
<p>© Hinkowicz{legal_links()}</p>
</footer>
</main><script src="/assets/site.js" defer></script></body></html>"""


def write(out_dir, stamp, path="content/links.json", site_path="content/site.json"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page(load(path), load_site(site_path), stamp), encoding="utf-8")
    # Für die App: woran sie erkennt, dass eine Änderung live ist
    (out / "version.json").write_text(json.dumps({"rev": os.environ.get("GITHUB_SHA", "local"), "built": stamp}),
                                      encoding="utf-8")
