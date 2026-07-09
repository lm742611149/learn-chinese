/* Reader interactions: pinyin toggle, translation toggle, tap-word popover,
 * sentence & word audio via the browser's Chinese TTS.
 * Voice: auto-picks the clearest female Mandarin voice available on the
 * device, and offers a voice picker (persisted in localStorage). */
(function () {
  "use strict";

  /* ---------- TTS voice selection ---------- */
  // Known good, clear (mostly female) Mandarin voices across platforms,
  // best first: iOS/macOS Tingting, Windows Xiaoxiao/Huihui/Yaoyao,
  // Android/Chrome "Google 普通话".
  var PREFERRED = ["Tingting", "婷婷", "Xiaoxiao", "晓晓", "Google 普通话",
                   "Huihui", "慧慧", "Yaoyao", "瑶瑶", "Meijia", "Sinji"];
  var zhVoices = [], voice = null;

  function scoreVoice(v) {
    var s = 0;
    if (/zh[-_]CN/i.test(v.lang)) s += 40; else if (/^zh/i.test(v.lang)) s += 10;
    for (var i = 0; i < PREFERRED.length; i++) {
      if (v.name.indexOf(PREFERRED[i]) !== -1) { s += 100 - i * 5; break; }
    }
    if (/natural|neural|online/i.test(v.name)) s += 30;   // MS natural voices
    if (/enhanced|premium/i.test(v.name)) s += 15;        // Apple enhanced
    if (/eloquence|compact/i.test(v.name)) s -= 40;       // robotic fallbacks
    return s;
  }

  function refreshVoices() {
    if (!window.speechSynthesis) return;
    zhVoices = speechSynthesis.getVoices()
      .filter(function (v) { return /^zh/i.test(v.lang); })
      .sort(function (a, b) { return scoreVoice(b) - scoreVoice(a); });
    var saved = localStorage.getItem("zh-voice");
    voice = zhVoices.find(function (v) { return v.name === saved; }) || zhVoices[0] || null;
    fillVoicePicker();
  }
  if (window.speechSynthesis) {
    refreshVoices();
    speechSynthesis.onvoiceschanged = refreshVoices;
  }

  function fillVoicePicker() {
    var sel = document.getElementById("t-voice");
    if (!sel || !zhVoices.length) return;
    sel.innerHTML = zhVoices.map(function (v) {
      return '<option value="' + v.name + '"' +
        (voice && v.name === voice.name ? " selected" : "") + ">" +
        v.name.replace(/\s*\(.*\)$/, "") + "</option>";
    }).join("");
    sel.onchange = function () {
      voice = zhVoices.find(function (v) { return v.name === sel.value; }) || voice;
      localStorage.setItem("zh-voice", sel.value);
      speak("你好,我们一起读中文吧!");
    };
  }

  var rate = 1.0;
  /* --- Play-all state machine: idle -> playing <-> paused -> idle --- */
  var ICON_PLAY = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
  var ICON_PAUSE = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
  var playBtn = document.getElementById("t-play");
  var playState = "idle";
  function setPlayState(s) {
    playState = s;
    if (!playBtn) return;
    playBtn.innerHTML = s === "playing" ? ICON_PAUSE + " Pause"
      : s === "paused" ? ICON_PLAY + " Resume"
      : ICON_PLAY + " Play all";
  }
  var sents = Array.prototype.slice.call(document.querySelectorAll(".sent"));
  function clearKaraoke() {
    sents.forEach(function (s) { s.classList.remove("playing"); });
  }
  function speak(text) {
    if (!window.speechSynthesis) { alert("Your browser does not support audio."); return; }
    speechSynthesis.cancel();     // kills any play-all session too
    setPlayState("idle");
    clearKaraoke();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = "zh-CN";
    if (voice) u.voice = voice;
    u.rate = rate;
    speechSynthesis.speak(u);
  }

  /* ---------- toolbar toggles ---------- */
  var pb = document.getElementById("t-pinyin");
  if (pb) {
    pb.classList.add("on");
    pb.addEventListener("click", function () {
      var off = document.body.classList.toggle("no-pinyin");
      pb.classList.toggle("on", !off);
    });
  }
  var eb = document.getElementById("t-en");
  if (eb) {
    eb.addEventListener("click", function () {
      var on = document.body.classList.toggle("show-en");
      eb.classList.toggle("on", on);
    });
  }
  var sb = document.getElementById("t-speed");
  if (sb) {
    sb.addEventListener("click", function () {
      rate = rate === 1.0 ? 0.7 : 1.0;
      sb.classList.toggle("on", rate !== 1.0);
    });
  }
  if (playBtn) {
    playBtn.addEventListener("click", function () {
      if (!window.speechSynthesis) { alert("Your browser does not support audio."); return; }
      if (playState === "playing") {          // -> pause
        speechSynthesis.pause();
        setPlayState("paused");
        return;
      }
      if (playState === "paused") {           // -> resume
        speechSynthesis.resume();
        setPlayState("playing");
        return;
      }
      // idle -> karaoke mode: play sentence by sentence with highlight
      speechSynthesis.cancel();
      setPlayState("playing");
      playSentence(0);
    });
  }
  function playSentence(i) {
    if (i >= sents.length) { clearKaraoke(); setPlayState("idle"); return; }
    clearKaraoke();
    var s = sents[i];
    s.classList.add("playing");
    try { s.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) {}
    var line = s.querySelector(".zh-line");
    var u = new SpeechSynthesisUtterance(line ? line.getAttribute("data-say") : "");
    u.lang = "zh-CN";
    if (voice) u.voice = voice;
    u.rate = rate;
    u.onend = function () {
      if (playState === "playing") playSentence(i + 1);
    };
    u.onerror = function () {
      if (playState === "playing") playSentence(i + 1);
    };
    speechSynthesis.speak(u);
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

  /* ---------- progress & streak (localStorage) ---------- */
  var STORE = "rcd-progress";
  function localDay(d) {
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") +
      "-" + String(d.getDate()).padStart(2, "0");
  }
  function pget() {
    try { return JSON.parse(localStorage.getItem(STORE)) || { done: {} }; }
    catch (e) { return { done: {} }; }
  }
  function markDone(slug) {
    var p = pget();
    if (!p.done[slug]) {
      p.done[slug] = localDay(new Date());
      localStorage.setItem(STORE, JSON.stringify(p));
    }
    return p;
  }
  function streak(p) {
    var days = {};
    Object.keys(p.done).forEach(function (k) { days[p.done[k]] = 1; });
    var s = 0, d = new Date();
    if (!days[localDay(d)]) d.setDate(d.getDate() - 1); // today not read yet
    while (days[localDay(d)]) { s++; d.setDate(d.getDate() - 1); }
    return s;
  }

  /* ---------- quiz ---------- */
  var quiz = document.getElementById("quiz");
  if (quiz) {
    var qitems = quiz.querySelectorAll(".qitem");
    var answered = 0, correctN = 0;
    qitems.forEach(function (it) {
      var c = parseInt(it.getAttribute("data-c"), 10);
      var opts = it.querySelectorAll(".qopt");
      opts.forEach(function (o, i) {
        o.addEventListener("click", function () {
          if (it.classList.contains("ans")) return;
          it.classList.add("ans");
          if (i === c) { o.classList.add("ok"); correctN++; }
          else { o.classList.add("bad"); opts[c].classList.add("ok"); }
          answered++;
          if (answered === qitems.length) {
            var slug = location.pathname.split("/").pop().replace(".html", "");
            var p = markDone(slug);
            var r = document.getElementById("qresult");
            r.hidden = false;
            r.innerHTML = "You got <b>" + correctN + " / " + qitems.length +
              "</b> &nbsp;·&nbsp; ✓ Reading finished &nbsp;·&nbsp; 🔥 " +
              streak(p) + "-day streak";
            try { r.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) {}
          }
        });
      });
    });
  }

  /* ---------- progress annotations on index ---------- */
  var idxCards = document.querySelectorAll(".card[href]");
  if (idxCards.length) {
    var prog = pget(), doneCount = 0;
    idxCards.forEach(function (c) {
      var slug = (c.getAttribute("href") || "").split("/").pop().replace(".html", "");
      if (prog.done[slug]) {
        doneCount++;
        c.classList.add("done");
        var m = c.querySelector(".meta");
        if (m) {
          var f = document.createElement("span");
          f.className = "done-flag";
          f.textContent = "✓ Read";
          m.insertBefore(f, m.querySelector(".go"));
        }
      }
    });
    if (doneCount > 0) {
      var bar = document.createElement("div");
      bar.className = "progress-strip";
      bar.innerHTML = '<span class="fire">🔥 ' + streak(prog) +
        "-day streak</span><span>" + doneCount + " / " + idxCards.length +
        " readings finished</span>";
      var cardsEl = document.querySelector(".cards");
      if (cardsEl) cardsEl.parentNode.insertBefore(bar, cardsEl);
    }
  }

  /* ---------- hero carousel on index ---------- */
  var track = document.getElementById("hero-track");
  if (track) {
    var dots = document.querySelectorAll("#hero-dots .dot");
    var n = track.children.length, idx = 0, timer = null;
    function go(i) {
      idx = (i + n) % n;
      track.scrollTo({ left: idx * track.clientWidth, behavior: "smooth" });
    }
    function sync() {
      var i = Math.round(track.scrollLeft / track.clientWidth);
      idx = Math.max(0, Math.min(n - 1, i));
      dots.forEach(function (d, k) { d.classList.toggle("on", k === idx); });
    }
    track.addEventListener("scroll", function () { requestAnimationFrame(sync); },
      { passive: true });
    dots.forEach(function (d, k) {
      d.addEventListener("click", function () { go(k); restart(); });
    });
    function restart() {
      if (timer) clearInterval(timer);
      timer = setInterval(function () { go(idx + 1); }, 5000);
    }
    // pause while the user is interacting
    track.addEventListener("touchstart", function () {
      if (timer) clearInterval(timer);
    }, { passive: true });
    track.addEventListener("touchend", restart, { passive: true });
    track.addEventListener("mouseenter", function () {
      if (timer) clearInterval(timer);
    });
    track.addEventListener("mouseleave", restart);
    restart();
  }

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
