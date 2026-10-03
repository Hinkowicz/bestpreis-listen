# hinkowicz.de – Website & App

Dieses Repo ist **nur** die Website hinkowicz.de und die Link-App (/app/):
Link-Seite, Mein Setup, Gaming-PC-Bestpreis-Listen, Technik-Deals, Amazon-Seite,
Impressum/Datenschutz (auch die Bot-Rechtstexte unter /discord/), Umfrage-Seite.

## Projekte sauber trennen
Der Nutzer möchte, dass jedes Projekt in seinem eigenen Chat bleibt.
Kommt in einem Chat zu diesem Repo eine Anfrage zu einem anderen Projekt, kurz daran erinnern
und auf den passenden Chat verweisen, statt es hier umzusetzen:

- **Discord-Bot (Hinko-Bot):** Repo `Hinkowicz/test`, läuft per Docker auf dem NAS des Nutzers.
  Eigener Chat „Discord-Bot starten“. Ausnahme: Die Rechtstexte liegen hier unter
  `content/discord-*.md`. Ändert der Bot, welche Daten er speichert, muss der Text hier angepasst werden.
- **Mail-Connector (MCP-Server für web.de per IMAP):** eigenes Projekt `mail-connector`, eigener Chat.
- **Routinen** (Tech-News, Second Brain, Monatsbericht, ROG-Liste) sind eigenständig.
  Nur „Amazon-Aktionen prüfen“ gehört hierher (pflegt `content/amazon.json`).

## Wichtig
- Niemals den bürgerlichen Namen des Nutzers verwenden – immer „Hinkowicz“.
- Antworten auf Deutsch, einfach erklärt.
- Die Website ist noch nicht öffentlich beworben; nichts ohne Rückfrage verlinken oder veröffentlichen.
- Tests: `python -m unittest discover -s tests -t .`, Vorschau offline: `python run.py --mock`.
