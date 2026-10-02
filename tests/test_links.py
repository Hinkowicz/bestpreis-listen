"""Link-Seite: nur sichere Links/Bilder, Werbekennzeichnung, Reihenfolge."""
import tempfile
import unittest
from pathlib import Path

from gh import links

YAML = """
links:
  - title: Erster
    url: https://example.com/a
    image: /assets/links/bild.webp
  - title: <script>alert(1)</script>
    description: '"><img src=x onerror=alert(1)>'
    url: https://example.com/b?x=1&y=2
    ad: false
  - title: Unsicherer Link
    url: javascript:alert(1)
  - title: Ohne https
    url: http://example.com
  - title: Versteckt
    url: https://example.com/c
    visible: false
  - title: Fremdes Bild
    url: https://example.com/d
    image: https://tracker.example/pixel.gif
  - title: Pfad-Trick
    url: https://example.com/e
    image: ../../etc/passwd
"""


class LinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name) / "links.yml"
        p.write_text(YAML, encoding="utf-8")
        cls.items = links.load(p)
        cls.html = links.page(cls.items, "Test")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_nur_https_und_sichtbare_links_in_reihenfolge(self):
        self.assertEqual([i["title"] for i in self.items],
                         ["Erster", "<script>alert(1)</script>", "Fremdes Bild", "Pfad-Trick"])

    def test_nur_eigene_bilder(self):
        imgs = {i["title"]: i["image"] for i in self.items}
        self.assertEqual(imgs["Erster"], "assets/links/bild.webp")
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


if __name__ == "__main__":
    unittest.main()
