/* Merch-Umfrage: eine Frage pro Schritt, Antworten gehen anonym an das Google-Apps-Script. Kein Tracking. */
(function () {
  const root = document.getElementById('sv');
  if (!root) return;
  const endpoint = root.dataset.endpoint || '';
  const steps = [...root.querySelectorAll('.step')];
  const questions = steps.filter(s => s.dataset.key);
  const bar = root.querySelector('.bar i');
  const DONE_KEY = 'hinko-merch-umfrage';
  const started = Date.now();
  let idx = 0;

  const store = {
    get() { try { return localStorage.getItem(DONE_KEY); } catch (e) { return null; } },
    set() { try { localStorage.setItem(DONE_KEY, '1'); } catch (e) { /* privater Modus */ } },
  };

  function show(i) {
    steps[idx].classList.remove('on');
    idx = Math.max(0, Math.min(i, steps.length - 1));
    steps[idx].classList.add('on');
    const qi = questions.indexOf(steps[idx]);
    const progress = steps[idx].dataset.kind === 'done' ? 1 : qi < 0 ? 0 : qi / questions.length;
    bar.style.width = (progress * 100) + '%';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const t = steps[idx].querySelector('textarea');
    if (t) setTimeout(() => t.focus({ preventScroll: true }), 350);
  }

  function value(step) {
    if (step.dataset.kind === 'text') return step.querySelector('textarea').value.trim();
    const picked = [...step.querySelectorAll('.opt[aria-pressed="true"]')].map(b => b.dataset.v);
    return step.dataset.kind === 'many' ? picked : (picked[0] || '');
  }

  function refresh(step) {
    const next = step.querySelector('.next');
    if (step.dataset.kind !== 'text') next.disabled = value(step).length === 0;
  }

  root.addEventListener('click', ev => {
    const step = ev.target.closest('.step');
    if (!step) return;
    const opt = ev.target.closest('.opt');
    if (opt) {
      if (step.dataset.kind === 'one') {
        step.querySelectorAll('.opt').forEach(b => b.setAttribute('aria-pressed', String(b === opt)));
        refresh(step); // weiter geht es erst mit „Weiter“
      } else {
        opt.setAttribute('aria-pressed', String(opt.getAttribute('aria-pressed') !== 'true'));
        refresh(step);
      }
      return;
    }
    if (ev.target.closest('.back')) return show(idx - 1);
    if (ev.target.closest('.next')) {
      if (step === questions[questions.length - 1]) return submit(step);
      show(idx + 1);
    }
  });

  root.addEventListener('input', ev => {
    if (ev.target.matches('textarea')) {
      const c = ev.target.closest('.step').querySelector('.count span');
      if (c) c.textContent = ev.target.value.length;
    }
  });

  async function submit(step) {
    const btn = step.querySelector('.next');
    const err = step.querySelector('.err');
    const data = { t: Date.now() - started, website: (root.querySelector('.hp input') || {}).value || '' };
    questions.forEach(q => { data[q.dataset.key] = value(q); });
    const done = steps[steps.length - 1];
    if (!endpoint) { // Vorschau, solange die Google-Tabelle noch nicht verbunden ist
      done.querySelector('.hint').textContent = 'Vorschau – die Umfrage ist noch nicht mit der Tabelle verbunden, es wurde nichts gespeichert.';
      return show(steps.length - 1);
    }
    btn.disabled = true; btn.textContent = 'Wird gesendet …'; err.textContent = '';
    try {
      // text/plain + no-cors: keine Vorab-Anfrage nötig, Google leitet intern weiter
      await fetch(endpoint, { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(data) });
      store.set();
      show(steps.length - 1);
    } catch (e) {
      err.textContent = 'Senden hat nicht geklappt – bitte prüf deine Verbindung und versuch es nochmal.';
      btn.disabled = false; btn.textContent = 'Absenden';
    }
  }

  if (store.get()) {
    const done = steps[steps.length - 1];
    done.querySelector('h2').textContent = 'Du hast schon mitgemacht!';
    done.querySelector('.hint').textContent = 'Danke dir – deine Antworten sind angekommen.';
    show(steps.length - 1);
  }
})();
