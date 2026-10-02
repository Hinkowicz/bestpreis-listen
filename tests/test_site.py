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
        cls.pages = {p.name: p.read_text(encoding="utf-8") for p in cls.out.glob("*.html")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_genau_vier_pc_seiten_plus_deals_und_index(self):
        self.assertEqual(sorted(self.pages),
                         ["deals.html", "index.html", "pc-1000.html", "pc-1500.html", "pc-2000.html", "pc-800.html"])

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
        self.assertIn('src="img/123.jpg"', render.img("img/123.jpg"))


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
