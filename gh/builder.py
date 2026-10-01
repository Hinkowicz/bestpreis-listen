"""Stellt pro Budget-Stufe den PC mit dem besten Hinkowicz-Score zusammen.

Vorgehen:
 1. Basisteile pro Plattform (Board, RAM, SSD, Gehäuse, Kühler) nach eigenen
    Qualitätsregeln wählen: Whitelist + Preis-/Beliebtheitsfenster.
 2. Alle CPU×GPU-Kombinationen durchrechnen, Netzteil passend zur Leistung.
 3. Score = GPU^w · CPU^(1-w), unter Einhaltung von Budget und VRAM-Minimum.
"""
import re

from . import config
from .catalog import product_url
from .hardware import match_cpu, match_gpu

REF_SCORE = (100 ** 0.75) * (100 ** 0.25)  # RTX 5070 + 9800X3D = 100 Punkte
WATT_RE = re.compile(r"(\d{3,4})\s?W\b")


def _price(p):
    return float(p["best_price"])


def value_pick(cands, window=1.08):
    """Unter allen Produkten im Preisfenster (günstigstes × window) das beliebteste."""
    if not cands:
        return None
    cheapest = min(_price(p) for p in cands)
    pool = [p for p in cands if _price(p) <= cheapest * window]
    return min(pool, key=lambda p: (p.get("_rank", 9999), _price(p)))


def popular_pick(cands, price_max):
    pool = [p for p in cands if _price(p) <= price_max]
    return min(pool, key=lambda p: p.get("_rank", 9999)) if pool else None


def _filter(prods, include=None, exclude=None, prefer=None):
    out = [p for p in prods
           if (not include or re.search(include, p["product"], re.I))
           and not (exclude and re.search(exclude, p["product"], re.I))]
    if prefer:
        good = [p for p in out if re.search(prefer, p["product"], re.I)]
        if good:
            return good
    return out


