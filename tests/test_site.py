"""Prüft die Kernanforderungen mit Beispieldaten (ohne API-Zugang).

  python -m unittest -v
"""
import re
import tempfile
import unittest
from pathlib import Path

from gh import config, deals, render
from gh.builder import Builder
from gh.catalog import Catalog
from gh.hardware import match_cpu, match_gpu
from gh.mock import MockAPI


class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        api = MockAPI()
        catalog = Catalog(api, cache_dir=Path(cls.tmp.name) / "cache")
        builder = Builder(catalog)
        cls.builds = [b for b in (builder.build_tier(t) for t in config.TIERS) if b]
        cls.deals = deals.collect(catalog, api)
        cls.out = Path(cls.tmp.name) / "site"
        render.write_site(cls.out, cls.builds, cls.deals, None, "Test")
        cls.pages = {str(p.relative_to(cls.out)): p.read_text(encoding="utf-8") for p in cls.out.rglob("*.html")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_genau_vier_pc_seiten_plus_deals_und_index(self):
        self.assertEqual(sorted(self.pages), ["deals/index.html", "pc/1000.html", "pc/1500.html",
                                              "pc/2000.html", "pc/800.html", "pc/index.html"])

    def test_jeder_geizhals_link_hat_affiliate_parameter(self):
        for name, html in self.pages.items():
            links = re.findall(r'href="(https://geizhals\.de/[^"]*)"', html)
            for link in links:
                self.assertIn(config.AFFILIATE_PARAMS.replace("&", "&amp;"), link, f"{name}: {link}")
        self.assertTrue(any("geizhals.de" in h for h in self.pages.values()))

    def test_jede_seite_ist_als_anzeige_gekennzeichnet(self):
        for name, html in self.pages.items():
            self.assertIn("<b>Anzeige</b>", html, name)

    def test_affiliate_links_sind_als_sponsored_markiert(self):
        for name, html in self.pages.items():
            for tag in re.findall(r'<a [^>]*href="https://geizhals\.de/[^>]*>', html):
                self.assertIn('rel="sponsored', tag, name)

    def test_builds_bleiben_im_budget(self):
        self.assertEqual(len(self.builds), len(config.TIERS))
        tiers = {t["id"]: t for t in config.TIERS}
        for b in self.builds:
            self.assertLessEqual(b["total"], tiers[b["tier"]]["max"], b["tier"])
            self.assertAlmostEqual(b["total"], sum(p["price"] for p in b["parts"]), places=1)

    def test_keine_skripte_auf_den_seiten(self):
        for name, html in self.pages.items():
            self.assertNotIn("<script", html.lower(), name)

    def test_nichts_wird_von_fremden_servern_geladen(self):  # Datenschutz: keine IP-Weitergabe
        for name, html in self.pages.items():
            self.assertEqual(re.findall(r'(?:src|srcset)="(?:https?:)?//[^"]*"|url\((?:https?:)?//', html), [], name)

    def test_nur_selbst_gehostete_bilder(self):
        self.assertIn("noimg", render.img("https://gzhls.at/i/1/2/123-s0.jpg"))
        self.assertIn("noimg", render.img("javascript:alert(1)"))
        self.assertIn('src="/img/123.jpg"', render.img("/img/123.jpg"))
        self.assertIn("noimg", render.img("img/../../x.jpg"))


class HardwareTest(unittest.TestCase):
    def test_vram_nicht_aus_modellnummer(self):  # Regression: "Arc B570" wurde als 70 GB gelesen
        self.assertEqual(match_gpu("ASRock Arc B570 Challenger OC, 10GB GDDR6")["vram"], 10)
        self.assertEqual(match_gpu("Intel Arc B570 Limited Edition")["vram"], 10)

    def test_gpu_varianten_werden_unterschieden(self):
        self.assertEqual(match_gpu("Palit GeForce RTX 5060 Ti Dual, 8GB")["chip"], "GeForce RTX 5060 Ti")
        self.assertEqual(match_gpu("Gigabyte GeForce RTX 5060 Windforce, 8GB")["chip"], "GeForce RTX 5060")
        self.assertEqual(match_gpu("Sapphire Pulse Radeon RX 9070 XT, 16GB")["chip"], "Radeon RX 9070 XT")
        self.assertEqual(match_gpu("XFX Swift Radeon RX 9070, 16GB")["chip"], "Radeon RX 9070")

    def test_cpu_nur_auf_passender_plattform(self):
        self.assertIsNotNone(match_cpu("AMD Ryzen 5 7600, 6C/12T, boxed", "AM5"))
        self.assertIsNone(match_cpu("AMD Ryzen 5 7600, 6C/12T, boxed", "AM4"))
        self.assertEqual(match_cpu("AMD Ryzen 5 7600X, 6C/12T", "AM5")["chip"], "Ryzen 5 7600X")


if __name__ == "__main__":
    unittest.main()


class AmazonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gh import amazon
        cls.tmp = tempfile.TemporaryDirectory()
        api = MockAPI()
        catalog = Catalog(api, cache_dir=Path(cls.tmp.name) / "cache")
        cls.items, cls.cache, _ = amazon.collect(catalog, api, offline=True)
        amazon.write(cls.tmp.name, cls.items, cls.cache, config.TIERS, "Test")
        cls.page = (Path(cls.tmp.name) / "amazon" / "index.html").read_text(encoding="utf-8")
        cls.redirect = (Path(cls.tmp.name) / "a" / "index.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_nur_amazon_deals_mit_asin(self):
        self.assertTrue(self.items)
        for d in self.items:
            self.assertRegex(d["merchant"], r"(?i)^amazon")
            self.assertEqual(d["url"], "/a/?i=" + d["asin"])

    def test_links_gekennzeichnet_und_ueber_weiterleitung(self):
        hrefs = re.findall(r'<a class="card deal[^>]*href="([^"]+)"[^>]*rel="sponsored noopener"', self.page)
        self.assertEqual(len(hrefs), len(self.items))
        self.assertTrue(all(h.startswith("/a/?i=") for h in hrefs))
        self.assertIn("Anzeige", self.page)
        self.assertIn("Als Amazon-Partner verdiene ich an qualifizierten Verkäufen", self.page)
        self.assertIn("noindex", self.page)

    def test_weiterleitung_mit_partner_tag_und_ohne_fremdinhalte(self):
        js = Path("assets/amazon.js").read_text(encoding="utf-8")
        self.assertIn(f"const TAG = '{config.AMAZON_TAG}'", js)
        self.assertIn("com.amazon.mShop.android.shopping", js)
        self.assertEqual(re.findall(r'<script[^>]*src="([^"]+)"', self.redirect), ["/assets/amazon.js"])
        self.assertIn("Anzeige", self.redirect)
        self.assertNotRegex(self.redirect, r'(src|href)="https?://(?!www\.amazon\.de/")')

    def test_ausserhalb_der_aktion_leer(self):
        from gh import amazon
        html = amazon.amazon_page(self.items, config.TIERS, "Test", "", active=False)
        self.assertNotIn("/a/?i=", html)
        self.assertIn("Gerade läuft keine Aktion", html)
        from datetime import date
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"events": [{"event": "BF", "from": "2026-11-20", "until": "2026-11-30"},'
                    ' {"event": "PD", "from": "2026-10-06", "until": "2026-10-08"}, {"event": "kaputt", "from": "x"}]}')
        ev = lambda d: amazon.load_event(f.name, date.fromisoformat(d))
        self.assertEqual((ev("2026-10-03")["active"], ev("2026-10-03")["event"]), (False, "PD"))  # nächste Aktion
        self.assertEqual((ev("2026-10-06")["active"], ev("2026-10-06")["event"]), (True, "PD"))
        self.assertFalse(ev("2026-10-09")["active"])
        self.assertEqual((ev("2026-11-30")["active"], ev("2026-11-30")["event"]), (True, "BF"))
        self.assertFalse(ev("2026-12-01")["active"])
        Path(f.name).unlink()

    def test_asin_aus_antwort(self):
        from gh.amazon import _find_asin
        self.assertEqual(_find_asin({"response": [{"x": 1, "asin": "B0ABCDEF12"}]}), "B0ABCDEF12")
        self.assertEqual(_find_asin({"asins": [{"asin": "B0ABCDEF12"}]}), "B0ABCDEF12")
        self.assertIsNone(_find_asin({"asin": "<script>"}))
