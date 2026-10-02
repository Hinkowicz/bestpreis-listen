/* Hinko Links – kleine App zum Pflegen der Links auf hinkowicz.de.
 * Speichert direkt ins GitHub-Repository (ein Commit pro „Veröffentlichen“),
 * danach baut GitHub die Seite neu (ca. 1 Minute). Keine Fremddienste außer der GitHub-API. */
'use strict';

const REPO = 'Hinkowicz/bestpreis-listen';
const BRANCH = 'main';
const FILE = 'content/links.json';
const API = 'https://api.github.com';
const AUTHOR = { name: 'Hinkowicz', email: 'hinkowicz@users.noreply.github.com' };
const TOKEN_KEY = 'hinko.token';
const MAX_IMG = 800;

const S = {
  token: null, links: [], base: null, dirty: false,  // base = zuletzt geladener/gespeicherter Stand
  pending: {},   // Pfad -> Blob (neue Bilder, noch nicht hochgeladen)
  previews: {},  // Pfad -> blob:-URL für die Vorschau
  status: { kind: 'idle', text: 'Lädt …' },
};

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

async function loadLinks() {
  const f = await gh(`/repos/${REPO}/contents/${FILE}?ref=${BRANCH}`);
  const text = b64ToText(f.content);
  S.base = canon(text);
  S.links = (JSON.parse(text).links || []).map(l => ({
    title: l.title || '', description: l.description || '', url: l.url || '', image: l.image || null,
    ad: l.ad !== false, featured: l.featured === true, visible: l.visible !== false,
  }));
  S.dirty = false;
}

// Inhalt vergleichbar machen (unabhängig von Formatierung)
function canon(text) { try { return JSON.stringify(JSON.parse(text)); } catch { return text; } }

