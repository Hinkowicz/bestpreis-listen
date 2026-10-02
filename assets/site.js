/* Einzige Aufgabe: Rabattcodes per Tippen kopieren. Kein Tracking, keine Fremd-Skripte. */
document.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('.code');
  if (!btn) return;
  ev.preventDefault();
  const code = btn.dataset.code || '';
  let ok = false;
  try { await navigator.clipboard.writeText(code); ok = true; } catch (e) {
    const t = document.createElement('textarea');
    t.value = code; t.setAttribute('readonly', ''); t.style.position = 'fixed'; t.style.opacity = '0';
    document.body.appendChild(t); t.select();
    try { ok = document.execCommand('copy'); } catch (e2) { ok = false; }
    t.remove();
  }
  const lbl = btn.querySelector('.lbl');
  if (!lbl) return;
  const before = lbl.textContent;
  lbl.textContent = ok ? 'Kopiert ✓' : 'Code';
  btn.classList.toggle('ok', ok);
  setTimeout(() => { lbl.textContent = before; btn.classList.remove('ok'); }, 1600);
});
