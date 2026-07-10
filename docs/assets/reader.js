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
      var saved = whas(zh);
      pop.innerHTML =
        '<div class="p-main">' +
          '<div class="p-word"><span class="p-zh">' + zh + '</span>' +
          '<span class="p-py">' + py + '</span></div>' +
          '<div class="p-en">' + en + '</div>' +
        '</div>' +
        '<div class="p-actions">' +
          '<button id="pop-say" title="Play">🔊</button>' +
          '<button class="wstar' + (saved ? " saved" : "") + '" id="pop-star" ' +
          'title="Save to wordbook">' + (saved ? "★" : "☆") + '</button>' +
        '</div>';
      pop.classList.add("show");
      document.getElementById("pop-say").addEventListener("click", function (ev) {
        ev.stopPropagation();
        speak(zh);
      });
      document.getElementById("pop-star").addEventListener("click", function (ev) {
        ev.stopPropagation();
        var s = wtoggle(zh, py, en);
        this.classList.toggle("saved", s);
        this.textContent = s ? "★" : "☆";
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
      document.dispatchEvent(new CustomEvent("rcd-changed"));
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

  /* ---------- wordbook store ---------- */
  var WSTORE = "rcd-words";
  function wget() {
    try { return JSON.parse(localStorage.getItem(WSTORE)) || []; }
    catch (e) { return []; }
  }
  function whas(z) { return wget().some(function (w) { return w.z === z; }); }
  function wtoggle(z, p, e) {
    var l = wget();
    var i = l.findIndex(function (w) { return w.z === z; });
    if (i >= 0) { l.splice(i, 1); }
    else if (p !== undefined && p !== null) { l.push({ z: z, p: p, e: e }); }
    localStorage.setItem(WSTORE, JSON.stringify(l));
    document.dispatchEvent(new CustomEvent("rcd-changed"));
    return i < 0;
  }
  // static star buttons (words page)
  document.querySelectorAll(".wstar[data-z][data-p]").forEach(function (b) {
    if (whas(b.getAttribute("data-z"))) { b.classList.add("saved"); b.textContent = "★"; }
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      var s = wtoggle(b.getAttribute("data-z"), b.getAttribute("data-p"),
                      b.getAttribute("data-e"));
      b.classList.toggle("saved", s);
      b.textContent = s ? "★" : "☆";
    });
  });

  /* ---------- cached auth state: paint signed-in UI before Firebase loads ---------- */
  var authBtn0 = document.getElementById("t-auth");
  try {
    var cachedUser = localStorage.getItem("rcd-auth");
    if (authBtn0 && cachedUser) {
      authBtn0.textContent = "👤 " + cachedUser;
      authBtn0.classList.add("signed");
    }
  } catch (e) {}

  /* ---------- mobile nav drawer ---------- */
  var burger = document.getElementById("nav-burger");
  var navMenu = document.getElementById("nav-menu");
  var navBack = document.getElementById("nav-backdrop");
  var navClose = document.getElementById("nav-close");
  function closeNav() {
    if (navMenu) navMenu.classList.remove("open");
    if (navBack) navBack.classList.remove("show");
  }
  if (burger && navMenu) {
    burger.addEventListener("click", function () {
      navMenu.classList.add("open");
      if (navBack) navBack.classList.add("show");
    });
    if (navBack) navBack.addEventListener("click", closeNav);
    if (navClose) navClose.addEventListener("click", closeNav);
    navMenu.querySelectorAll("a, #t-auth").forEach(function (a) {
      a.addEventListener("click", closeNav);
    });
  }

  /* ---------- theme toggle ---------- */
  var tt = document.getElementById("t-theme");
  if (tt) {
    var tti = document.getElementById("t-theme-i") || tt;
    if (document.documentElement.getAttribute("data-theme") === "dark") tti.textContent = "☀️";
    tt.addEventListener("click", function () {
      var dark = document.documentElement.getAttribute("data-theme") !== "dark";
      if (dark) document.documentElement.setAttribute("data-theme", "dark");
      else document.documentElement.removeAttribute("data-theme");
      tti.textContent = dark ? "☀️" : "🌙";
      try { localStorage.setItem("rcd-theme", dark ? "dark" : "light"); } catch (e) {}
    });
  }

  /* ---------- top progress bar while the next page loads ---------- */
  var pgbar = document.createElement("div");
  pgbar.id = "pgbar";
  document.body.appendChild(pgbar);
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || a.target === "_blank" || e.metaKey || e.ctrlKey) return;
    if (a.origin !== location.origin) return;
    if (a.pathname === location.pathname && a.hash) return;
    pgbar.classList.add("on");
  });
  // bfcache 返回时页面不重载,得手动把进度条收掉
  window.addEventListener("pageshow", function () { pgbar.classList.remove("on"); });

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
        ' readings finished</span><a class="ps-link" href="progress.html">🏆 View →</a>';
      var anchorEl = document.getElementById("lvlgrid") ||
        document.querySelector(".cards");
      if (anchorEl) anchorEl.parentNode.insertBefore(bar, anchorEl);
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

  /* ---------- level filter + search (index & words pages) ---------- */
  var chips = document.querySelectorAll(".lvl-chip");
  var searchEl = document.getElementById("search");
  var seg = document.querySelector(".seg");
  var segInd = document.querySelector(".seg-ind");
  function moveInd() {
    if (!segInd || !seg) return;
    var on = document.querySelector(".lvl-chip.on");
    if (!on) return;
    segInd.style.left = on.offsetLeft + "px";
    segInd.style.width = on.offsetWidth + "px";
    segInd.style.background =
      "var(--lvl" + (on.getAttribute("data-l") || "0") + ")";
    seg.classList.add("hasind");
    segInd.classList.add("ready");
    // 窄屏上 tab 条会横向溢出,把当前级别滚到可视区中间,不然像消失了一样
    if (seg.scrollWidth > seg.clientWidth) {
      seg.scrollLeft = Math.max(0,
        on.offsetLeft - (seg.clientWidth - on.offsetWidth) / 2);
    }
  }
  function applyFilters(animate) {
    var onChip = document.querySelector(".lvl-chip.on");
    var l = onChip ? onChip.getAttribute("data-l") : "0";
    var q = searchEl ? searchEl.value.trim().toLowerCase() : "";
    var shown = [];
    document.querySelectorAll("[data-search]").forEach(function (el) {
      var okL = l === "0" || el.getAttribute("data-l") === l;
      var okQ = !q || (el.getAttribute("data-search") || "").indexOf(q) >= 0;
      var ok = okL && okQ;
      el.style.display = ok ? "" : "none";
      if (ok) shown.push(el);
    });
    if (!animate) return;
    shown.forEach(function (el) {
      el.style.transition = "none";
      el.style.opacity = "0";
      el.style.transform = "translateY(10px)";
    });
    void document.body.offsetHeight; // flush, so the fade-in actually runs
    shown.forEach(function (el, i) {
      var d = Math.min(i * 30, 300);
      el.style.transition = "opacity .3s ease, transform .3s ease";
      el.style.transitionDelay = d + "ms";
      el.style.opacity = "1";
      el.style.transform = "none";
      setTimeout(function () {
        el.style.transition = "";
        el.style.transitionDelay = "";
        el.style.opacity = "";
        el.style.transform = "";
      }, 400 + d);
    });
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      if (c.classList.contains("on")) return;
      chips.forEach(function (x) { x.classList.remove("on"); });
      c.classList.add("on");
      moveInd();
      c.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
      applyFilters(true);
    });
  });
  if (searchEl) searchEl.addEventListener("input", function () {
    // home page: search reveals the (otherwise hidden) full list,
    // and tucks the level grid / today's pick away while typing
    var res = document.getElementById("search-results");
    if (res) {
      var q = !!searchEl.value.trim();
      res.hidden = !q;
      var lg = document.getElementById("lvlgrid");
      if (lg) lg.hidden = q;
      var tw = document.getElementById("today-wrap");
      if (tw) tw.hidden = q || !tw.dataset.filled;
    }
    applyFilters(false);
  });
  if (segInd) {
    moveInd();
    window.addEventListener("resize", moveInd);
    setTimeout(moveInd, 300);   // re-measure once webfonts settle
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(moveInd);
  }

  /* ---------- word rows expand to examples & usage (words + wordbook) ----------
     Detail HTML is built lazily from assets/word-examples.json on first tap;
     inlining it at build time made words.html balloon past 1 MB. */
  var WEX = null, wexWaiters = [];
  if (document.querySelector(".wlist")) {
    fetch("assets/word-examples.json")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        WEX = d;
        wexWaiters.forEach(function (f) { f(); });
        wexWaiters = [];
      }).catch(function () {});
  }
  function wexSentence(idx, hlWord) {
    var s = WEX.s[idx];
    var zh = s[0].map(function (tk) {
      if (tk.length === 1) return tk[0];
      var r = "<ruby>" + tk[0] + "<rt>" + tk[1] + "</rt></ruby>";
      return tk[0] === hlWord ? "<b>" + r + "</b>" : r;
    }).join("");
    return { zh: zh, en: s[1], slug: s[2], title: s[3] };
  }
  function wexFirstEx(z) {
    var d = WEX && WEX.w && WEX.w[z];
    return (d && d.ex.length) ? wexSentence(d.ex[0], z) : null;
  }
  function wexDetail(z) {
    var d = WEX && WEX.w && WEX.w[z];
    if (!d || (!d.ex.length && !d.us.length)) return "";
    var h = '<div class="vdetail">';
    d.us.forEach(function (u) {
      h += '<div class="vuse"><b>' + u[0] + "</b> " + u[1] + "</div>";
    });
    d.ex.forEach(function (i) {
      var e = wexSentence(i, z);
      h += '<div class="vex"><span class="vex-zh">' + e.zh +
        '</span><span class="vex-en">' + e.en +
        '</span><a class="vex-src" href="texts/' + e.slug + '.html">《' +
        e.title + "》→</a></div>";
    });
    return h + "</div>";
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest("button, a")) return;
    var it = e.target.closest ? e.target.closest(".vitem.vx") : null;
    if (!it) return;
    if (it.querySelector(".vdetail")) { it.classList.toggle("open"); return; }
    var z = (it.querySelector(".vzh") || {}).textContent || "";
    var open = function () {
      var h = wexDetail(z);
      if (h) { it.insertAdjacentHTML("beforeend", h); it.classList.add("open"); }
    };
    if (WEX) open(); else wexWaiters.push(open);
  });

  /* ---------- today's pick (index only, into its own slot) ---------- */
  var todaySlot = document.getElementById("today-slot");
  if (idxCards.length && todaySlot) {
    var day = Math.floor(Date.now() / 86400000);
    var pick = idxCards[day % idxCards.length];
    if (pick) {
      // clone: the original stays findable in the search results list
      var cl = pick.cloneNode(true);
      var tflag = document.createElement("span");
      tflag.className = "today-flag";
      tflag.textContent = "📖 Today";
      cl.appendChild(tflag);
      todaySlot.appendChild(cl);
      var tw = document.getElementById("today-wrap");
      if (tw) { tw.hidden = false; tw.dataset.filled = "1"; }
    }
  }

  /* ---------- home level cards: fill read-progress ---------- */
  var lvlCards = document.querySelectorAll(".lvlcard[data-l]");
  if (lvlCards.length) {
    var lp = pget(), byLvl = {};
    Object.keys(lp.done || {}).forEach(function (s) {
      var l = (window.RCD_LEVELS || {})[s];
      if (l) byLvl[l] = (byLvl[l] || 0) + 1;
    });
    lvlCards.forEach(function (c) {
      var l = c.getAttribute("data-l"), n = +c.getAttribute("data-n") || 0;
      var d = byLvl[l] || 0;
      if (!d) return;
      var t = c.querySelector(".lv-done");
      if (t) t.textContent = d + " / " + n + " read";
      var b = c.querySelector(".lv-bar i");
      if (b) b.style.width = (n ? Math.min(100, Math.round(d / n * 100)) : 0) + "%";
    });
  }

  /* ---------- progress page: stats, badges, calendar ---------- */
  var pgBadges = document.getElementById("pg-badges");
  if (pgBadges) {
    var pp = pget(), doneMap = pp.done || {};
    var doneSlugs = Object.keys(doneMap);
    var doneN = doneSlugs.length, wordsN = wget().length;
    var dayCount = {};
    doneSlugs.forEach(function (s) {
      dayCount[doneMap[s]] = (dayCount[doneMap[s]] || 0) + 1;
    });
    function nextDay(s) {
      var d = new Date(s + "T00:00:00");
      d.setDate(d.getDate() + 1);
      return localDay(d);
    }
    var ds = Object.keys(dayCount).sort();
    var best = 0, run = 0, prev = null;
    ds.forEach(function (d) {
      run = (prev && nextDay(prev) === d) ? run + 1 : 1;
      best = Math.max(best, run);
      prev = d;
    });
    var curStreak = streak(pp);
    var lvlDone = {};
    doneSlugs.forEach(function (s) {
      var l = (window.RCD_LEVELS || {})[s];
      if (l) lvlDone[l] = (lvlDone[l] || 0) + 1;
    });
    var totals = window.RCD_TOTALS || {};

    document.getElementById("pg-stats").innerHTML = [
      ["🔥", curStreak, "day streak"],
      ["🏅", best, "best streak"],
      ["📖", doneN, "readings done"],
      ["⭐", wordsN, "words saved"],
    ].map(function (x) {
      return '<div class="stat"><div class="s-i">' + x[0] +
        '</div><div class="s-n">' + x[1] + '</div><div class="s-l">' +
        x[2] + "</div></div>";
    }).join("");

    function lvlBadge(l) {
      return (totals[l] || totals[String(l)]) &&
        (lvlDone[l] || 0) >= (totals[l] || totals[String(l)]);
    }
    var BD = [
      ["🌱", "First Read", "Finish your first reading", doneN >= 1],
      ["📖", "Reader", "Finish 5 readings", doneN >= 5],
      ["🐛", "Bookworm", "Finish 15 readings", doneN >= 15],
      ["🎓", "Scholar", "Finish 50 readings", doneN >= 50],
      ["🔥", "On Fire", "3-day reading streak", best >= 3],
      ["⚡", "Unstoppable", "7-day reading streak", best >= 7],
      ["🏆", "Iron Will", "30-day reading streak", best >= 30],
      ["⭐", "Collector", "Save 10 words", wordsN >= 10],
      ["💎", "Word Dragon", "Save 50 words", wordsN >= 50],
      ["🀄", "HSK 1 Complete", "Finish every HSK 1 reading", lvlBadge(1)],
      ["🎋", "HSK 2 Complete", "Finish every HSK 2 reading", lvlBadge(2)],
      ["🐉", "HSK 3 Complete", "Finish every HSK 3 reading", lvlBadge(3)],
    ];
    pgBadges.innerHTML = BD.map(function (b) {
      return '<div class="bd' + (b[3] ? " got" : "") + '"><div class="bd-i">' +
        b[0] + '</div><div class="bd-n">' + b[1] + '</div><div class="bd-d">' +
        b[2] + "</div></div>";
    }).join("");

    var calEl = document.getElementById("pg-cal");
    var now = new Date(), vy = now.getFullYear(), vm = now.getMonth();
    function renderCal() {
      var first = new Date(vy, vm, 1);
      var startDow = first.getDay();
      var dim = new Date(vy, vm + 1, 0).getDate();
      var html = '<div class="cal-head"><button class="tbtn" id="cal-prev">←</button><b>' +
        first.toLocaleString("en", { month: "long" }) + " " + vy +
        '</b><button class="tbtn" id="cal-next">→</button></div><div class="cal-grid">' +
        ["S", "M", "T", "W", "T", "F", "S"].map(function (d) {
          return '<span class="cal-dow">' + d + "</span>";
        }).join("");
      for (var i = 0; i < startDow; i++) html += "<span></span>";
      for (var d = 1; d <= dim; d++) {
        var key = vy + "-" + String(vm + 1).padStart(2, "0") + "-" +
          String(d).padStart(2, "0");
        var n = dayCount[key] || 0;
        var isToday = key === localDay(new Date());
        html += '<span class="cal-day' + (n ? " on" : "") +
          (isToday ? " td" : "") + '"' +
          (n ? ' title="' + n + ' reading(s)"' : "") + ">" + d + "</span>";
      }
      calEl.innerHTML = html + "</div>";
      document.getElementById("cal-prev").onclick = function () {
        vm--; if (vm < 0) { vm = 11; vy--; } renderCal();
      };
      document.getElementById("cal-next").onclick = function () {
        vm++; if (vm > 11) { vm = 0; vy++; } renderCal();
      };
    }
    renderCal();
  }

  /* ---------- wordbook page ---------- */
  var wbList = document.getElementById("wb-list");
  if (wbList) {
    var practiceBtn = document.getElementById("wb-practice");
    var deck = document.getElementById("deck");
    var deckCard = document.getElementById("deck-card");
    var order = [], di = 0;
    function renderWb() {
      var l = wget();
      if (!l.length) {
        wbList.innerHTML = '<div class="wb-empty">No words saved yet — tap ☆ on any word while reading.</div>';
        return;
      }
      wbList.innerHTML = l.map(function (w) {
        return '<div class="vitem vx"><button class="s-play" data-say="' + w.z +
          '">🔊</button><div class="vtext"><span class="vzh">' + w.z +
          '</span><span class="vpy">' + w.p + '</span><span class="ven">' +
          w.e + '</span><span class="vmore">▾</span></div>' +
          '<button class="wstar saved" data-z="' + w.z +
          '">★</button></div>';
      }).join("");
      wbList.querySelectorAll(".s-play").forEach(function (b) {
        b.addEventListener("click", function (e) {
          e.stopPropagation(); speak(b.getAttribute("data-say"));
        });
      });
      wbList.querySelectorAll(".wstar").forEach(function (b) {
        b.addEventListener("click", function () {
          wtoggle(b.getAttribute("data-z")); renderWb();
        });
      });
    }
    renderWb();
    function showDeckCard(flip) {
      var w = order[di];
      var fx = flip ? wexFirstEx(w.z) : null;
      var ex = fx
        ? '<div class="dex">' + fx.zh + '<i>' + fx.en + '</i></div>'
        : "";
      deckCard.innerHTML = flip
        ? '<div class="dz">' + w.z + '</div><div class="dp">' + w.p +
          '</div><div class="de">' + w.e + '</div>' + ex
        : '<div class="dz">' + w.z + '</div><div class="dhint">Tap “Show answer”</div>';
      if (flip) speak(w.z);
    }
    if (practiceBtn) {
      practiceBtn.addEventListener("click", function () {
        var l = wget();
        if (!l.length) { alert("Save some words first — tap ☆ on any word while reading."); return; }
        order = l.slice().sort(function () { return Math.random() - 0.5; });
        di = 0; deck.hidden = false; wbList.hidden = true;
        practiceBtn.style.display = "none";
        showDeckCard(false);
      });
      document.getElementById("deck-flip").addEventListener("click", function () { showDeckCard(true); });
      document.getElementById("deck-next").addEventListener("click", function () {
        di = (di + 1) % order.length; showDeckCard(false);
      });
      document.getElementById("deck-close").addEventListener("click", function () {
        deck.hidden = true; wbList.hidden = false;
        practiceBtn.style.display = ""; renderWb();
      });
    }
  }
})();
