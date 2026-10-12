/* DocCompare — tryb prezentacji z lektorem (włączany przez ?demo=1).
 *
 * Nie zmienia logiki aplikacji: strony scenariusza pokazuje w ramce iframe
 * (ta sama domena, bez ?demo=1), a lektor gra w oknie nadrzędnym, więc
 * przejście między stronami nie przerywa nagrania. Jedno nagranie naraz:
 * każda zmiana kroku najpierw zatrzymuje bieżące audio / syntezę.
 * Brak MP3 w manifeście → speechSynthesis (pl-PL) + ostrzeżenie w konsoli.
 */
(function () {
  'use strict';
  if (window.top !== window.self) return;          // nie uruchamiaj w ramce

  var BASE = '/static/demo/';
  var PAUSE_MS = 500;
  var HL = 'dc-demo-hl';

  var steps = [], manifest = {};
  var idx = 0, playing = false, token = 0, cur = null;
  var frameUrl = null, volume = 1, muted = false;
  var audio = new Audio(), nextAudio = new Audio();
  audio.preload = nextAudio.preload = 'auto';
  var ui = {};

  function h(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  }

  function getJSON(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error(url + ' → ' + r.status);
      return r.json();
    });
  }

  // ── Strony i podświetlenie ─────────────────────────────────────────────
  function pageFor(i) {                            // ostatni url na lub przed krokiem i
    for (var j = i; j >= 0; j--) if (steps[j].url) return steps[j].url;
    return '/home';
  }

  function frameDoc() {
    try { return ui.frame.contentDocument; } catch (e) { return null; }
  }

  function load(url) {
    return new Promise(function (resolve) {
      ui.frame.onload = function () {
        ui.frame.onload = null;
        var d = frameDoc();
        if (d && !d.getElementById('dc-demo-style')) {
          var st = d.createElement('style');
          st.id = 'dc-demo-style';
          st.textContent = '.' + HL + '{outline:3px solid #f59e0b!important;outline-offset:4px;' +
            'border-radius:10px;box-shadow:0 0 0 6px rgba(245,158,11,.25)!important;transition:outline-color .3s}';
          d.head.appendChild(st);
        }
        frameUrl = url;
        setTimeout(resolve, 400);                  // Alpine/JS strony dorysowuje widok
      };
      ui.frame.src = url;
    });
  }

  function highlight(selector) {
    var d = frameDoc();
    if (!d) return null;
    var old = d.querySelectorAll('.' + HL);
    for (var i = 0; i < old.length; i++) old[i].classList.remove(HL);
    if (!selector) return null;
    var t = d.querySelector(selector);
    if (!t) { console.warn('[demo] nie znaleziono elementu: ' + selector); return null; }
    t.classList.add(HL);
    var tall = t.getBoundingClientRect().height > ui.frame.clientHeight * 0.6;   // duży blok: pokaż jego początek
    t.scrollIntoView({ block: tall ? 'start' : 'center', behavior: 'smooth' });
    return t;
  }

  function act(i, fresh) {
    var s = steps[i], url = pageFor(i);
    var p = (fresh || frameUrl !== url) ? load(url) : Promise.resolve();
    return p.then(function () {
      var t = highlight(s.selector);
      if (t && s.action === 'click') t.click();
    });
  }

  // ── Lektor: jedno nagranie naraz ───────────────────────────────────────
  function stopVoice() {
    cur = null;
    audio.onended = audio.onerror = null;
    audio.pause();
    if (window.speechSynthesis) { speechSynthesis.cancel(); speechSynthesis.resume(); }  // Chrome pamięta pauzę po cancel
  }

  function speak(i) {
    return new Promise(function (resolve) {
      var s = steps[i], file = manifest[s.id];
      var c = { step: s, kind: file ? 'audio' : 'tts', started: false, done: false, resolve: resolve };
      cur = c;
      if (file) {
        audio.src = BASE + 'audio/' + file;
        audio.onended = function () { finish(c); };
        audio.onerror = function () {
          console.warn('[demo] nie można odtworzyć ' + file + ' — czytam przez speechSynthesis');
          c.kind = 'tts'; c.started = false;
          if (playing && cur === c) start();
        };
      } else {
        console.warn('[demo] brak nagrania dla ' + s.id + ' — czytam przez speechSynthesis');
      }
      preload(i + 1);
      if (playing) start();
    });
  }

  function finish(c) {
    if (c.done) return;
    c.done = true;
    c.resolve();
  }

  function start() {                               // start albo wznowienie bieżącego klipu
    var c = cur;
    if (!c || c.done) return;
    if (c.kind === 'audio') {
      c.started = true;
      audio.muted = muted; audio.volume = volume;
      audio.play().catch(function (e) { console.warn('[demo] odtwarzanie zablokowane: ' + e.message); });
      return;
    }
    if (!window.speechSynthesis) {                 // brak syntezy — odczekaj czas czytania
      c.started = true;
      setTimeout(function () { if (cur === c) finish(c); }, 60 * c.step.text.length);
      return;
    }
    if (c.started) { speechSynthesis.resume(); return; }
    c.started = true;
    var u = new SpeechSynthesisUtterance(c.step.text);
    u.lang = 'pl-PL';
    u.volume = muted ? 0 : volume;
    var pl = speechSynthesis.getVoices().filter(function (v) { return /^pl/i.test(v.lang); })[0];
    if (pl) u.voice = pl;
    u.onend = function () { if (cur === c) finish(c); };
    speechSynthesis.speak(u);
  }

  function holdVoice() {
    if (!cur) return;
    if (cur.kind === 'audio') audio.pause();
    else if (window.speechSynthesis) speechSynthesis.pause();
  }

  function preload(i) {
    var s = steps[i];
    if (s && manifest[s.id]) nextAudio.src = BASE + 'audio/' + manifest[s.id];
  }

  // ── Przebieg ───────────────────────────────────────────────────────────
  function go(i, fresh) {
    stopVoice();
    var my = ++token;
    if (i >= steps.length) { done(); return; }
    idx = i;
    render();
    act(i, fresh)
      .then(function () { return my === token ? speak(i) : null; })
      .then(function () {
        if (my !== token) return;
        cur = null;
        waitThenNext(my);
      });
  }

  function waitThenNext(my) {
    setTimeout(function () {
      if (my !== token) return;
      if (playing) go(idx + 1);
      else ui.pendingNext = true;                  // pauza w przerwie — ruszy po wznowieniu
    }, PAUSE_MS);
  }

  function done() {
    playing = false;
    highlight(null);
    idx = steps.length;
    ui.subs.textContent = 'Koniec prezentacji. Dziękuję.';
    render();
  }

  function toggle() {
    if (idx >= steps.length) { playing = true; go(0, true); return; }
    playing = !playing;
    if (playing) {
      if (ui.pendingNext) { ui.pendingNext = false; go(idx + 1); }
      else start();
    } else holdVoice();
    render();
  }

  function jump(delta) {
    ui.pendingNext = false;
    var i = Math.max(0, Math.min(steps.length - 1, idx + delta));
    go(i, delta < 0);                              // wstecz = świeże wczytanie strony
  }

  function setMuted(m) {
    muted = m;
    audio.muted = m;
    render();
  }

  // ── Interfejs ──────────────────────────────────────────────────────────
  function render() {
    var n = steps.length, end = idx >= n;
    ui.play.textContent = playing ? '⏸' : '▶';
    ui.play.setAttribute('aria-label', playing ? 'Pauza' : 'Odtwórz');
    ui.mute.textContent = muted ? '🔇' : '🔊';
    ui.mute.setAttribute('aria-pressed', String(muted));
    ui.prev.disabled = idx <= 0;
    ui.next.disabled = end || idx >= n - 1;
    ui.count.textContent = (end ? n : idx + 1) + ' / ' + n;
    if (!end) ui.subs.textContent = steps[idx].text;
    progress();
  }

  function progress() {
    var n = steps.length || 1, frac = 0;
    if (idx >= n) frac = 0;
    else if (cur && cur.kind === 'audio' && audio.duration) frac = audio.currentTime / audio.duration;
    ui.bar.style.width = (Math.min(n, idx + frac) / n * 100).toFixed(2) + '%';
  }

  function close() {
    token++;
    playing = false;
    stopVoice();
    ui.root.remove();
    document.documentElement.classList.remove('dc-demo-open');
    ui.startBtn.hidden = false;
  }

  function build() {
    var root = h('div', { 'class': 'dc-demo', role: 'region', 'aria-label': 'Prezentacja z lektorem' });
    var frame = h('iframe', { 'class': 'dc-demo-frame', title: 'Prezentowana strona' });
    var subs = h('div', { 'class': 'dc-demo-subs', 'aria-live': 'polite' });
    var panel = h('div', { 'class': 'dc-demo-panel' });
    var track = h('div', { 'class': 'dc-demo-track' });
    var bar = h('div', { 'class': 'dc-demo-bar' });
    track.appendChild(bar);

    function btn(label, text, fn) {
      var b = h('button', { type: 'button', 'class': 'dc-demo-btn', 'aria-label': label, title: label }, text);
      b.addEventListener('click', fn);
      return b;
    }
    var prev = btn('Poprzedni krok', '⏮', function () { jump(-1); });
    var play = btn('Pauza', '⏸', toggle);
    var next = btn('Następny krok', '⏭', function () { jump(1); });
    var mute = btn('Wycisz', '🔊', function () { setMuted(!muted); });
    var vol = h('input', { type: 'range', min: '0', max: '1', step: '0.05', value: '1', 'class': 'dc-demo-vol', 'aria-label': 'Głośność' });
    vol.addEventListener('input', function () { volume = +vol.value; audio.volume = volume; if (volume > 0 && muted) setMuted(false); });
    var count = h('span', { 'class': 'dc-demo-count' });
    var x = btn('Zamknij prezentację', '✕', close);

    [prev, play, next, mute, vol, count, x].forEach(function (e) { panel.appendChild(e); });
    root.appendChild(frame);
    root.appendChild(subs);
    root.appendChild(track);
    root.appendChild(panel);
    document.body.appendChild(root);
    document.documentElement.classList.add('dc-demo-open');

    ui.root = root; ui.frame = frame; ui.subs = subs; ui.bar = bar;
    ui.prev = prev; ui.play = play; ui.next = next; ui.mute = mute; ui.count = count;
    audio.addEventListener('timeupdate', progress);
  }

  function begin() {
    ui.startBtn.disabled = true;
    Promise.all([
      getJSON(BASE + 'demo_script.json'),
      getJSON(BASE + 'audio/manifest.json').catch(function () {
        console.warn('[demo] brak audio/manifest.json — całość przez speechSynthesis');
        return {};
      })
    ]).then(function (r) {
      steps = r[0].steps; manifest = r[1];
      ui.startBtn.disabled = false;
      ui.startBtn.hidden = true;
      frameUrl = null; ui.pendingNext = false;
      build();
      playing = true;
      go(0, true);
    }).catch(function (e) {
      ui.startBtn.disabled = false;
      console.error('[demo] nie można wczytać scenariusza', e);
    });
  }

  function init() {
    var b = h('button', { type: 'button', 'class': 'dc-demo-start' }, '▶  Rozpocznij prezentację');
    b.addEventListener('click', begin);         // start tylko z kliknięcia (autoplay policy)
    document.body.appendChild(b);
    ui.startBtn = b;
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && ui.root && ui.root.isConnected) close();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
