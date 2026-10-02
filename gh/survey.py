"""Merch-Umfrage: versteckte Seite (/umfrage/<slug>/, nirgends verlinkt, noindex).

Die Antworten gehen per POST an ein Google-Apps-Script, das sie in eine Google-Tabelle schreibt.
Fragen stehen nur hier; Seite und Apps-Script (tools/merch-umfrage.gs) werden daraus erzeugt,
damit das Skript nur Antworten annimmt, die es auf der Seite auch gibt.
"""
import json
import re
from pathlib import Path

from .render import e, head_icons, legal_links, logo_html
from .theme import BASE

ENDPOINT_RE = re.compile(r"^https://script\.google\.com/macros/s/[A-Za-z0-9_-]{20,}/exec$")
TEXT_MAX = 500

# (key, Typ, Frage, Hinweis, Optionen) – Typ: one = eine Antwort, many = mehrere, text = Freitext
QUESTIONS = [
    ("produkte", "many", "Was würdest du dir holen?", "Mehrere möglich",
     ["T-Shirt", "Hoodie", "Zip-Hoodie", "Sweatshirt", "Jogginghose", "Shorts", "Cap", "Beanie",
      "Mauspad", "Sticker", "Tasse", "Tote Bag"]),
    ("schnitt", "one", "Welchen Schnitt trägst du?", None,
     ["Unisex", "Herren", "Damen"]),
    ("groesse", "one", "Welche Größe trägst du oben?", None,
     ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]),
    ("fit", "one", "Wie soll es sitzen?", None,
     ["Oversized – schön weit", "Regular – ganz normal", "Slim – eher eng"]),
    ("stoff", "one", "Welcher Stoff?", None,
     ["Heavyweight – dick & robust", "Mittel – klassisch", "Leicht – dünn & luftig"]),
    ("material", "many", "Was ist dir beim Material wichtig?", "Mehrere möglich",
     ["Bio-Baumwolle", "Recycelt", "Extra weich", "Formstabil nach dem Waschen", "Hauptsache günstig", "Egal"]),
    ("farben", "many", "Welche Farben würdest du tragen?", "Mehrere möglich",
     ["Schwarz", "Weiß", "Grau", "Creme / Off-White", "Navy", "Cyan", "Magenta", "Pastell", "Bunt"]),
    ("design", "many", "Welcher Design-Stil?", "Mehrere möglich",
     ["Minimal – kleines Logo", "Großer Print auf dem Rücken", "Hinkowicz-Muster (All-over)",
      "Nur das Monogramm", "Schriftzug „Hinkowicz“", "Gaming- / Tech-Motive", "Insider aus den Videos"]),
    ("position", "many", "Wo soll das Logo hin?", "Mehrere möglich",
     ["Brust links", "Brust mittig", "Rücken", "Ärmel", "Nacken"]),
    ("veredelung", "one", "Gestickt oder gedruckt?", None,
     ["Gestickt", "Gedruckt", "Egal"]),
    ("preis_shirt", "one", "Was würdest du für ein T-Shirt ausgeben?", None,
     ["Bis 20 €", "20–30 €", "30–40 €", "Über 40 €"]),
    ("preis_hoodie", "one", "Und für einen Hoodie?", None,
     ["Bis 45 €", "45–60 €", "60–75 €", "Über 75 €"]),
    ("drop", "one", "Limitierter Drop oder immer erhältlich?", None,
     ["Limitiert – macht es besonders", "Immer erhältlich", "Egal"]),
    ("plattform", "one", "Wo schaust du mich am meisten?", None,
     ["TikTok", "YouTube", "Instagram", "Twitch", "Discord"]),
    ("ideen", "text", "Noch Ideen oder Wünsche?", "Optional – Motive, Sprüche, Produkte …", None),
]
KEYS = [q[0] for q in QUESTIONS]

