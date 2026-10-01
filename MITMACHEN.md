# Mitmachen: Feedback zu den PC-Listen

## Der einfachste Weg (ohne Programmieren)

1. Einen kostenlosen GitHub-Account anlegen.
2. Auf https://github.com/Hinkowicz/bestpreis-listen/issues/new/choose die Vorlage
   **„Hardware-Feedback zu den PC-Listen“** wählen und ausfüllen.
3. Hinkowicz sagt Claude Bescheid. Claude liest die Issues und setzt die Änderungen um.

## Wo was geregelt ist (für Fortgeschrittene)

| Was | Datei |
|---|---|
| Leistungswerte von GPUs und CPUs (Hinko-Score) | `gh/hardware.py` |
| Budgets, Mindest-CPU, VRAM-Minimum, RAM-Größe, Preisgrenzen für Gehäuse und Kühler | `gh/config.py` → `TIERS` |
| Bevorzugte Marken und Serien (Netzteile, SSDs, Gehäuse, Kühler, Boards) | `gh/config.py` → `*_GOOD`, `PSU_PREMIUM`, `BOARD_BRANDS` |
| Auswahl-Logik | `gh/builder.py` |

Änderungen werden beim nächsten Lauf aktiv. Der Lauf startet jeden Montag automatisch,
oder du startest ihn manuell unter *Actions → Run workflow*.
