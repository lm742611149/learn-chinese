#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site generator (stdlib only).

    python3 build.py      ->  regenerates docs/ from content/ + assets/

Add a reading = drop a JSON into content/texts/ and rebuild.
Deploy = GitHub Pages serving the docs/ folder.
"""
import html
import json
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
SITE = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))

LEVEL_WORDS = {1: "Newbie", 2: "Elementary", 3: "Intermediate",
               4: "Upper Int.", 5: "Advanced", 6: "Fluent"}
LEVEL_COLORS = {1: "#3e9464", 2: "#2f7fa8", 3: "#7b5fc0",
                4: "#cf7622", 5: "#c73e2a", 6: "#6d4434"}


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, desc, body, rel=""):
    """rel = prefix to reach site root ('' at root, '../' inside texts/)."""
    name = esc(SITE["site_name"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%23c73e2a'/><text x='50' y='72' font-size='62' text-anchor='middle' fill='white' font-family='serif' font-weight='bold'>读</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700;900&display=swap">
<link rel="stylesheet" href="{rel}assets/style.css">
<link rel="manifest" href="{rel}manifest.webmanifest">
<link rel="apple-touch-icon" href="{rel}assets/icon-180.png">
<meta name="theme-color" content="#c73e2a">
<script>try{{if(localStorage.getItem("rcd-theme")==="dark")document.documentElement.setAttribute("data-theme","dark")}}catch(e){{}}</script>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="brand" href="{rel}index.html"><span class="seal">读</span><span class="bname">{name}</span></a>
    <nav>
      <a class="nav-link" href="{rel}words.html">Words</a>
      <a class="nav-link" href="{rel}wordbook.html" title="My wordbook">★</a>
      <button class="nav-link" id="t-theme" title="Dark mode">🌙</button>
      <a class="nav-cta" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M13.4 21v-8.2h2.8l.4-3.2h-3.2V7.5c0-.9.3-1.6 1.7-1.6h1.7V3.1c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.3v3.2h2.8V21h3.3z"/></svg>
        Follow</a>
    </nav>
  </header>
{body}
  <footer class="footer">
    <div>© {name} · Original graded readings, free to read.</div>
    <div style="margin-top:6px">
      <a href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">Facebook</a>
      <a href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a lesson</a>
      <a href="{rel}about.html">About</a>
    </div>
  </footer>
</div>
<div id="pop"></div>
<script src="{rel}assets/reader.js"></script>
<script>if("serviceWorker" in navigator)navigator.serviceWorker.register("{rel}sw.js");</script>
{SITE.get("analytics_snippet", "")}
</body>
</html>"""


OPENING_PUNCT = set("“‘(《【〈「『")


def sentence_html(sent):
    """Chinese line with ruby pinyin + tappable words + a play button.
    Words are grouped with their adjacent punctuation into no-break units
    (.nb) so lines never start with a closing quote / full stop and never
    split inside a word."""
    units, say, prefix = [], [], ""
    for tok in sent["t"]:
        if len(tok) == 1:  # punctuation
            say.append(tok[0])
            p = f'<span class="punct">{esc(tok[0])}</span>'
            if tok[0] in OPENING_PUNCT:
                prefix += p          # attach opening quote to the NEXT word
            elif units:
                units[-1] += p       # attach closing punct to the previous word
            else:
                prefix += p
        else:
            zh, py, en = tok
            say.append(zh)
            units.append(
                prefix +
                f'<span class="w" data-zh="{esc(zh)}" data-py="{esc(py)}" '
                f'data-en="{esc(en)}"><ruby>{esc(zh)}<rt>{esc(py)}</rt></ruby></span>')
            prefix = ""
    if prefix:
        units.append(prefix)
    parts = "".join(f'<span class="nb">{u}</span>' for u in units)
    say_txt = esc("".join(say))
    return (f'<div class="sent">'
            f'<div class="zh-line" data-say="{say_txt}">{parts}'
            f'<button class="s-play" data-say="{say_txt}" title="Play sentence">🔊</button></div>'
            f'<div class="en-line">{esc(sent["en"])}</div></div>')


