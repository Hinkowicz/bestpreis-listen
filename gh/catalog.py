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
        """-> dict(cat=..., [xf=...], [preset=...]) für einen Eintrag aus config.CATEGORIES."""
        if key in self._cats:
            return self._cats[key]
        rx = config.CATEGORIES[key]
        for code, path, ids in self.flat():
            if code and re.search(rx, path, re.I):
                sel = {"cat": code}
                if ids.get("xf"):
                    sel["xf"] = ids["xf"]
                if ids.get("preset"):
                    sel["preset"] = ids["preset"]
                self._cats[key] = sel
                return sel
        raise KeyError(f"Kategorie '{key}' nicht im Kategoriebaum gefunden (Regex {rx})")

    # --- Produkte -----------------------------------------------------------
    def products(self, key, sort="p", pagesize=1000, **extra):
        """Alle lieferbaren Produkte einer Kategorie (ein Request)."""
        cache_key = (key, sort, pagesize, tuple(sorted(extra.items())))
        if cache_key not in self._lists:
            sel = dict(self.resolve(key))
            cat = sel.pop("cat")
            if "preset" in sel:
                sel["preset"] = int(sel["preset"])
                sel["new_filters"] = True
            resp = self.api.categorylist(cat, sort=sort, pagesize=pagesize,
                                         v="l", productratings=True, **sel, **extra)
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