CSS = r"""
.sv{max-width:620px;margin:0 auto;padding:calc(14px + env(safe-area-inset-top)) 16px calc(24px + env(safe-area-inset-bottom));
  min-height:100vh;min-height:100dvh;display:flex;flex-direction:column}
.sv .top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px}
.sv .wordmark{height:30px;width:auto}
.bar{height:6px;border-radius:9px;background:var(--chip);overflow:hidden;margin:4px 0 18px}
.bar i{display:block;height:100%;width:0;border-radius:inherit;background:linear-gradient(90deg,var(--accent),var(--accent2));
  transition:width .5s var(--spring)}
.step{display:none;padding:24px 20px;border-radius:30px}
.step.on{display:block;animation:rise .55s var(--spring) both}
.step .n{font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}
.step h1{font-size:clamp(28px,7.5vw,40px);margin:8px 0 8px;letter-spacing:-.03em;line-height:1.08}
.step h2{font-size:clamp(23px,6.4vw,30px);margin:6px 0 4px;letter-spacing:-.02em;line-height:1.15}
.step .hint{color:var(--muted);font-size:14px;margin:0 0 16px}
.opts{display:flex;flex-wrap:wrap;gap:8px}
.opts.list{display:grid}
.opt{font:inherit;font-weight:650;font-size:15.5px;color:var(--text);cursor:pointer;padding:12px 16px;border-radius:999px;
  background:var(--chip);border:1px solid var(--edge);transition:transform .35s var(--spring),background .2s,border-color .2s}
.opts.list .opt{border-radius:18px;text-align:left;padding:15px 18px}
.opt:active{transform:scale(.95)}
.opt[aria-pressed="true"]{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-color:transparent;
  box-shadow:0 10px 24px -12px var(--accent2),inset 0 1px 0 rgba(255,255,255,.45)}
textarea.in{width:100%;min-height:140px;resize:vertical;font:inherit;font-size:16px;color:var(--text);padding:14px 16px;
  border-radius:20px;border:1px solid var(--edge);background:var(--chip);outline:none}
textarea.in:focus{border-color:var(--accent)}
.count{color:var(--faint);font-size:12px;text-align:right;margin-top:6px}
.nav{display:flex;gap:10px;margin-top:20px}
.nav .btn{flex:1;padding:15px 18px;font-size:16px;border:0;cursor:pointer;font-family:inherit}
.nav .btn[disabled]{opacity:.4;cursor:default}
.nav .ghost{flex:0 0 auto;background:var(--chip);color:var(--text);box-shadow:none;border:1px solid var(--edge)}
.intro p{color:var(--muted);line-height:1.55}
.intro ul{color:var(--muted);padding-left:20px;margin:10px 0 0;line-height:1.7}
.done{text-align:center}.done .big{font-size:64px;margin:6px 0}
.err{color:var(--bad);font-size:14px;margin-top:12px;min-height:1em}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.sv footer{margin-top:auto;padding-top:22px;text-align:center;color:var(--faint);font-size:12.5px}
.sv footer a{color:inherit}
"""


def load(path="content/umfrage.json"):
    p = Path(path)
    cfg = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    slug = cfg.get("slug") or ""
    endpoint = cfg.get("endpoint") or ""
    return {"slug": slug if re.fullmatch(r"[a-z0-9-]{6,60}", slug) else "",
            "endpoint": endpoint if ENDPOINT_RE.match(endpoint) else ""}


def _question(i, q):
    key, kind, title, hint, opts = q
    num = f'<div class="n">Frage {i} von {len(QUESTIONS)}</div>'
    hint_html = f'<p class="hint">{e(hint)}</p>' if hint else '<p class="hint">Eine Antwort wählen, dann „Weiter“</p>'
    if kind == "text":
        body = (f'<textarea class="in" name="{key}" maxlength="{TEXT_MAX}" placeholder="Schreib einfach drauf los …"></textarea>'
                f'<div class="count"><span>0</span> / {TEXT_MAX}</div>')
    else:
        long = any(len(o) > 14 for o in opts)
        body = (f'<div class="opts{" list" if long else ""}" role="group" aria-label="{e(title)}">'
                + "".join(f'<button type="button" class="opt" aria-pressed="false" data-v="{e(o)}">{e(o)}</button>' for o in opts)
                + "</div>")
    last = i == len(QUESTIONS)
    nxt = "Absenden" if last else "Weiter"
    return (f'<section class="step glass" data-key="{key}" data-kind="{kind}">{num}<h2>{e(title)}</h2>{hint_html}{body}'
            f'<div class="nav"><button type="button" class="btn ghost back">←</button>'
            f'<button type="button" class="btn next"{"" if kind == "text" else " disabled"}>{nxt}</button></div>'
            f'{"<div class=err></div>" if last else ""}</section>')


