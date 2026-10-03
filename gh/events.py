"""Amazon-Aktionen (Prime Day, Black Friday …) – nur Standardbibliothek, damit der Workflow es ohne Installation prüfen kann."""
import json
from pathlib import Path


def load_event(path="content/amazon.json", today=None):
    """Aktionen (Prime Day, Black Friday …) aus content/amazon.json -> die gerade laufende, sonst die nächste.

    Nur während einer Aktion wird die Amazon-Liste berechnet und alle 3 Stunden erneuert.
    """
    from datetime import date, datetime
    from zoneinfo import ZoneInfo
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    today = today or datetime.now(ZoneInfo("Europe/Berlin")).date()

    def day(v):
        try:
            return date.fromisoformat(str(v or ""))
        except ValueError:
            return None
    events = []
    for ev in data.get("events") or []:
        start, end = day(ev.get("from")), day(ev.get("until"))
        if start and end and start <= end:
            events.append({"event": str(ev.get("event") or "").strip()[:40], "from": start, "until": end})
    events.sort(key=lambda x: x["from"])
    current = next((x for x in events if x["from"] <= today <= x["until"]), None)
    upcoming = next((x for x in events if x["from"] > today), None)
    pick = current or upcoming or {"event": "", "from": None, "until": None}
    return {**pick, "active": current is not None}
