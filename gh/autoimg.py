"""Automatische Vorschaubilder für Links ohne eigenes Bild.

Beim Bauen wird das Vorschaubild der verlinkten Seite (og:image / twitter:image) einmal geladen,
verkleinert und unter /auto/ selbst ausgeliefert – Besucher laden nichts von fremden Servern.
Bereits geladene Bilder werden von der Live-Seite übernommen (/auto/index.json), statt sie neu zu holen.
Amazon ist ausgenommen: dessen Partnerbedingungen erlauben Produktbilder nur über die eigene Schnittstelle.
"""
import hashlib
import html
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

SITE = "https://hinkowicz.de"
AUTO_RE = re.compile(r"^/auto/[0-9a-f]{16}\.webp$")
SKIP_HOST = re.compile(r"(^|\.)(amazon\.[a-z.]+|amzn\.(to|eu)|a\.co|amzlink\.to|hinkowicz\.(de|com))$", re.I)
UA = "Mozilla/5.0 (compatible; HinkowiczVorschau/1.0; +https://hinkowicz.de)"
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
LINK_RE = re.compile(r"<link\b[^>]*>", re.I)
MAX_HTML, MAX_IMG = 1_500_000, 6_000_000


def name_for(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16] + ".webp"


def _attr(tag, name):
    m = re.search(rf'\b{name}\s*=\s*("([^"]*)"|\'([^\']*)\')', tag, re.I)
    return html.unescape(m.group(2) if m.group(2) is not None else m.group(3)) if m else None


def find_image(page_html, base):
    """og:image bzw. twitter:image aus dem HTML-Kopf -> absolute https-URL oder None."""
    found = {}
    for tag in META_RE.findall(page_html[:400_000]):
        key = (_attr(tag, "property") or _attr(tag, "name") or "").lower()
        if key in ("og:image:secure_url", "og:image", "og:image:url", "twitter:image", "twitter:image:src"):
            found.setdefault(key, _attr(tag, "content"))
    candidates = [found[k] for k in ("og:image:secure_url", "og:image", "og:image:url", "twitter:image", "twitter:image:src")
                  if found.get(k)]
    # Ersatz: großes App-Icon der Seite (meist das Logo)
    for tag in LINK_RE.findall(page_html[:400_000]):
        rel = (_attr(tag, "rel") or "").lower()
        if "apple-touch-icon" in rel and _attr(tag, "href"):
            candidates.append(_attr(tag, "href"))
    for c in candidates:
        url = urljoin(base, c.strip())
        if urlparse(url).scheme in ("https", "http"):
            return url.replace("http://", "https://", 1)
    return None


def _get(session, url, limit, ok_codes=(200,), **kw):
    r = session.get(url, timeout=12, stream=True, allow_redirects=True, headers={"User-Agent": UA, **kw})
    if r.status_code not in ok_codes:
        r.close()
        raise ValueError(f"HTTP {r.status_code}")
    data = b""
    for chunk in r.iter_content(65536):
        data += chunk
        if len(data) > limit:
            r.close()
            raise ValueError("zu groß")
    return r, data


