/**
 * Hinkowicz Merch-Umfrage → Google-Tabelle
 * Automatisch erzeugt aus gh/survey.py – Fragen bitte dort ändern und neu erzeugen.
 * Einrichtung: siehe Anleitung im Chat (Erweiterungen → Apps Script → einfügen → Bereitstellen als Web-App).
 */
const KEYS = ["produkte", "schnitt", "groesse", "fit", "stoff", "material", "farben", "design", "position", "veredelung", "preis_shirt", "preis_hoodie", "drop", "plattform", "ideen"];
const ALLOWED = {
 "produkte": [
  "T-Shirt",
  "Hoodie",
  "Zip-Hoodie",
  "Sweatshirt",
  "Jogginghose",
  "Shorts",
  "Cap",
  "Beanie",
  "Mauspad",
  "Sticker",
  "Tasse",
  "Tote Bag"
 ],
 "schnitt": [
  "Unisex",
  "Herren",
  "Damen"
 ],
 "groesse": [
  "XS",
  "S",
  "M",
  "L",
  "XL",
  "XXL",
  "3XL",
  "4XL"
 ],
 "fit": [
  "Oversized – schön weit",
  "Regular – ganz normal",
  "Slim – eher eng"
 ],
 "stoff": [
  "Heavyweight – dick & robust",
  "Mittel – klassisch",
  "Leicht – dünn & luftig"
 ],
 "material": [
  "Bio-Baumwolle",
  "Recycelt",
  "Extra weich",
  "Formstabil nach dem Waschen",
  "Hauptsache günstig",
  "Egal"
 ],
 "farben": [
  "Schwarz",
  "Weiß",
  "Grau",
  "Creme / Off-White",
  "Navy",
  "Cyan",
  "Magenta",
  "Pastell",
  "Bunt"
 ],
 "design": [
  "Minimal – kleines Logo",
  "Großer Print auf dem Rücken",
  "Hinkowicz-Muster (All-over)",
  "Nur das Monogramm",
  "Schriftzug „Hinkowicz“",
  "Gaming- / Tech-Motive",
  "Insider aus den Videos"
 ],
 "position": [
  "Brust links",
  "Brust mittig",
  "Rücken",
  "Ärmel",
  "Nacken"
 ],
 "veredelung": [
  "Gestickt",
  "Gedruckt",
  "Egal"
 ],
 "preis_shirt": [
  "Bis 20 €",
  "20–30 €",
  "30–40 €",
  "Über 40 €"
 ],
 "preis_hoodie": [
  "Bis 45 €",
  "45–60 €",
  "60–75 €",
  "Über 75 €"
 ],
 "drop": [
  "Limitiert – macht es besonders",
  "Immer erhältlich",
  "Egal"
 ],
 "plattform": [
  "TikTok",
  "YouTube",
  "Instagram",
  "Twitch",
  "Discord"
 ]
};
const MULTI = ["produkte", "material", "farben", "design", "position"];
const TEXTS = ["ideen"];
const TEXT_MAX = 500;
const MAX_PER_MINUTE = 60; // Schutz vor Spam-Fluten

function doPost(e) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return reply('busy');
  try {
    const cache = CacheService.getScriptCache();
    const n = Number(cache.get('n') || 0);
    if (n >= MAX_PER_MINUTE) return reply('busy');
    cache.put('n', String(n + 1), 60);

    const data = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (data.website) return reply('ok'); // Bot-Falle: echtes Formular lässt das Feld leer
    if (!data.t || data.t < 8000) return reply('ok'); // in unter 8 Sekunden ausgefüllt = Bot
    const row = [new Date()];
    let answered = 0;
    for (const k of KEYS) {
      let v = data[k];
      if (TEXTS.includes(k)) {
        v = String(v || '').slice(0, TEXT_MAX).replace(/^[=+\-@\t\r]+/, ''); // keine Tabellen-Formeln
      } else {
        const list = (Array.isArray(v) ? v : [v]).filter(x => ALLOWED[k].includes(x));
        v = (MULTI.includes(k) ? list : list.slice(0, 1)).join(', ');
      }
      if (v) answered++;
      row.push(v);
    }
    if (!answered) return reply('empty');
    sheet().appendRow(row);
    return reply('ok');
  } catch (err) {
    return reply('error');
  } finally {
    lock.releaseLock();
  }
}

function sheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName('Antworten') || ss.insertSheet('Antworten');
  if (sh.getLastRow() === 0) {
    sh.appendRow(['Zeitpunkt'].concat(KEYS));
    sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, KEYS.length + 1).setFontWeight('bold');
  }
  return sh;
}

function reply(status) {
  return ContentService.createTextOutput(JSON.stringify({ status: status })).setMimeType(ContentService.MimeType.JSON);
}

// Zum Testen im Editor: einmal ausführen, dann steht eine Testzeile in der Tabelle (danach löschen).
function test() {
  const r = doPost({ postData: { contents: JSON.stringify({ t: 60000, produkte: ['Hoodie'], groesse: 'L', ideen: 'Test' }) } });
  Logger.log(r.getContent());
}
