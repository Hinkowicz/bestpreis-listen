"""Startseite: nur sichere Links/Bilder, Werbekennzeichnung, Reihenfolge, keine Fremdinhalte."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from gh import links

DATA = {"links": [
    {"title": "Erster", "url": "https://example.com/a", "image": "/assets/links/bild.webp", "featured": True},
    {"title": "<script>alert(1)</script>", "description": '"><img src=x onerror=alert(1)>',
     "url": "https://example.com/b?x=1&y=2", "ad": False},
    {"title": "Unsicherer Link", "url": "javascript:alert(1)"},
    {"title": "Ohne https", "url": "http://example.com"},
    {"title": "Versteckt", "url": "https://example.com/c", "visible": False},
    {"title": "Fremdes Bild", "url": "https://example.com/d", "image": "https://tracker.example/pixel.gif"},
    {"title": "Pfad-Trick", "url": "https://example.com/e", "image": "../../etc/passwd"},
]}
SITE = {"tagline": "Gaming", "contact": "a@b.de", "socials": [
    {"name": "TikTok", "url": "https://tiktok.com/@x"}, {"name": "Unbekannt", "url": "https://x.y"},
    {"name": "YouTube", "url": "javascript:alert(1)"}]}


class LinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        (d / "links.json").write_text(json.dumps(DATA), encoding="utf-8")
        (d / "site.json").write_text(json.dumps(SITE), encoding="utf-8")
        cls.items = links.load(d / "links.json")
        cls.site = links.load_site(d / "site.json")
        cls.html = links.page(cls.items, cls.site, "Test")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_nur_https_und_sichtbare_links_in_reihenfolge(self):
        self.assertEqual([i["title"] for i in self.items],
                         ["Erster", "<script>alert(1)</script>", "Fremdes Bild", "Pfad-Trick"])

    def test_nur_eigene_bilder(self):
        imgs = {i["title"]: i["image"] for i in self.items}
        self.assertEqual(imgs["Erster"], "/assets/links/bild.webp")
        self.assertIsNone(imgs["Fremdes Bild"])
        self.assertIsNone(imgs["Pfad-Trick"])

    def test_eingaben_werden_entschaerft(self):
        self.assertNotIn("<script>alert", self.html)
        self.assertNotIn("<img src=x", self.html)
        self.assertNotIn("javascript:", self.html)

    def test_werbung_standardmaessig_gekennzeichnet(self):
        self.assertTrue(self.items[0]["ad"])
        self.assertFalse(self.items[1]["ad"])
        self.assertIn('rel="sponsored noopener"', self.html)
        self.assertIn("Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.", self.html)

    def test_hervorgehobener_link_als_grosse_karte(self):
        self.assertIn('class="feat glass', self.html)

    def test_nur_bekannte_socials_mit_https(self):
        self.assertEqual([s["name"] for s in self.site["socials"]], ["TikTok"])

    def test_nur_eigenes_skript_und_keine_fremdinhalte(self):
        self.assertEqual(re.findall(r"<script[^>]*>", self.html), ['<script src="/assets/site.js" defer>'])
        self.assertEqual(re.findall(r'(?:src|srcset)="(?:https?:)?//[^"]*"|url\((?:https?:)?//', self.html), [])

    def test_echte_inhalte_sind_gueltig(self):
        real = links.load("content/links.json")
        self.assertGreater(len(real), 0)
        for l in real:
            if l["image"]:
                self.assertTrue(Path(l["image"].lstrip("/")).exists(), l["image"])


class NeueFunktionenTest(unittest.TestCase):
    def test_rabattcode_button_entschaerft(self):
        l = links.clean({"title": "X", "url": "https://a.de", "code": '"><script>alert(1)</script>'})
        html = links.card(l, 1)
        self.assertIn('class="code"', html)
        self.assertNotIn("<script>alert", html)

    def test_ablaufdatum(self):
        self.assertIsNone(links.clean({"title": "Alt", "url": "https://a.de", "until": "2020-01-01"}))
        self.assertIsNotNone(links.clean({"title": "Neu", "url": "https://a.de", "until": "2999-01-01"}))
        self.assertIsNotNone(links.clean({"title": "Heute", "url": "https://a.de", "until": links.today().isoformat()}))
        self.assertIsNotNone(links.clean({"title": "Kaputt", "url": "https://a.de", "until": "irgendwann"}))

    def test_setup_seite(self):
        from gh import pages
        items = links.load("content/setup.json", key="items", extra=("category",))
        self.assertGreater(len(items), 10)
        html = pages.setup_page(items)
        self.assertIn('id="monitore-halterungen"', html)
        self.assertEqual(re.findall(r'src="(?:https?:)?//[^"]*"', html), [])
        for it in items:
            if it["image"]:
                self.assertTrue(Path(it["image"].lstrip("/")).exists(), it["image"])

    def test_404_und_vorschaukarten(self):
        from gh import og, pages
        self.assertIn("404", pages.not_found_page())
        meta = og.meta("Titel", "Beschreibung", "home.png", "/")
        self.assertIn('content="https://hinkowicz.de/og/home.png"', meta)
        with tempfile.TemporaryDirectory() as d:
            og.card(Path(d) / "x.png", "Kicker", "Titel", ["Zeile"], big="1.000 €")
            from PIL import Image
            self.assertEqual(Image.open(Path(d) / "x.png").size, (1200, 630))


class LegalTest(unittest.TestCase):
    def test_impressum_und_datenschutz(self):
        from gh import legal
        imp = legal.page("Impressum", Path("content/impressum.md").read_text(encoding="utf-8"))
        ds = legal.page("Datenschutz", Path("content/datenschutz.md").read_text(encoding="utf-8"))
        self.assertIn("§ 5 DDG", imp)
        self.assertIn("Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.", imp)
        self.assertIn("GitHub Pages", ds)
        self.assertIn("Amazon PartnerNet", ds)
        for html in (imp, ds):
            self.assertNotIn("<script", html.lower())
            self.assertNotIn("pc.hinkowicz.de", html)
            self.assertNotIn("[entfernt]", html)
            self.assertEqual(re.findall(r'(?:src|srcset)="(?:https?:)?//[^"]*"', html), [])

    def test_markdown_entschaerft(self):
        from gh import legal
        out = legal.to_html("##Titel\n<script>x</script> **fett** https://a.de/x?y=1")
        self.assertNotIn("<script>", out)
        self.assertIn("<strong>fett</strong>", out)
        self.assertIn('href="https://a.de/x?y=1"', out)


if __name__ == "__main__":
    unittest.main()