def build_reader(t):
    n_words = sum(len(s["t"]) for s in t["sentences"])
    minutes = max(1, round(n_words / 60))
    body_sents = "\n".join(sentence_html(s) for s in t["sentences"])
    vocab_rows = "\n".join(
        f'<div class="vitem"><button class="s-play" data-say="{esc(z)}">🔊</button>'
        f'<div class="vtext"><span class="vzh">{esc(z)}</span>'
        f'<span class="vpy">{esc(p)}</span>'
        f'<span class="ven">{esc(e)}</span></div></div>'
        for z, p, e in t["vocab"])

    grammar_html = ""
    if t.get("grammar"):
        gitems = "".join(
            f'<div class="gitem"><div class="gp">{esc(g["p"])}</div>'
            f'<p>{esc(g["e"])}</p>'
            f'<div class="gx">{esc(g["x"])}</div></div>'
            for g in t["grammar"])
        grammar_html = (f'    <section class="grammar">\n'
                        f'      <h2>Grammar note <span class="zh">语法点</span></h2>\n'
                        f'      {gitems}\n'
                        f'    </section>')

    quiz_html = ""
    if t.get("quiz"):
        qitems = []
        for qi, q in enumerate(t["quiz"]):
            opts = "".join(f'<button class="qopt">{esc(o)}</button>' for o in q["a"])
            qitems.append(
                f'<div class="qitem" data-c="{q["c"]}">'
                f'<div class="qq">{qi + 1}. {esc(q["q"])}</div>'
                f'<div class="qopts">{opts}</div></div>')
        quiz_html = (f'    <section class="quiz" id="quiz">\n'
                     f'      <h2>Check yourself <span class="zh">小测验</span></h2>\n'
                     f'      {"".join(qitems)}\n'
                     f'      <div class="qresult" id="qresult" hidden></div>\n'
                     f'    </section>')
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[t['level']]}" data-char="{esc(t['title_zh'][0])}">
      <span class="feat-tag">HSK {t['level']} · {LEVEL_WORDS[t['level']]}</span>
      <h1>{esc(t['title_zh'])}</h1>
      <div class="b-py">{esc(t['title_py'])}</div>
      <div class="b-en">{esc(t['title_en'])} · {n_words} words · ~{minutes} min</div>
    </div>
    <div class="toolbar">
      <button class="tb-play" id="t-play">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
        Play all</button>
      <button class="tbtn" id="t-pinyin">拼音</button>
      <button class="tbtn" id="t-en">English</button>
      <button class="tbtn" id="t-speed">Slow 0.7×</button>
      <select class="tbtn tb-voice" id="t-voice" title="Choose voice"></select>
    </div>
    <div class="paper-card">
      <div class="text-body">
{body_sents}
      </div>
      <div class="caption">🔊 Audio uses your device's Chinese voice for now —
        teacher recordings are coming. Tap any word to see its meaning.</div>
    </div>
    <section class="vocab">
      <h2>Key words <span class="zh">生词</span></h2>
      <div class="vgrid">{vocab_rows}</div>
    </section>
{grammar_html}
{quiz_html}
    <div class="reader-foot">
      <a class="tbtn" href="../index.html">← All readings</a>
      <a class="nav-cta" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M13.4 21v-8.2h2.8l.4-3.2h-3.2V7.5c0-.9.3-1.6 1.7-1.6h1.7V3.1c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.3v3.2h2.8V21h3.3z"/></svg>
        Follow for daily lessons</a>
    </div>
  </article>"""
    title = f"{t['title_zh']} {t['title_en']} — HSK {t['level']} Reading | {SITE['site_name']}"
    desc = (f"Free HSK {t['level']} graded Chinese reading with pinyin, audio and "
            f"English translation: {t['title_en']}.")
    return page(title, desc, body, rel="../")


def build_index(texts):
    by_slug = {t["slug"]: t for t in texts}
    featured = [by_slug[s] for s in SITE.get("featured", []) if s in by_slug]
    slides = []
    for t in featured:
        n_words = sum(len(s["t"]) for s in t["sentences"])
        slides.append(f"""      <a class="slide feat" data-char="{esc(t['title_zh'][0])}"
        style="--sc:{LEVEL_COLORS[t['level']]}" href="texts/{t['slug']}.html">
        <span class="feat-tag">Featured · HSK {t['level']}</span>
        <h2 class="feat-zh">{esc(t['title_zh'])}</h2>
        <div class="feat-py">{esc(t['title_py'])}</div>
        <p>{esc(t['title_en'])} · {n_words} words</p>
        <span class="cta">Read now →</span>
      </a>""")
    featured_slides = "\n".join(slides)
    dots = "".join(f'<button class="dot{" on" if i == 0 else ""}" aria-label="slide {i+1}"></button>'
                   for i in range(1 + len(featured)))
    cards = []
    for t in sorted(texts, key=lambda x: (x["level"], x["slug"])):
        n_words = sum(len(s["t"]) for s in t["sentences"])
        search_blob = " ".join([t["title_zh"], t["title_py"], t["title_en"]] +
                               [w[0] + " " + w[1] + " " + w[2] for w in t["vocab"]]).lower()
        cards.append(f"""
    <a class="card" data-l="{t['level']}" data-search="{esc(search_blob)}" href="texts/{t['slug']}.html">
      <div class="tile">{esc(t['title_zh'][0])}</div>
      <div class="card-main">
        <div class="zh-title">{esc(t['title_zh'])}</div>
        <div class="py-title">{esc(t['title_py'])}</div>
        <div class="en-title">{esc(t['title_en'])}</div>
        <div class="meta"><span class="badge l{t['level']}">HSK {t['level']}</span>
          <span>{n_words} words</span><span class="go">读 →</span></div>
      </div>
    </a>""")
    counts = {}
    for t in texts:
        counts[t["level"]] = counts.get(t["level"], 0) + 1
    chips = [f'<button class="lvl-chip on" data-l="0">All<span class="n">{len(texts)}</span></button>'] + [
        f'<button class="lvl-chip" data-l="{i}">HSK {i}<span class="n">{counts.get(i, 0)}</span></button>'
        for i in range(1, 7)]
    body = f"""
  <section class="carousel">
    <div class="hero-track" id="hero-track">
      <div class="slide intro" data-char="读">
        <h1>Real Chinese in <span class="zh">5</span> minutes a day.</h1>
        <p>Free graded readings with pinyin, tap-to-translate and audio — by a real Chinese teacher.</p>
        <a class="cta" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">
          Follow the daily lessons →</a>
      </div>
{featured_slides}
    </div>
    <div class="dots" id="hero-dots">{dots}</div>
  </section>
  <div class="searchbar"><input type="search" id="search"
    placeholder="Search readings — 汉字 / pinyin / English…" autocomplete="off"></div>
  <div class="levels"><div class="seg">{''.join(chips)}</div></div>
  <section class="cards">{''.join(cards)}
  </section>"""
    return page(f"{SITE['site_name']} — Free graded Chinese readings (HSK 1-6)",
                SITE["description"], body)


def build_words(texts):
    """Aggregate every unique word from all readings into one searchable list."""
    words = {}   # zh -> (level, py, en)
    for t in sorted(texts, key=lambda x: x["level"]):
        pool = [tok for s in t["sentences"] for tok in s["t"] if len(tok) == 3]
        pool += [list(v) for v in t["vocab"]]
        for zh, py, en in pool:
            if zh not in words:
                words[zh] = (t["level"], py, en)
    rows = []
    for zh in sorted(words, key=lambda z: (words[z][0], words[z][1].lower())):
        lvl, py, en = words[zh]
        blob = f"{zh} {py} {en}".lower()
        rows.append(
            f'<div class="vitem" data-l="{lvl}" data-search="{esc(blob)}">'
            f'<button class="s-play" data-say="{esc(zh)}">🔊</button>'
            f'<div class="vtext"><span class="vzh">{esc(zh)}</span>'
            f'<span class="vpy">{esc(py)}</span>'
            f'<span class="badge l{lvl}">HSK {lvl}</span>'
            f'<span class="ven">{esc(en)}</span></div>'
            f'<button class="wstar" data-z="{esc(zh)}" data-p="{esc(py)}" '
            f'data-e="{esc(en)}" title="Save to wordbook">☆</button></div>')
    chips = ['<button class="lvl-chip on" data-l="0">All</button>'] + [
        f'<button class="lvl-chip" data-l="{i}">HSK {i}</button>' for i in range(1, 7)]
    body = f"""
  <section class="about">
    <h1>Vocabulary <span style="font-family:var(--serif);color:var(--red)">词汇表</span></h1>
    <p>{len(words)} words from our graded readings — tap 🔊 to hear, ☆ to save to your wordbook.</p>
  </section>
  <div class="searchbar"><input type="search" id="search"
    placeholder="Search — 汉字 / pinyin / English…" autocomplete="off"></div>
  <div class="levels"><div class="seg">{''.join(chips)}</div></div>
  <div class="wlist">{''.join(rows)}</div>"""
    return page(f"Chinese Vocabulary List (HSK 1-6) | {SITE['site_name']}",
                "Searchable Chinese vocabulary with pinyin and audio from graded readings.",
                body)


def build_wordbook():
    body = """
  <section class="about">
    <h1>My Wordbook <span style="font-family:var(--serif);color:var(--red)">生词本</span></h1>
    <p>Words you saved with ☆ while reading. Stored on this device.</p>
  </section>
  <div class="wb-actions">
    <button class="tb-play" id="wb-practice">Practice flashcards</button>
  </div>
  <div class="wlist" id="wb-list"></div>
  <div class="deck" id="deck" hidden>
    <div class="deck-card" id="deck-card"></div>
    <div class="deck-btns">
      <button class="tbtn" id="deck-flip">Show answer</button>
      <button class="tbtn" id="deck-next">Next →</button>
      <button class="tbtn" id="deck-close">Done</button>
    </div>
  </div>"""
    return page(f"My Wordbook | {SITE['site_name']}",
                "Your saved Chinese words with flashcard practice.", body)


def build_about():
    body = f"""
  <section class="about">
    <h1>About</h1>
    <p>你好! I'm <strong>{esc(SITE['teacher_name'])}</strong>. {esc(SITE['teacher_bio'])}</p>
    <p>Every reading here is <strong>original</strong>, written and graded for
      real HSK levels — short enough to finish with your morning coffee,
      rich enough to actually teach you something.</p>
    <p>Want to go faster with a real teacher?
      <a href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a 1-on-1 lesson</a>
      or follow the free daily lessons on
      <a href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">Facebook</a>.</p>
  </section>"""
    return page(f"About | {SITE['site_name']}",
                f"About {SITE['teacher_name']} — Chinese teacher.", body)


def main():
    texts = []
    tdir = os.path.join(ROOT, "content", "texts")
    for f in sorted(os.listdir(tdir)):
        if f.endswith(".json"):
            texts.append(json.load(open(os.path.join(tdir, f), encoding="utf-8")))

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "texts"))
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(build_index(texts))
    open(os.path.join(OUT, "about.html"), "w", encoding="utf-8").write(build_about())
    open(os.path.join(OUT, "words.html"), "w", encoding="utf-8").write(build_words(texts))
    open(os.path.join(OUT, "wordbook.html"), "w", encoding="utf-8").write(build_wordbook())
    for f in ("manifest.webmanifest", "sw.js"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))
    for t in texts:
        open(os.path.join(OUT, "texts", f"{t['slug']}.html"), "w",
             encoding="utf-8").write(build_reader(t))
    print(f"built {len(texts)} readings + words/wordbook -> docs/")


if __name__ == "__main__":
    main()
