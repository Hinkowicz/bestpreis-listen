# Hinkowicz Bestpreis-Listen

Erzeugt jede Woche automatisch:

- **Gaming-PC-Listen** für 800 / 1.000 / 1.500 / 2.000+ € (Selbstbau-Teile)
- **Top-Technik-Deals** der Woche

Datenquelle ist die Geizhals Partner-API. Alle Links enthalten die Affiliate-Parameter
und sind als Anzeige gekennzeichnet.

## Warum die Listen eigenständig sind

Die Teile werden nicht von anderen Listen übernommen, sondern von einem eigenen Optimierer gewählt:

- Ein **eigener Leistungsindex** steht in `gh/hardware.py` (GPU: RTX 5070 = 100, CPU: 9800X3D = 100).
- Der **Hinko-Score** berechnet sich als GPU^w · CPU^(1−w), wobei die Gewichtung pro Budget unterschiedlich ist.
- Alle CPU×GPU-Kombinationen werden gegen die aktuellen Bestpreise durchgerechnet.
  Das Netzteil wird passend zur Leistung gewählt, und Sockel und RAM-Typ müssen zusammenpassen.
- Eigene **Qualitäts-Whitelists** gibt es für Netzteile, SSDs, Gehäuse und Kühler (`gh/config.py`).
- Pro Liste gibt es einen **Upgrade-Tipp** und einen **Vergleich zur Vorwoche**.

## Seiten

| Datei | Inhalt |
|---|---|
| `index.html` | Übersicht aller Budgets + Top-5-Deals |
| `pc-800.html` … `pc-2000.html` | einzelne PC-Listen |
| `deals.html` | Technik-Deals der Woche |
| `api/*.json` | dieselben Daten für den Discord-Bot |

## Einrichtung (einmalig)

1. Unter Settings → Secrets and variables → Actions → **New repository secret**
   das Secret `GEIZHALS_SECRET` anlegen. Der Wert ist das Shared Secret aus dem Geizhals-Partnerkonto.
2. Unter Settings → Pages bei **Source** die Option „GitHub Actions“ auswählen.
3. Unter Actions → „Wöchentliche Bestpreis-Listen“ → **Run workflow** den ersten Lauf manuell starten.

Danach läuft das Update jeden Montag früh automatisch.

## Lokal testen

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -t .   # Tests
python run.py --mock          # Vorschau mit Beispieldaten → site/
GEIZHALS_SECRET=... python run.py
```

## Pflege

- Erscheinen neue GPUs oder CPUs, trägst du sie in `gh/hardware.py` ein.
- Budgets, Preisgrenzen und Whitelists stehen in `gh/config.py`.
- Wenn ein Kategorie-Code nicht passt, sucht das Tool automatisch über den Kategoriebaum.
  Der Baum wird nach jedem Lauf in `data/cache/categories.json` gespeichert.