def _text(r, data):
    """HTML als Text – UTF-8 zuerst (viele Seiten nennen den Zeichensatz nur im HTML), sonst laut Server."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(r.encoding or "latin-1", "replace")


def to_webp(data):
    """Bild prüfen und als WebP (max. 800 px) speichern; zu kleine Bilder (Icons) verwerfen."""
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    img.load()
    if min(img.size) < 120:
        raise ValueError("zu klein")
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
    img.thumbnail((800, 800))
    out = io.BytesIO()
    img.save(out, "WEBP", quality=80, method=6)
    return out.getvalue()


def wanted(items):
    """Links ohne eigenes Bild, für die ein Auto-Bild erlaubt ist."""
    urls = []
    for it in items:
        url = str(it.get("url") or "").strip()
        if it.get("visible", True) is False or it.get("image") or not url.startswith("https://"):
            continue
        if SKIP_HOST.search(urlparse(url).hostname or ""):
            continue
        if url not in urls:
            urls.append(url)
    return urls


def fetch_one(session, url, previous):
    """-> WebP-Bytes oder None. Erst vom letzten Lauf (eigene Seite), sonst frisch von der verlinkten Seite."""
    name = name_for(url)
    if previous.get(url) == f"/auto/{name}":
        try:
            return _get(session, f"{SITE}/auto/{name}", MAX_IMG)[1]
        except Exception:
            pass
    try:
        # manche Shops antworten mit 404/410, liefern aber trotzdem ihre Seite mit Vorschaubild
        r, data = _get(session, url, MAX_HTML, ok_codes=(200, 203, 404, 410), Accept="text/html,application/xhtml+xml")
        final = r.url
        if SKIP_HOST.search(urlparse(final).hostname or ""):  # Kurzlink führte zu Amazon o. Ä.
            return None
        img_url = find_image(_text(r, data), final)
        if not img_url:
            return None
        return to_webp(_get(session, img_url, MAX_IMG, Accept="image/*", Referer=final)[1])
    except Exception:
        return None


def build(out_dir, groups, offline=False):
    """groups: Listen roher Einträge aus content/*.json -> {url: "/auto/<name>.webp"}; schreibt /auto/."""
    urls = []
    for items in groups:
        urls += [u for u in wanted(items) if u not in urls]
    out = Path(out_dir) / "auto"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if not offline and urls:
        import requests
        session = requests.Session()
        try:
            previous = session.get(f"{SITE}/auto/index.json", timeout=10).json()
        except Exception:
            previous = {}
        with ThreadPoolExecutor(6) as pool:
            for url, webp in zip(urls, pool.map(lambda u: fetch_one(session, u, previous), urls)):
                if webp:
                    (out / name_for(url)).write_bytes(webp)
                    manifest[url] = f"/auto/{name_for(url)}"
    (out / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
    return manifest


TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def find_title(page_html):
    """og:title, sonst twitter:title, sonst <title> – bereinigt und gekürzt."""
    head = page_html[:400_000]
    found = {}
    for tag in META_RE.findall(head):
        key = (_attr(tag, "property") or _attr(tag, "name") or "").lower()
        if key in ("og:title", "twitter:title"):
            found.setdefault(key, _attr(tag, "content"))
    m = TITLE_RE.search(head)
    for t in (found.get("og:title"), found.get("twitter:title"), html.unescape(m.group(1)) if m else None):
        t = re.sub(r"\s+", " ", t or "").strip()
        if t:
            return t if len(t) <= 80 else t[:80].rsplit(" ", 1)[0] + " …"
    return None


def wanted_titles(items):
    urls = []
    for it in items:
        url = str(it.get("url") or "").strip()
        if it.get("visible", True) is False or str(it.get("title") or "").strip() or not url.startswith("https://"):
            continue
        if not SKIP_HOST.search(urlparse(url).hostname or "") and url not in urls:
            urls.append(url)
    return urls


def build_titles(out_dir, groups, offline=False):
    """Titel für Einträge ohne eigenen Titel -> {url: titel}; schreibt /auto/titles.json (vom letzten Lauf übernommen)."""
    urls = []
    for items in groups:
        urls += [u for u in wanted_titles(items) if u not in urls]
    titles = {}
    if not offline and urls:
        import requests
        session = requests.Session()
        try:
            previous = session.get(f"{SITE}/auto/titles.json", timeout=10).json()
        except Exception:
            previous = {}

        def one(url):
            if isinstance(previous.get(url), str) and previous[url].strip():
                return previous[url].strip()[:90]
            try:
                r, data = _get(session, url, MAX_HTML, Accept="text/html,application/xhtml+xml")  # nur echte Seiten, keine 404-Titel
                return find_title(_text(r, data))
            except Exception:
                return None
        with ThreadPoolExecutor(6) as pool:
            titles = {u: t for u, t in zip(urls, pool.map(one, urls)) if t}
    out = Path(out_dir) / "auto"
    out.mkdir(parents=True, exist_ok=True)
    (out / "titles.json").write_text(json.dumps(titles, ensure_ascii=False, indent=0), encoding="utf-8")
    return titles


def load_groups(paths=(("content/links.json", "links"), ("content/setup.json", "items"), ("content/amazon-deals.json", "items"))):
    groups = []
    for path, key in paths:
        p = Path(path)
        if p.exists():
            groups.append((json.loads(p.read_text(encoding="utf-8")) or {}).get(key) or [])
    return groups
