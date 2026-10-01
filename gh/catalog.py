"""Kategorie-Auflösung und Produktabruf (mit Cache pro Lauf)."""
import json
import re
from pathlib import Path

from . import config


def _flatten(nodes, path=(), out=None):
    """Erzeugt (cat_code, 'Top > Mid > Low', ids) für alle Ebenen des Baums."""
    out = [] if out is None else out
    for n in nodes or []:
        title = n.get("title", "")
        ids = n.get("id") or {}
        p = path + (title,)
        out.append((ids.get("cat"), " > ".join(p), ids))
        _flatten(n.get("childs"), p, out)
    return out


class Catalog:
    def __init__(self, api, cache_dir="data/cache"):
        self.api = api
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._tree = None
        self._cats = {}
        self._lists = {}

    # --- Kategorien ---------------------------------------------------------
    def tree(self):
        if self._tree is None:
            self._tree = self.api.categories()
            (self.cache_dir / "categories.json").write_text(
                json.dumps(self._tree, ensure_ascii=False, indent=1), encoding="utf-8")
        return self._tree

    def flat(self):
        return _flatten(self.tree())

    def top_categories(self):
        """[(m_id, title)] der obersten Ebene."""
        return [((n.get("id") or {}).get("m"), n.get("title", "")) for n in self.tree()]

    def resolve(self, key):
        if key in self._cats:
            return self._cats[key]
        code, rx = config.CATEGORIES[key]
        flat = [(c, p) for c, p, _ in self.flat() if c]
        codes = {c for c, _ in flat}
        if code not in codes:
            hits = [c for c, p in flat if re.search(rx, p, re.I)]
            if not hits:
                raise KeyError(f"Kategorie '{key}' nicht gefunden (Code {code}, Regex {rx})")
            print(f"  [info] Kategorie {key}: '{code}' unbekannt, nutze '{hits[0]}'")
            code = hits[0]
        self._cats[key] = code
        return code

    # --- Produkte -----------------------------------------------------------
    def products(self, key, sort="p", pagesize=1000, **extra):
        """Alle lieferbaren Produkte einer Kategorie (ein Request)."""
        cache_key = (key, sort, pagesize, tuple(sorted(extra.items())))
        if cache_key not in self._lists:
            resp = self.api.categorylist(self.resolve(key), sort=sort, pagesize=pagesize,
                                         v="l", productratings=True, **extra)
            prods = [p for p in resp.get("products", []) if p.get("best_price")]
            for rank, p in enumerate(prods):
                p["_rank"] = rank
            self._lists[cache_key] = prods
        return self._lists[cache_key]


def product_url(pid):
    return f"{config.GEIZHALS_BASE}/a{pid}.html?{config.AFFILIATE_PARAMS}"


def with_affiliate(url):
    """Hängt die Affiliate-Parameter an einen beliebigen Geizhals-Link an."""
    if not url:
        return url
    if url.startswith("//"):
        url = "https:" + url
    sep = "&" if "?" in url else "?"
    return url + sep + config.AFFILIATE_PARAMS
