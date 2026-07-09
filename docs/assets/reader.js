/* Reader interactions: pinyin toggle, translation toggle, tap-word popover,
 * sentence & word audio via the browser's Chinese TTS (free, offline-capable).
 * Upgrade path: when a text has real recordings, set data-audio on .text-body
 * and this file will prefer the mp3 over TTS. */
(function () {
  "use strict";

  /* ---------- TTS ---------- */
  var zhVoice = null;
  function pickVoice() {
    var vs = window.speechSynthesis ? speechSynthesis.getVoices() : [];
    var zh = vs.filter(function (v) { return /^zh([-_]|$)/i.test(v.lang); });
    // prefer zh-CN, then any Chinese
    zhVoice = zh.find(function (v) { return /CN/i.test(v.lang); }) || zh[0] || null;
  }
  if (window.speechSynthesis) {
    pickVoice();
    speechSynthesis.onvoiceschanged = pickVoice;
  }
  var rate = 1.0;
  function speak(text) {
    if (!window.speechSynthesis) { alert("Your browser does not support audio."); return; }
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = "zh-CN";
    if (zhVoice) u.voice = zhVoice;
    u.rate = rate;
    speechSynthesis.speak(u);
  }

  /* ---------- toolbar toggles ---------- */
  function bindToggle(id, cls, defaultOn) {
    var b = document.getElementById(id);
    if (!b) return;
    if (defaultOn) { document.body.classList.add(cls); b.classList.add("on"); }
    b.addEventListener("click", function () {
      var on = document.body.classList.toggle(cls);
      b.classList.toggle("on", on);
    });
  }
  // pinyin: shown by default => the class hides it, so invert
  var pb = document.getElementById("t-pinyin");
  if (pb) {
    pb.classList.add("on");
    pb.addEventListener("click", function () {
      var off = document.body.classList.toggle("no-pinyin");
      pb.classList.toggle("on", !off);
    });
  }
  bindToggle("t-en", "show-en", false);

  var sb = document.getElementById("t-speed");
  if (sb) {
    sb.addEventListener("click", function () {
      rate = rate === 1.0 ? 0.7 : 1.0;
      sb.textContent = rate === 1.0 ? "🐢 Slow" : "🐇 Normal";
      sb.classList.toggle("on", rate !== 1.0);
    });
  }

  var pa = document.getElementById("t-play");
  if (pa) {
    pa.addEventListener("click", function () {
      var t = [];
      document.querySelectorAll(".zh-line").forEach(function (s) {
        t.push(s.getAttribute("data-say") || "");
      });
      speak(t.join(""));
    });
  }

  /* ---------- per-sentence play ---------- */
  document.querySelectorAll(".s-play[data-say]").forEach(function (b) {
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      speak(b.getAttribute("data-say"));
    });
  });

  /* ---------- tap-word popover ---------- */
  var pop = document.getElementById("pop");
  var lastW = null;
  document.querySelectorAll(".w").forEach(function (w) {
    w.addEventListener("click", function (e) {
      e.stopPropagation();
      if (lastW) lastW.classList.remove("hl");
      w.classList.add("hl");
      lastW = w;
      var zh = w.getAttribute("data-zh"), py = w.getAttribute("data-py"),
          en = w.getAttribute("data-en");
      pop.innerHTML =
        '<span class="p-zh">' + zh + '</span>' +
        '<span class="p-py">' + py + '</span>' +
        '<button id="pop-say" title="Play">🔊</button>' +
        '<span class="p-en">' + en + '</span>';
      pop.classList.add("show");
      document.getElementById("pop-say").addEventListener("click", function (ev) {
        ev.stopPropagation();
        speak(zh);
      });
      speak(zh);
    });
  });
  document.addEventListener("click", function () {
    if (pop) pop.classList.remove("show");
    if (lastW) { lastW.classList.remove("hl"); lastW = null; }
  });

  /* ---------- level filter on index ---------- */
  var chips = document.querySelectorAll(".lvl-chip");
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      chips.forEach(function (x) { x.classList.remove("on"); });
      c.classList.add("on");
      var l = c.getAttribute("data-l");
      document.querySelectorAll(".card[data-l]").forEach(function (card) {
        card.style.display =
          (l === "0" || card.getAttribute("data-l") === l) ? "" : "none";
      });
    });
  });
})();
