"""Impressum und Datenschutz aus content/*.md (einfaches Markdown: #-Überschriften, Absätze, Listen, **fett**, Links)."""
import re
from pathlib import Path

from .render import e, head_icons, logo_html
from .theme import BASE

CSS = r"""
.legal{max-width:760px;margin:0 auto;padding:calc(16px + env(safe-area-inset-top)) 16px 0}
.legal .top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:16px}
.legal .back{display:inline-flex;align-items:center;gap:6px}
.legal article{padding:22px 20px;border-radius:26px}
.legal h1{font-size:clamp(28px,7vw,40px);margin:0 0 14px}
.legal h2{font-size:20px;margin:26px 0 8px}
.legal h3{font-size:16px;margin:18px 0 6px}
.legal p,.legal li{color:var(--muted);line-height:1.65;overflow-wrap:anywhere}
.legal p strong,.legal li strong{color:var(--text)}
.legal a{color:var(--accent)}
.legal ul{padding-left:20px}
.legal .addr{color:var(--text);white-space:pre-line}
@media (min-width:760px){.legal article{padding:36px 40px}}
"""

LINK = re.compile(r"(https?://[^\s<>()]+[^\s<>().,;:])|([\w.+-]+@[\w-]+\.[\w.-]+\w)")


def _inline(text):
    out, pos = [], 0
    for m in LINK.finditer(text):
        out.append(_bold(e(text[pos:m.start()])))
        url, mail = m.group(1), m.group(2)
        href = url if url else f"mailto:{mail}"
        out.append(f'<a href="{e(href)}" rel="noopener">{e(url or mail)}</a>')
        pos = m.end()
    out.append(_bold(e(text[pos:])))
    return "".join(out)


def _bold(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def to_html(md):
    html, para, items = [], [], []

    def flush():
        if para:
            lines = [_inline(l.strip()) for l in para]
            # kurze Zeilen untereinander (Adressen) behalten ihre Zeilenumbrüche
            cls = ' class="addr"' if len(para) > 1 and all(len(l.strip()) < 70 for l in para) else ""
            html.append(f"<p{cls}>" + ("<br>" if cls else " ").join(lines) + "</p>")
            para.clear()
        if items:
            html.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    first = True
    for line in md.splitlines():
        m = re.match(r"^(#{2,4})\s*(.+)$", line.strip())
        if m:
            flush()
            level = 1 if first else min(len(m.group(1)) - 1, 3)
            html.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            first = False
        elif line.strip().startswith("- "):
            if para:
                flush()
            items.append(line.strip()[2:])
        elif not line.strip():
            flush()
        else:
            if items:
                flush()
            para.append(line)
    flush()
    return "\n".join(html)


def page(title, md):
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)} – Hinkowicz</title>{head_icons()}<meta name="color-scheme" content="dark light">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<style>{BASE}{CSS}</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<main class="legal">
<div class="top"><a href="/" aria-label="Startseite">{logo_html() or 'Hinkowicz'}</a>
<a class="chip glass press back" href="/">← Zurück</a></div>
<article class="glass">{to_html(md)}</article>
<footer><a href="/impressum/">Impressum</a> · <a href="/datenschutz/">Datenschutz</a></footer>
</main></body></html>"""


PAGES = (("impressum", "impressum", "Impressum"), ("datenschutz", "datenschutz", "Datenschutz"),
         # Discord-Bot (Links im Discord Developer Portal)
         ("discord-nutzungsbedingungen", "discord/nutzungsbedingungen", "Nutzungsbedingungen Hinko-Bot"),
         ("discord-datenschutz", "discord/datenschutz", "Datenschutz Hinko-Bot"))


def write(out_dir):
    for src_name, path, title in PAGES:
        src = Path("content") / f"{src_name}.md"
        if src.exists():
            d = Path(out_dir) / path
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(page(title, src.read_text(encoding="utf-8")), encoding="utf-8")