class Builder:
    def __init__(self, catalog):
        self.cat = catalog

    # --- Einzelteile --------------------------------------------------------
    def board(self, plat, tier):
        pc = config.PLATFORMS[plat]
        excl = r"\bITX\b|refurb|B-Ware"
        if pc.get("mb_exclude"):
            excl += "|" + pc["mb_exclude"]
        cands = _filter(self.cat.products(pc["mb"], sort="t"), pc["mb_regex"], excl)
        cands = [p for p in cands if re.search(config.BOARD_BRANDS, p["product"])]
        if tier["board_wifi"]:
            cands = [p for p in cands if re.search(r"WIFI|Wi-?Fi|\bAX\b", p["product"], re.I)] or cands
        return value_pick(cands, 1.12)

    def ram(self, plat, tier):
        pc = config.PLATFORMS[plat]
        gb = tier["ram_gb"]
        cands = _filter(self.cat.products(pc["ram"], sort="t"),
                        rf"Kit {gb}GB|{gb}GB.*Kit|2x\s?{gb // 2}GB",
                        r"SO-DIMM|RDIMM|Registered|\bECC\b(?!.*on-die)")
        cands = [p for p in cands if re.search(pc["ram_speed"], p["product"])]
        fast = [p for p in cands if re.search(r"DDR5-6000|DDR4-3600", p["product"])]
        best = value_pick(cands, 1.05)
        best_fast = value_pick(fast, 1.05)
        if best_fast and best and _price(best_fast) <= _price(best) * 1.12:
            return best_fast
        return best

    def ssd(self, tier):
        tb = tier["ssd_tb"]
        cands = _filter(self.cat.products("ssd", sort="t"), rf"\b{tb}\s?TB\b.*M\.2|M\.2.*\b{tb}\s?TB\b",
                        r"SATA|2,5\"|extern|Portable|USB", prefer=config.SSD_GOOD)
        return value_pick(cands, 1.10)

    def case(self, tier):
        cands = _filter(self.cat.products("case", sort="t"), None,
                        r"mit Netzteil|inkl\. Netzteil|\b\d{3}W\b|Mini-ITX|ITX-Gehäuse",
                        prefer=config.CASE_GOOD)
        return popular_pick(cands, tier["case_max"])

    def cooler(self, tier):
        cands = _filter(self.cat.products("cooler", sort="t"), None, r"Wärmeleitpaste$|Lüfter für",
                        prefer=config.COOLER_GOOD)
        return popular_pick(cands, tier["cooler_max"])

    def psu(self, watt_needed, tier):
        cands = []
        for p in _filter(self.cat.products("psu", sort="t"), None, r"\bSFX\b|\bTFX\b|Flex",
                         prefer=config.PSU_GOOD):
            m = WATT_RE.search(p["product"])
            if m and int(m.group(1)) >= watt_needed:
                cands.append(p)
        if tier["budget"] >= 1500:  # ab High-End: modulares, aktuelles Netzteil
            cands = [p for p in cands if re.search(r"ATX 3|modular|Gold|Platinum", p["product"], re.I)] or cands
        return value_pick(cands, 1.08)

    def gpus(self):
        best = {}
        for p in self.cat.products("gpu", sort="p"):
            g = match_gpu(p["product"])
            if not g:
                continue
            k = (g["chip"], g["vram"])
            if k not in best or _price(p) < _price(best[k][0]):
                best[k] = (p, g)
        return list(best.values())

    def cpus(self, plat):
        best = {}
        for p in self.cat.products(config.PLATFORMS[plat]["cpu"], sort="p"):
            c = match_cpu(p["product"], plat)
            if not c:
                continue
            # günstigste Variante je Chip – getrennt nach "mit Kühler" (boxed) und ohne
            k = (c["chip"], bool(re.search(r"ohne Kühler|\btray\b|\bWOF\b", p["product"], re.I)))
            if k not in best or _price(p) < _price(best[k][0]):
                best[k] = (p, c)
        return list(best.values())

    # --- Optimierung --------------------------------------------------------
    def build_tier(self, tier):
        w = tier["gpu_weight"]
        combos = []
        gpus = [(p, g) for p, g in self.gpus() if g["vram"] >= tier["min_vram"]]
        ssd, case, cooler = self.ssd(tier), self.case(tier), self.cooler(tier)
        for plat in tier["platforms"]:
            board, ram = self.board(plat, tier), self.ram(plat, tier)
            base = [board, ram, ssd, case]
            if not all(base) or not cooler:
                names = ["Board", "RAM", "SSD", "Gehäuse"]
                missing = [n for n, x in zip(names, base) if not x] + ([] if cooler else ["Kühler"])
                print(f"::warning::{tier['id']}€/{plat}: Basisteil fehlt ({', '.join(missing)})")
                continue
            base_cost = sum(_price(p) for p in base)
            psu_cache = {}
            for cp, c in self.cpus(plat):
                # Einsteiger-Stufen: mitgelieferter Boxed-Kühler reicht für 65-W-CPUs
                boxed = (tier.get("boxed_cooler_ok") and c["watt"] <= 65
                         and re.search(r"\bboxed\b", cp["product"], re.I)
                         and not re.search(r"ohne Kühler|\btray\b|\bWOF\b", cp["product"], re.I))
                cpu_cooler = None if boxed else cooler
                for gp, g in gpus:
                    need = g["psu"] + (100 if c["watt"] > 150 else 0)
                    need = max(550, need)
                    if need not in psu_cache:
                        psu_cache[need] = self.psu(need, tier)
                    psu = psu_cache[need]
                    if not psu:
                        continue
                    total = base_cost + _price(cp) + _price(gp) + _price(psu)
                    total += _price(cpu_cooler) if cpu_cooler else 0
                    score = (g["perf"] ** w) * (c["perf"] ** (1 - w)) / REF_SCORE * 100
                    combos.append({"total": total, "score": score, "plat": plat,
                                   "cpu": (cp, c), "gpu": (gp, g), "board": board, "ram": ram,
                                   "ssd": ssd, "case": case, "cooler": cpu_cooler, "psu": psu})
        within = [x for x in combos if x["total"] <= tier["max"]]
        if not within:
            return None
        best = max(within, key=lambda x: (round(x["score"], 1), -x["total"]))
        # Upgrade-Tipp: bis +15 % Budget, mindestens +8 % Score
        ups = [x for x in combos if best["total"] < x["total"] <= tier["max"] * 1.15
               and x["score"] >= best["score"] * 1.08]
        upgrade = max(ups, key=lambda x: x["score"] / x["total"]) if ups else None
        return self._format(tier, best, upgrade)

    def _format(self, tier, b, up):
        def part(slot, p, extra=""):
            return {"slot": slot, "name": p["product"], "price": round(_price(p), 2), "id": p["id"],
                    "url": product_url(p["id"]), "image": p.get("image_thumb"), "note": extra,
                    "merchant": p.get("hname")}
        cp, c = b["cpu"]
        gp, g = b["gpu"]
        parts = [
            part("Prozessor", cp, c["chip"]),
            part("Grafikkarte", gp, f"{g['chip']} · {g['vram']} GB"),
            part("Mainboard", b["board"], b["plat"]),
            part("Arbeitsspeicher", b["ram"], f"{tier['ram_gb']} GB"),
            part("SSD", b["ssd"], f"{tier['ssd_tb']} TB NVMe"),
            part("CPU-Kühler", b["cooler"]) if b["cooler"] else
            {"slot": "CPU-Kühler", "name": "Boxed-Kühler (liegt der CPU bei)", "price": 0.0, "id": None,
             "url": None, "image": None, "note": "reicht für diese CPU aus", "merchant": None},
            part("Netzteil", b["psu"]),
            part("Gehäuse", b["case"]),
        ]
        out = {
            "tier": tier["id"], "name": tier["name"], "budget": tier["budget"],
            "platform": b["plat"], "total": round(b["total"], 2), "score": round(b["score"]),
            "parts": parts,
        }
        if up:
            ug, ugi = up["gpu"]
            uc, uci = up["cpu"]
            changes = []
            if ugi["chip"] != g["chip"] or ugi["vram"] != g["vram"]:
                changes.append(f"{ugi['chip']} ({ugi['vram']} GB) statt {g['chip']}")
            if uci["chip"] != c["chip"]:
                changes.append(f"{uci['chip']} statt {c['chip']}")
            if changes:
                out["upgrade"] = {
                    "extra": round(up["total"] - b["total"]),
                    "gain": round((up["score"] / b["score"] - 1) * 100),
                    "text": " + ".join(changes),
                }
        return out
