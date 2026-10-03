/* Links – kleine App zum Pflegen der Links auf hinkowicz.de.
 * Speichert direkt ins GitHub-Repository (ein Commit pro „Veröffentlichen“),
 * danach baut GitHub die Seite neu (ca. 1 Minute). Keine Fremddienste außer der GitHub-API. */
'use strict';

const REPO = 'Hinkowicz/bestpreis-listen';
const BRANCH = 'main';
// Zwei Listen: Startseiten-Links und „Mein Setup“
const COLL = {
  links: { file: 'content/links.json', key: 'links', label: 'Links', img: 'assets/links' },
  setup: { file: 'content/setup.json', key: 'items', label: 'Setup', img: 'assets/setup' },
  amazon: { file: 'content/amazon-deals.json', key: 'items', label: 'Amazon', img: 'assets/amazon' },
};
const API = 'https://api.github.com';
const AUTHOR = { name: 'Hinkowicz', email: 'hinkowicz@users.noreply.github.com' };
const TOKEN_KEY = 'hinko.token';
const MAX_IMG = 1600; // genug Reserve zum Zoomen

const S = {
  token: null, tab: 'links', data: { links: [], setup: [], amazon: [] }, dirty: false,
  base: {},      // je Liste: Stand auf GitHub beim Laden/Speichern (erkennt Änderungen von anderen Geräten)
  saved: {},     // je Liste: eigener gespeicherter Stand (erkennt, ob hier überhaupt etwas geändert wurde)
  pending: {},   // Pfad -> Blob (neue Bilder, noch nicht hochgeladen)
  previews: {},  // Pfad -> blob:-URL für die Vorschau
  status: { kind: 'idle', text: 'Lädt …' },
};

Object.defineProperty(S, 'links', { get() { return S.data[S.tab]; }, set(v) { S.data[S.tab] = v; } });

/* ---------- kleine Helfer ---------- */
const $app = document.getElementById('app');

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'checked' || k === 'value') el[k] = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : String(kid));
  return el;
}

function svg(path, size = 22, fill = false) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('width', size); s.setAttribute('height', size);
  s.setAttribute('fill', fill ? 'currentColor' : 'none'); s.setAttribute('stroke', fill ? 'none' : 'currentColor');
  s.setAttribute('stroke-width', '2.2'); s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round');
  s.innerHTML = path; // nur feste Icon-Pfade aus diesem Code, nie Nutzereingaben
  return s;
}
const ICON = {
  plus: '<path d="M12 5v14M5 12h14"/>',
  grip: '<circle cx="9" cy="6" r="1.4"/><circle cx="15" cy="6" r="1.4"/><circle cx="9" cy="12" r="1.4"/><circle cx="15" cy="12" r="1.4"/><circle cx="9" cy="18" r="1.4"/><circle cx="15" cy="18" r="1.4"/>',
  more: '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  up: '<path d="M12 19V5M5 12l7-7 7 7"/>',
};

function toast(text, ms = 2600) {
  const t = h('div', { class: 'toast glass' }, text);
  document.body.append(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 500); }, ms);
}

function setStatus(kind, text) { S.status = { kind, text }; const p = document.querySelector('.bar .pill'); if (p) p.replaceWith(statusPill()); }

function statusPill() {
  if (S.dirty && S.status.kind !== 'busy' && S.status.kind !== 'err') return h('span', { class: 'pill glass warn' }, h('span', { class: 'dot' }), 'Entwurf');
  const cls = { live: '', busy: 'busy', warn: 'warn', err: 'err', idle: 'busy' }[S.status.kind] ?? '';
  return h('span', { class: `pill glass ${cls}` }, h('span', { class: 'dot' }), S.status.text);
}

function b64ToText(b64) {
  const bin = atob(b64.replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(bin, c => c.charCodeAt(0)));
}

function blobToB64(blob) {
  return new Promise((ok, fail) => {
    const r = new FileReader();
    r.onload = () => ok(String(r.result).split(',')[1]);
    r.onerror = fail;
    r.readAsDataURL(blob);
  });
}

function slug(s) {
  return (s || 'bild').toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 32) || 'bild';
}