def page(cfg):
    connect = "https://script.google.com https://script.googleusercontent.com" if cfg["endpoint"] else "'none'"
    steps = "".join(_question(i, q) for i, q in enumerate(QUESTIONS, 1))
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Merch-Umfrage – Hinkowicz</title>{head_icons()}<meta name="color-scheme" content="dark light">
<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'self'; connect-src {connect}; base-uri 'none'; form-action 'none'">
<style>{BASE}{CSS}</style></head><body>
<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="pattern" aria-hidden="true"></div>
<main class="sv" id="sv" data-endpoint="{e(cfg['endpoint'])}">
<div class="top"><a href="/" aria-label="Startseite">{logo_html() or 'Hinkowicz'}</a></div>
<div class="bar" aria-hidden="true"><i></i></div>
<section class="step glass intro on" data-kind="intro"><div class="n">Merch · Umfrage</div>
<h1>Hilf mir bei meinem Merch!</h1>
<p>Bald gibt es Hinkowicz-Merch – und du entscheidest mit, wie er wird. {len(QUESTIONS)} kurze Fragen, dauert etwa eine Minute.</p>
<ul><li>Komplett anonym – kein Name, keine E-Mail</li><li>Einfach antippen, fertig</li></ul>
<div class="nav"><button type="button" class="btn next">Los geht's</button></div>
<noscript><p class="err">Bitte JavaScript aktivieren, um an der Umfrage teilzunehmen.</p></noscript></section>
{steps}
<label class="hp" aria-hidden="true">Bitte leer lassen <input name="website" tabindex="-1" autocomplete="off"></label>
<section class="step glass done" data-kind="done"><div class="big">🙌</div><h2>Danke dir!</h2>
<p class="hint">Deine Antworten sind angekommen. Halt die Augen offen – der Merch kommt bald.</p>
<div class="nav"><a class="btn" href="/">Zu hinkowicz.de</a></div></section>
<footer>Anonym · Antworten werden in einer Google-Tabelle von Hinkowicz gespeichert{legal_links()}</footer>
</main><script src="/assets/umfrage.js" defer></script></body></html>"""


def apps_script():
    """Google-Apps-Script, das nur bekannte Fragen/Antworten annimmt und in die Tabelle schreibt."""
    allowed = {k: opts for k, kind, _, _, opts in QUESTIONS if kind != "text"}
    multi = [k for k, kind, *_ in QUESTIONS if kind == "many"]
    texts = [k for k, kind, *_ in QUESTIONS if kind == "text"]
    return f"""/**
 * Hinkowicz Merch-Umfrage → Google-Tabelle
 * Automatisch erzeugt aus gh/survey.py – Fragen bitte dort ändern und neu erzeugen.
 * Einrichtung: siehe Anleitung im Chat (Erweiterungen → Apps Script → einfügen → Bereitstellen als Web-App).
 */
const KEYS = {json.dumps(KEYS, ensure_ascii=False)};
const ALLOWED = {json.dumps(allowed, ensure_ascii=False, indent=1)};
const MULTI = {json.dumps(multi)};
const TEXTS = {json.dumps(texts)};
const TEXT_MAX = {TEXT_MAX};
const MAX_PER_MINUTE = 60; // Schutz vor Spam-Fluten

function doPost(e) {{
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return reply('busy');
  try {{
    const cache = CacheService.getScriptCache();
    const n = Number(cache.get('n') || 0);
    if (n >= MAX_PER_MINUTE) return reply('busy');
    cache.put('n', String(n + 1), 60);

    const data = JSON.parse((e && e.postData && e.postData.contents) || '{{}}');
    if (data.website) return reply('ok'); // Bot-Falle: echtes Formular lässt das Feld leer
    if (!data.t || data.t < 8000) return reply('ok'); // in unter 8 Sekunden ausgefüllt = Bot
    const row = [new Date()];
    let answered = 0;
    for (const k of KEYS) {{
      let v = data[k];
      if (TEXTS.includes(k)) {{
        v = String(v || '').slice(0, TEXT_MAX).replace(/^[=+\\-@\\t\\r]+/, ''); // keine Tabellen-Formeln
      }} else {{
        const list = (Array.isArray(v) ? v : [v]).filter(x => ALLOWED[k].includes(x));
        v = (MULTI.includes(k) ? list : list.slice(0, 1)).join(', ');
      }}
      if (v) answered++;
      row.push(v);
    }}
    if (!answered) return reply('empty');
    sheet().appendRow(row);
    return reply('ok');
  }} catch (err) {{
    return reply('error');
  }} finally {{
    lock.releaseLock();
  }}
}}

function sheet() {{
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName('Antworten') || ss.insertSheet('Antworten');
  if (sh.getLastRow() === 0) {{
    sh.appendRow(['Zeitpunkt'].concat(KEYS));
    sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, KEYS.length + 1).setFontWeight('bold');
  }}
  return sh;
}}

function reply(status) {{
  return ContentService.createTextOutput(JSON.stringify({{ status: status }})).setMimeType(ContentService.MimeType.JSON);
}}

// Zum Testen im Editor: einmal ausführen, dann steht eine Testzeile in der Tabelle (danach löschen).
function test() {{
  const r = doPost({{ postData: {{ contents: JSON.stringify({{ t: 60000, produkte: ['Hoodie'], groesse: 'L', ideen: 'Test' }}) }} }});
  Logger.log(r.getContent());
}}
"""


def write(out_dir):
    cfg = load()
    if not cfg["slug"]:
        return None
    d = Path(out_dir) / "umfrage" / cfg["slug"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page(cfg), encoding="utf-8")
    return f"/umfrage/{cfg['slug']}/"


if __name__ == "__main__":
    Path("tools").mkdir(exist_ok=True)
    Path("tools/merch-umfrage.gs").write_text(apps_script(), encoding="utf-8")
    print("tools/merch-umfrage.gs geschrieben")