async function publish() {
  setStatus('busy', 'Speichert …');
  render();
  try {
    const head = (await gh(`/repos/${REPO}/git/ref/heads/${BRANCH}`)).object.sha;
    // Nur abbrechen, wenn jemand anderes die Links inhaltlich geändert hat (z. B. auf einem zweiten Gerät)
    const current = await gh(`/repos/${REPO}/contents/${FILE}?ref=${head}`);
    if (canon(b64ToText(current.content)) !== S.base) {
      setStatus('err', 'Konflikt');
      render();
      if (confirm('Die Links wurden inzwischen auf einem anderen Gerät geändert.\n\nOK = neu laden (deine ungespeicherten Änderungen hier gehen verloren)\nAbbrechen = nichts tun')) location.reload();
      return;
    }
    const baseTree = (await gh(`/repos/${REPO}/git/commits/${head}`)).tree.sha;
    const used = new Set(S.links.map(l => (l.image || '').replace(/^\//, '')));
    const entries = [];
    for (const [path, blob] of Object.entries(S.pending)) {
      if (!used.has(path)) continue;
      const b = await gh(`/repos/${REPO}/git/blobs`, { method: 'POST', body: JSON.stringify({ content: await blobToB64(blob), encoding: 'base64' }) });
      entries.push({ path, mode: '100644', type: 'blob', sha: b.sha });
    }
    const json = JSON.stringify({ links: S.links }, null, 2) + '\n';
    entries.push({ path: FILE, mode: '100644', type: 'blob', content: json });
    const tree = await gh(`/repos/${REPO}/git/trees`, { method: 'POST', body: JSON.stringify({ base_tree: baseTree, tree: entries }) });
    const when = new Date().toISOString();
    const commit = await gh(`/repos/${REPO}/git/commits`, {
      method: 'POST',
      body: JSON.stringify({ message: 'Links aktualisiert (Hinko-App)', tree: tree.sha, parents: [head],
        author: { ...AUTHOR, date: when }, committer: { ...AUTHOR, date: when } }),
    });
    await gh(`/repos/${REPO}/git/refs/heads/${BRANCH}`, { method: 'PATCH', body: JSON.stringify({ sha: commit.sha }) });
    S.base = canon(json);
    S.pending = {};
    S.dirty = false;
    setStatus('busy', 'Wird veröffentlicht …');
    render();
    toast('Gespeichert – in ca. 1 Minute live');
    waitForLive(commit.sha);
  } catch (e) {
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
  const path = `assets/links/${slug(title)}-${Date.now().toString(36)}.${ext}`;
  S.pending[path] = blob;
  S.previews[path] = URL.createObjectURL(blob);
  return '/' + path;
}

/* ---------- Ansichten ---------- */
function render() {
  if (!S.token) return renderLogin();
  const list = h('div', { class: 'list' });
  S.links.forEach((l, i) => list.append(itemView(l, i)));
  if (!S.links.length) list.append(h('div', { class: 'empty' }, 'Noch keine Links. Tippe auf +'));

  const dock = h('div', { class: 'dock' },
    S.dirty ? h('button', { class: 'cta glass', onclick: publish }, 'Veröffentlichen') : null,
    h('button', { class: 'fab', 'aria-label': 'Neuer Link', onclick: () => openSheet(-1) }, svg(ICON.plus, 26)));

  $app.replaceChildren(h('div', { class: 'screen' },
    h('div', { class: 'bar' }, h('h1', {}, 'Links'),
      h('div', { class: 'baracts' }, statusPill(),
        h('button', { class: 'iconbtn glass', 'aria-label': 'Menü', onclick: openMenu }, svg(ICON.more, 20, true)))),
    list), dock);
}

function itemView(l, i) {
  const thumb = h('div', { class: `thumb${l.image ? '' : ' mono'}` },
    h('img', { src: l.image ? imgSrc(l.image) : '/assets/monogram-white.png', alt: '' }));
  const badges = h('div', { class: 'badges' },
    l.featured ? h('span', { class: 'badge feat' }, 'Groß') : null,
    l.ad ? h('span', { class: 'badge ad' }, 'Anzeige') : null,
    l.image && S.pending[l.image.replace(/^\//, '')] ? h('span', { class: 'badge new' }, 'Neu') : null);
  const sw = h('label', { class: 'switch', onclick: e => e.stopPropagation() },
    h('input', { type: 'checkbox', checked: l.visible, 'aria-label': 'Sichtbar',
      onchange: e => { l.visible = e.target.checked; S.dirty = true; render(); } }), h('span'));
  const handle = h('div', { class: 'handle', 'aria-label': 'Verschieben' }, svg(ICON.grip, 20, true));
  const el = h('div', { class: `item glass${l.visible ? '' : ' hidden'}`, 'data-i': i, onclick: () => openSheet(i) },
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

function toggleRow(label, hint, checked, onchange) {
  return h('label', { class: 'toggle' }, h('span', {}, label, hint ? h('small', {}, hint) : null),
    h('span', { class: 'switch' }, h('input', { type: 'checkbox', checked, onchange: e => onchange(e.target.checked) }), h('span')));
}

function openSheet(i) {
  const isNew = i < 0;
  const d = isNew ? { title: '', description: '', url: '', image: null, ad: true, featured: false, visible: true } : { ...S.links[i] };
  const back = h('div', { class: 'backdrop', onclick: () => close() });
  const err = h('div', { class: 'err' });
  const title = h('input', { class: 'input', placeholder: 'z. B. Razer Viper V4 Pro', value: d.title, enterkeyhint: 'next' });
  const desc = h('input', { class: 'input', placeholder: 'optional, z. B. Code „Hinko“ für 10 %', value: d.description });
  const url = h('input', { class: 'input', type: 'url', inputmode: 'url', autocapitalize: 'off', autocorrect: 'off',
    placeholder: 'https://…', value: d.url });
  const paste = h('button', { class: 'btn', type: 'button', onclick: async () => {
    try { url.value = normalizeUrl(await navigator.clipboard.readText()); } catch { url.focus(); toast('Bitte lange tippen → Einsetzen'); }
  } }, 'Einfügen');
  const thumb = h('div', { class: 'thumb' });
  const paintThumb = () => thumb.replaceChildren(d.image ? h('img', { src: imgSrc(d.image), alt: '' }) : svg(ICON.image, 30));
  paintThumb();
  const file = h('input', { type: 'file', accept: 'image/*', class: 'hide', onchange: async e => {
    const f = e.target.files[0]; if (!f) return;
    try { d.image = await processImage(f, title.value || d.title); paintThumb(); }
    catch { toast('Bild konnte nicht gelesen werden'); }
  } });

  const sheet = h('div', { class: 'sheet glass', role: 'dialog', 'aria-modal': 'true' },
    h('div', { class: 'grabber' }),
    h('h2', {}, isNew ? 'Neuer Link' : 'Link bearbeiten',
      h('button', { class: 'iconbtn glass', 'aria-label': 'Schließen', onclick: () => close() }, svg(ICON.close, 18))),
    h('label', { class: 'field' }, h('span', {}, 'Titel'), title),
    h('label', { class: 'field' }, h('span', {}, 'Kurze Beschreibung'), desc),
    h('div', { class: 'field' }, h('span', {}, 'Link'), h('div', { class: 'row2' }, url, paste)),
    err,
    h('div', { class: 'field' }, h('span', {}, 'Bild'),
      h('div', { class: 'imgpick' }, thumb, h('div', { class: 'acts' },
        h('button', { class: 'btn', type: 'button', onclick: () => file.click() }, d.image ? 'Bild ändern' : 'Bild wählen'),
        h('button', { class: 'btn', type: 'button', onclick: () => { d.image = null; paintThumb(); } }, 'Entfernen'))), file),
    h('div', { class: 'toggles glass' },
      toggleRow('Als Werbung kennzeichnen', 'Bei Kooperationen & Affiliate-Links anlassen', d.ad, v => { d.ad = v; }),
      toggleRow('Groß hervorheben', 'Breite Karte mit großem Bild', d.featured, v => { d.featured = v; }),
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
    if (!d.title) { err.textContent = 'Bitte einen Titel eingeben.'; title.focus(); return; }
    if (!URL_OK(d.url)) { err.textContent = 'Bitte einen vollständigen Link mit https:// eingeben.'; url.focus(); return; }
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
    h('img', { src: '/app/icon-192.png', alt: '' }), h('h1', {}, 'Hinko Links'),
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