function normalizeUrl(u) {
  u = (u || '').trim();
  if (!u) return '';
  if (!/^[a-z]+:\/\//i.test(u) && /^[\w-]+(\.[\w-]+)+/.test(u)) u = 'https://' + u;
  return u;
}
const URL_OK = u => /^https:\/\/[^\s<>"']+$/.test(u);
const AMAZON_OK = u => /^https:\/\/(www\.|smile\.|m\.)?(amazon\.de|amzn\.to|amzn\.eu)\//i.test(u);
/* ASIN aus einem Amazon-Link lesen; Kurzlinks (amzn.to) löst die Website beim Bauen auf */
function asinOf(u) {
  const m = /\/(?:dp|gp\/product|gp\/aw\/d|exec\/obidos\/asin)\/([A-Z0-9]{10})(?=[/?#]|$)/i.exec(u || '');
  return m ? m[1].toUpperCase() : '';
}

function imgSrc(path) { return path ? (S.previews[path.replace(/^\//, '')] || path) : null; }

/* ---------- GitHub ---------- */
async function gh(path, opts = {}) {
  const res = await fetch(API + path, {
    ...opts,
    headers: {
      Authorization: `Bearer ${S.token}`, Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28', ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    let msg = `GitHub ${res.status}`;
    try { msg += ': ' + (await res.json()).message; } catch { /* leer */ }
    const err = new Error(msg); err.status = res.status; throw err;
  }
  return res.status === 204 ? null : res.json();
}

function normalize(l, name) {
  const o = { title: l.title || '', description: l.description || '', url: l.url || '', image: l.image || null,
    focus: l.focus || '', zoom: Math.min(300, Math.max(100, +l.zoom || 100)), code: l.code || '', until: l.until || '', ad: l.ad !== false, visible: l.visible !== false };
  if (name === 'setup') o.category = l.category || 'Sonstiges'; else o.featured = l.featured === true;
  if (name === 'amazon') { o.asin = l.asin || ''; o.ad = true; }
  return o;
}

function serialize(name) {
  // leere optionale Felder weglassen, damit die Dateien übersichtlich bleiben
  const items = S.data[name].map(l => Object.fromEntries(Object.entries(l).filter(([k, v]) => !((['focus', 'code', 'until', 'asin'].includes(k) && !v) || (k === 'zoom' && v <= 100)))));
  return JSON.stringify({ [COLL[name].key]: items }, null, 2) + '\n';
}

async function loadLinks() {
  for (const [name, c] of Object.entries(COLL)) {
    let text = JSON.stringify({ [c.key]: [] });
    try { text = b64ToText((await gh(`/repos/${REPO}/contents/${c.file}?ref=${BRANCH}`)).content); }
    catch (e) { if (e.status !== 404) throw e; }
    S.base[name] = canon(text);
    S.data[name] = (JSON.parse(text)[c.key] || []).map(l => normalize(l, name));
    S.saved[name] = serialize(name);
  }
  S.dirty = false;
}

// Inhalt vergleichbar machen (unabhängig von Formatierung)
function canon(text) { try { return JSON.stringify(JSON.parse(text)); } catch { return text; } }

async function publish(retry = true) {
  setStatus('busy', 'Speichert …');
  render();
  try {
    const head = (await gh(`/repos/${REPO}/git/ref/heads/${BRANCH}`)).object.sha;
    // Nur abbrechen, wenn jemand anderes die Listen inhaltlich geändert hat (z. B. auf einem zweiten Gerät)
    let foreign = false;
    for (const [name, c] of Object.entries(COLL)) {
      let text = JSON.stringify({ [c.key]: [] });
      try { text = b64ToText((await gh(`/repos/${REPO}/contents/${c.file}?ref=${head}`)).content); }
      catch (e) { if (e.status !== 404) throw e; }
      if (canon(text) !== S.base[name]) foreign = true;
    }
    if (foreign) {
      setStatus('err', 'Konflikt');
      render();
      if (confirm('Die Links wurden inzwischen auf einem anderen Gerät geändert.\n\nOK = neu laden (deine ungespeicherten Änderungen hier gehen verloren)\nAbbrechen = nichts tun')) location.reload();
      return;
    }
    const baseTree = (await gh(`/repos/${REPO}/git/commits/${head}`)).tree.sha;
    const used = new Set([...S.data.links, ...S.data.setup, ...S.data.amazon].map(l => (l.image || '').replace(/^\//, '')));
    const entries = [];
    for (const [path, blob] of Object.entries(S.pending)) {
      if (!used.has(path)) continue;
      const b = await gh(`/repos/${REPO}/git/blobs`, { method: 'POST', body: JSON.stringify({ content: await blobToB64(blob), encoding: 'base64' }) });
      entries.push({ path, mode: '100644', type: 'blob', sha: b.sha });
    }
    const out = {};
    for (const [name, c] of Object.entries(COLL)) {
      out[name] = serialize(name);
      if (out[name] !== S.saved[name]) entries.push({ path: c.file, mode: '100644', type: 'blob', content: out[name] });
    }
    const tree = await gh(`/repos/${REPO}/git/trees`, { method: 'POST', body: JSON.stringify({ base_tree: baseTree, tree: entries }) });
    const when = new Date().toISOString();
    const commit = await gh(`/repos/${REPO}/git/commits`, {
      method: 'POST',
      body: JSON.stringify({ message: 'Links aktualisiert (Hinko-App)', tree: tree.sha, parents: [head],
        author: { ...AUTHOR, date: when }, committer: { ...AUTHOR, date: when } }),
    });
    await gh(`/repos/${REPO}/git/refs/heads/${BRANCH}`, { method: 'PATCH', body: JSON.stringify({ sha: commit.sha }) });
    for (const e of entries) {
      const name = Object.keys(COLL).find(n => COLL[n].file === e.path);
      if (name) { S.base[name] = canon(out[name]); S.saved[name] = out[name]; }
    }
    S.pending = {};
    S.dirty = false;
    setStatus('busy', 'Wird veröffentlicht …');
    render();
    toast('Gespeichert – in ca. 1 Minute live');
    waitForLive(commit.sha);
  } catch (e) {
    if (retry && (e.status === 422 || e.status === 409 || !e.status)) { await new Promise(r => setTimeout(r, 1500)); return publish(false); } // kurz danach nochmal
    setStatus('err', 'Fehler');
    render();
    alert('Speichern fehlgeschlagen.\n\n' + e.message +
      (e.status === 403 || e.status === 404 ? '\n\nHat dein Zugriffsschlüssel „Contents: Read and write“ für dieses Repository?' : ''));
  }
}

async function liveRev() {
  try { return (await (await fetch('/version.json?ts=' + Date.now(), { cache: 'no-store' })).json()).rev; }
  catch { return null; }
}

async function waitForLive(sha) {
  const before = await liveRev();
  const start = Date.now();
  const tick = async () => {
    const rev = await liveRev();
    if (rev === sha || (rev && before && rev !== before && Date.now() - start > 20000)) {
      setStatus('live', 'Live');
      toast('✓ Deine Änderungen sind live');
      return;
    }
    if (Date.now() - start > 6 * 60 * 1000) { setStatus('warn', 'Dauert länger …'); return; }
    setTimeout(tick, 5000);
  };
  setTimeout(tick, 15000);
}

/* ---------- Bilder ---------- */
async function processImage(file, title) {
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, MAX_IMG / Math.max(bmp.width, bmp.height));
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  let blob = await new Promise(r => c.toBlob(r, 'image/webp', 0.84));
  let ext = 'webp';
  if (!blob || blob.type !== 'image/webp') { blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.86)); ext = 'jpg'; }
  const path = `${COLL[S.tab].img}/${slug(title)}-${Date.now().toString(36)}.${ext}`;
  S.pending[path] = blob;
  S.previews[path] = URL.createObjectURL(blob);
  return '/' + path;
}

/* ---------- Ansichten ---------- */
function render() {
  if (!S.token) return renderLogin();
  const list = h('div', { class: 'list' });
  S.links.forEach((l, i) => list.append(itemView(l, i)));
  if (!S.links.length) list.append(h('div', { class: 'empty' }, 'Noch keine Einträge. Tippe auf +'));
  const seg = h('div', { class: 'seg glass' }, ...Object.entries(COLL).map(([name, c]) =>
    h('button', { class: name === S.tab ? 'on' : '', onclick: () => { S.tab = name; render(); window.scrollTo(0, 0); } }, c.label)));

  const dock = h('div', { class: 'dock' },
    S.dirty ? h('button', { class: 'cta glass', onclick: () => publish() }, 'Veröffentlichen') : null,
    h('button', { class: 'fab', 'aria-label': 'Neuer Link', onclick: () => openSheet(-1) }, svg(ICON.plus, 26)));

  $app.replaceChildren(h('div', { class: 'screen' },
    h('div', { class: 'bar' }, h('div', { class: 'brand' }, h('img', { src: '/assets/logo-dark.png', alt: 'Hinkowicz' }), h('h1', {}, COLL[S.tab].label)),
      h('div', { class: 'baracts' }, statusPill(),
        h('button', { class: 'iconbtn glass', 'aria-label': 'Menü', onclick: openMenu }, svg(ICON.more, 20, true)))),
    seg, list), dock);
}

function itemView(l, i) {
  const thumb = h('div', { class: `thumb${l.image ? '' : ' mono'}` },
    l.image ? focusImg(h('img', { src: imgSrc(l.image), alt: '' }), l) : h('img', { src: '/assets/monogram-white.png', alt: '' }));
  const badges = h('div', { class: 'badges' },
    l.featured ? h('span', { class: 'badge feat' }, 'Groß') : null,
    l.category && S.tab === 'setup' ? h('span', { class: 'badge' }, l.category) : null,
    l.code ? h('span', { class: 'badge code' }, 'Code ' + l.code) : null,
    l.until ? h('span', { class: `badge ${expired(l) ? 'exp' : 'until'}` }, expired(l) ? 'Abgelaufen' : 'bis ' + deDate(l.until)) : null,
    l.ad ? h('span', { class: 'badge ad' }, 'Anzeige') : null,
    l.image && S.pending[l.image.replace(/^\//, '')] ? h('span', { class: 'badge new' }, 'Neu') : null);
  const sw = h('label', { class: 'switch', onclick: e => e.stopPropagation() },
    h('input', { type: 'checkbox', checked: l.visible, 'aria-label': 'Sichtbar',
      onchange: e => { l.visible = e.target.checked; S.dirty = true; render(); } }), h('span'));
  const handle = h('div', { class: 'handle', 'aria-label': 'Verschieben' }, svg(ICON.grip, 20, true));
  const el = h('div', { class: `item glass${l.visible && !expired(l) ? '' : ' hidden'}`, 'data-i': i, onclick: () => openSheet(i) },
    thumb, h('div', { class: 'meta' }, h('div', { class: 't' }, l.title || '(ohne Titel)'),
      h('div', { class: 's' }, l.description || l.url), badges), sw, handle);
  handle.addEventListener('click', e => e.stopPropagation());
  handle.addEventListener('pointerdown', e => startDrag(e, el));
  return el;
}

/* Sortieren per Ziehen am Griff */
function startDrag(e, el) {
  e.preventDefault(); e.stopPropagation();
  const list = el.parentElement;
  let startY = e.clientY;
  el.classList.add('dragging');
  const move = ev => {
    let dy = ev.clientY - startY;
    const mid = el.getBoundingClientRect().top + el.offsetHeight / 2;
    const prev = el.previousElementSibling, next = el.nextElementSibling;
    const before = el.offsetTop;
    if (next && mid > next.getBoundingClientRect().top + next.offsetHeight / 2) list.insertBefore(next, el);
    else if (prev && mid < prev.getBoundingClientRect().top + prev.offsetHeight / 2) list.insertBefore(el, prev);
    startY += el.offsetTop - before;
    dy = ev.clientY - startY;
    el.style.transform = `translateY(${dy}px) scale(1.03)`;
    if (ev.clientY < 90) window.scrollBy(0, -10); else if (ev.clientY > innerHeight - 110) window.scrollBy(0, 10);
  };
  const up = () => {
    window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); window.removeEventListener('pointercancel', up);
    el.classList.remove('dragging'); el.style.transform = '';
    const order = [...list.querySelectorAll('.item')].map(x => S.links[+x.dataset.i]);
    if (order.some((l, i) => l !== S.links[i])) { S.links = order; S.dirty = true; }
    render();
  };
  window.addEventListener('pointermove', move); window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up);
}

function todayISO() {
  return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Berlin' }).format(new Date());  // YYYY-MM-DD
}
function expired(l) { return !!l.until && l.until < todayISO(); }
function deDate(iso) { const [y, m, d] = iso.split('-'); return `${d}.${m}.${y.slice(2)}`; }

function toggleRow(label, hint, checked, onchange) {
  return h('label', { class: 'toggle' }, h('span', {}, label, hint ? h('small', {}, hint) : null),
    h('span', { class: 'switch' }, h('input', { type: 'checkbox', checked, onchange: e => onchange(e.target.checked) }), h('span')));
}

/* Bildausschnitt: Fokuspunkt „x y“ in Prozent (wie CSS object-position), leer = Mitte */
function parseFocus(f) {
  const m = /^(\d{1,3}) (\d{1,3})$/.exec(f || '');
  return m ? [Math.min(+m[1], 100), Math.min(+m[2], 100)] : [50, 50];
}
function focusImg(img, d) {
  const [x, y] = parseFocus(d.focus), z = (d.zoom || 100) / 100;
  // CSSOM statt style-Attribut (CSP); gleiche Darstellung wie auf der Website
  img.style.objectPosition = img.style.transformOrigin = `${x}% ${y}%`;
  img.style.transform = z > 1 ? `scale(${z})` : '';
  return img;
}

/* Vorschau wie auf der Website (groß Handy 16:8, groß PC 16:6, klein quadratisch); Bild mit dem Finger verschieben */
function cropView(d, setup) {
  const frames = [];
  const frame = (cls, label) => {
    const img = focusImg(h('img', { src: imgSrc(d.image), alt: '', draggable: 'false' }), d);
    const f = h('div', { class: `frame ${cls}` }, img);
    frames.push(img);
    f.addEventListener('pointerdown', e => drag(e, f, img));
    return h('div', { class: `framebox ${cls}` }, f, h('small', {}, label));
  };
  const apply = () => frames.forEach(img => focusImg(img, d));
  function drag(e, f, img) {
    e.preventDefault();
    f.setPointerCapture(e.pointerId);
    let [x, y] = parseFocus(d.focus), lx = e.clientX, ly = e.clientY;
    const move = ev => {
      const fw = f.clientWidth, fh = f.clientHeight, nw = img.naturalWidth || 1, nh = img.naturalHeight || 1;
      // verschiebbarer Weg = gezoomte Bildgröße minus Rahmen
      const sc = Math.max(fw / nw, fh / nh) * (d.zoom || 100) / 100, ox = nw * sc - fw, oy = nh * sc - fh;
      // Bild folgt dem Finger: nach rechts ziehen zeigt mehr vom linken Rand
      if (ox > 1) x = Math.min(100, Math.max(0, x - (ev.clientX - lx) / ox * 100));
      if (oy > 1) y = Math.min(100, Math.max(0, y - (ev.clientY - ly) / oy * 100));
      lx = ev.clientX; ly = ev.clientY;
      d.focus = Math.round(x) === 50 && Math.round(y) === 50 ? '' : `${Math.round(x)} ${Math.round(y)}`;
      apply();
    };
    const up = () => { f.removeEventListener('pointermove', move); f.removeEventListener('pointerup', up); f.removeEventListener('pointercancel', up); };
    f.addEventListener('pointermove', move); f.addEventListener('pointerup', up); f.addEventListener('pointercancel', up);
  }
  const zoomLbl = h('b', {}, '');
  const zoom = h('input', { class: 'zoom', type: 'range', min: 100, max: 300, step: 5, value: d.zoom || 100, 'aria-label': 'Zoom',
    oninput: e => { d.zoom = +e.target.value; paintZoom(); apply(); } });
  const paintZoom = () => { zoomLbl.textContent = `${((d.zoom || 100) / 100).toFixed(1).replace('.', ',')}×`; };
  paintZoom();
  const reset = h('button', { class: 'btn small', type: 'button', onclick: () => {
    d.focus = ''; d.zoom = 100; zoom.value = 100; paintZoom(); apply(); } }, 'Zurücksetzen');
  const controls = [h('div', { class: 'zoomrow' }, svg(ICON.image, 16), zoom, zoomLbl),
    h('div', { class: 'crophint' }, setup ? 'Bild verschieben und zoomen.' : 'Bild mit dem Finger verschieben, mit dem Regler zoomen – so erscheint es auf der Website.', reset)];
  if (setup) return [h('div', { class: 'frames' }, frame('sq', 'Kachel')), ...controls];
  return [frame('wide', 'Groß · Handy'),
    h('div', { class: 'frames' }, frame('wider', 'Groß · PC'), frame('sq', 'Klein')), ...controls];
}

function openSheet(i) {
  const isNew = i < 0;
  const setup = S.tab === 'setup';
  const amz = S.tab === 'amazon';
  const blank = { title: '', description: '', url: '', image: null, focus: '', zoom: 100, code: '', until: '', ad: true, visible: true };
  if (setup) blank.category = S.links[0]?.category || ''; else blank.featured = false;
  const d = isNew ? blank : { ...S.links[i] };
  const cats = [...new Set(S.data.setup.map(x => x.category).filter(Boolean))];
  const back = h('div', { class: 'backdrop', onclick: () => close() });
  const err = h('div', { class: 'err' });
  const title = h('input', { class: 'input', placeholder: 'z. B. Razer Viper V4 Pro', value: d.title, enterkeyhint: 'next' });
  const desc = h('input', { class: 'input', placeholder: 'optional, z. B. Code „Hinko“ für 10 %', value: d.description });
  const url = h('input', { class: 'input', type: 'url', inputmode: 'url', autocapitalize: 'off', autocorrect: 'off',
    placeholder: amz ? 'Amazon-Link (amazon.de oder amzn.to)' : 'https://…', value: d.url });
  const paste = h('button', { class: 'btn', type: 'button', onclick: async () => {
    try { url.value = normalizeUrl(await navigator.clipboard.readText()); } catch { url.focus(); toast('Bitte lange tippen → Einsetzen'); }
  } }, 'Einfügen');
  const code = h('input', { class: 'input', placeholder: 'optional, z. B. HINKO10', value: d.code, autocapitalize: 'characters', autocorrect: 'off' });
  const until = h('input', { class: 'input', type: 'date', value: d.until, min: todayISO() });
  const clearUntil = h('button', { class: 'btn', type: 'button', onclick: () => { until.value = ''; } }, 'Ohne');
  const catList = h('datalist', { id: 'cats' }, ...cats.map(c => h('option', { value: c })));
  const category = h('input', { class: 'input', list: 'cats', placeholder: 'z. B. Peripherie & Controller', value: d.category || '' });
  const crop = h('div', { class: 'crop' });
  const pickBtn = h('button', { class: 'btn', type: 'button', onclick: () => file.click() });
  const paintThumb = () => {
    pickBtn.textContent = d.image ? 'Bild ändern' : 'Bild wählen';
    crop.replaceChildren(...(d.image ? cropView(d, setup) : [h('div', { class: 'thumb' }, svg(ICON.image, 30))]));
  };
  paintThumb();
  const file = h('input', { type: 'file', accept: 'image/*', class: 'hide', onchange: async e => {
    const f = e.target.files[0]; if (!f) return;
    try { d.image = await processImage(f, title.value || d.title); d.focus = ''; d.zoom = 100; paintThumb(); }
    catch { toast('Bild konnte nicht gelesen werden'); }
  } });

  const sheet = h('div', { class: 'sheet glass', role: 'dialog', 'aria-modal': 'true' },
    h('div', { class: 'grabber' }),
    h('h2', {}, isNew ? (setup ? 'Neues Produkt' : amz ? 'Neuer Amazon-Deal' : 'Neuer Link') : 'Bearbeiten',
      h('button', { class: 'iconbtn glass', 'aria-label': 'Schließen', onclick: () => close() }, svg(ICON.close, 18))),
    h('label', { class: 'field' }, h('span', {}, 'Titel'), title),
    h('label', { class: 'field' }, h('span', {}, 'Kurze Beschreibung'), desc),
    h('div', { class: 'field' }, h('span', {}, 'Link'), h('div', { class: 'row2' }, url, paste)),
    amz ? h('p', { class: 'note' }, 'Öffnet bei deinen Zuschauern die Amazon-App – dein Partner-Tag hinkowicz-21 wird automatisch angehängt.') : null,
    err,
    setup ? h('label', { class: 'field' }, h('span', {}, 'Kategorie'), category, catList) : null,
    amz ? null : h('label', { class: 'field' }, h('span', {}, 'Rabattcode'), code),
    h('div', { class: 'field' }, h('span', {}, 'Sichtbar bis (optional)'), h('div', { class: 'row2' }, until, clearUntil)),
    h('div', { class: 'field' }, h('span', {}, 'Bild'),
      crop, h('div', { class: 'acts2' }, pickBtn,
        h('button', { class: 'btn', type: 'button', onclick: () => { d.image = null; d.focus = ''; d.zoom = 100; paintThumb(); } }, 'Entfernen')), file),
    h('div', { class: 'toggles glass' },
      amz ? null : toggleRow('Als Werbung kennzeichnen', 'Bei Kooperationen & Affiliate-Links anlassen', d.ad, v => { d.ad = v; }),
      setup ? null : toggleRow('Groß hervorheben', 'Breite Karte mit großem Bild', d.featured, v => { d.featured = v; }),
      toggleRow('Sichtbar', null, d.visible, v => { d.visible = v; })),
    h('button', { class: 'btn primary wide', onclick: save }, isNew ? 'Hinzufügen' : 'Übernehmen'),
    isNew ? null : h('div', { class: 'acts2' },
      h('button', { class: 'btn', onclick: () => { const [x] = S.links.splice(i, 1); S.links.unshift(x); S.dirty = true; close(); } },
        svg(ICON.up, 16), ' Ganz nach oben'),
      h('button', { class: 'btn danger', onclick: () => {
        if (confirm(`„${d.title}“ wirklich löschen?`)) { S.links.splice(i, 1); S.dirty = true; close(); }
      } }, 'Löschen')));

  function save() {
    d.title = title.value.trim(); d.description = desc.value.trim(); d.url = normalizeUrl(url.value);
    d.code = code.value.trim().replace(/\s+/g, ' ').slice(0, 40); d.until = until.value || '';
    if (setup) d.category = category.value.trim() || 'Sonstiges';
    if (!d.title) { err.textContent = 'Bitte einen Titel eingeben.'; title.focus(); return; }
    if (!URL_OK(d.url)) { err.textContent = 'Bitte einen vollständigen Link mit https:// eingeben.'; url.focus(); return; }
    if (amz) {
      if (!AMAZON_OK(d.url)) { err.textContent = 'Bitte einen Link von amazon.de oder amzn.to einfügen.'; url.focus(); return; }
      d.asin = asinOf(d.url); d.ad = true; d.code = '';
    }
    if (isNew) S.links.unshift(d); else S.links[i] = d;
    S.dirty = true;
    close();
  }
  function close() {
    back.classList.remove('show'); sheet.classList.remove('show');
    setTimeout(() => { back.remove(); sheet.remove(); render(); }, 380);
  }
  document.body.append(back, sheet);
  requestAnimationFrame(() => { back.classList.add('show'); sheet.classList.add('show'); });
}

function openMenu(e) {
  e.stopPropagation();
  const m = h('div', { class: 'menu glass' },
    h('a', { href: '/', target: '_blank', rel: 'noopener' }, 'Website ansehen'),
    h('button', { onclick: () => location.reload() }, 'Neu laden'),
    h('button', { onclick: () => { if (confirm('Abmelden? Der Zugriffsschlüssel wird von diesem Gerät gelöscht.')) {
      localStorage.removeItem(TOKEN_KEY); S.token = null; render(); } } }, 'Abmelden'));
  document.body.append(m);
  setTimeout(() => document.addEventListener('click', () => m.remove(), { once: true }));
}

function renderLogin() {
  const inp = h('input', { class: 'input', type: 'password', placeholder: 'github_pat_…', autocapitalize: 'off', autocorrect: 'off' });
  const err = h('div', { class: 'err' });
  const go = async () => {
    const t = inp.value.trim();
    if (!t) return;
    S.token = t;
    try {
      await gh(`/repos/${REPO}`);
      await loadLinks();
      localStorage.setItem(TOKEN_KEY, t);
      setStatus('live', 'Live');
      render();
    } catch (e) {
      S.token = null;
      err.textContent = e.status === 401 ? 'Schlüssel ungültig oder abgelaufen.' : 'Anmeldung fehlgeschlagen: ' + e.message;
    }
  };
  $app.replaceChildren(h('div', { class: 'login' }, h('div', { class: 'card glass' },
    h('img', { src: '/app/icon-192.png', alt: '' }), h('h1', {}, 'Links'),
    h('p', {}, 'Melde dich einmalig mit deinem GitHub-Zugriffsschlüssel an. Er bleibt nur auf diesem Gerät gespeichert.'),
    h('label', { class: 'field' }, inp), err,
    h('button', { class: 'btn primary wide', onclick: go }, 'Anmelden'))));
}

/* ---------- Start ---------- */
window.addEventListener('beforeunload', e => { if (S.dirty) { e.preventDefault(); e.returnValue = ''; } });

(async function init() {
  S.token = localStorage.getItem(TOKEN_KEY);
  if (!S.token) return render();
  render();
  try {
    await loadLinks();
    setStatus('live', 'Live');
  } catch (e) {
    if (e.status === 401) { localStorage.removeItem(TOKEN_KEY); S.token = null; }
    else setStatus('err', 'Offline?');
  }
  render();
})();
