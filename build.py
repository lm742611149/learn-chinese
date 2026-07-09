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
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="brand" href="{rel}index.html"><span class="seal">读</span>{name}</a>
    <nav>
      <a href="{rel}index.html">Readings</a>
      <a href="{rel}about.html">About</a>
      <a href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">Facebook</a>
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
{SITE.get("analytics_snippet", "")}
</body>
</html>"""


def sentence_html(sent):
    """Chinese line with ruby pinyin + tappable words + a play button."""
    parts, say = [], []
    for tok in sent["t"]:
        if len(tok) == 1:  # punctuation
            parts.append(f'<span class="punct">{esc(tok[0])}</span>')
            say.append(tok[0])
        else:
            zh, py, en = tok
            say.append(zh)
            parts.append(
                f'<span class="w" data-zh="{esc(zh)}" data-py="{esc(py)}" '
                f'data-en="{esc(en)}"><ruby>{esc(zh)}<rt>{esc(py)}</rt></ruby></span>')
    say_txt = esc("".join(say))
    return (f'<div class="sent">'
            f'<div class="zh-line" data-say="{say_txt}">{"".join(parts)}'
            f'<button class="s-play" data-say="{say_txt}" title="Play sentence">🔊</button></div>'
            f'<div class="en-line">{esc(sent["en"])}</div></div>')


def build_reader(t):
    n_words = sum(len(s["t"]) for s in t["sentences"])
    minutes = max(1, round(n_words / 60))
    body_sents = "\n".join(sentence_html(s) for s in t["sentences"])
    vocab_rows = "\n".join(
        f'<tr><td class="zh">{esc(z)}</td><td class="py">{esc(p)}</td>'
        f'<td>{esc(e)}</td>'
        f'<td class="play"><button class="s-play" data-say="{esc(z)}">🔊</button></td></tr>'
        for z, p, e in t["vocab"])
    body = f"""
  <article>
    <div class="reader-head">
      <span class="badge l{t['level']}">HSK {t['level']}</span>
      <h1>{esc(t['title_zh'])}</h1>
      <div class="py">{esc(t['title_py'])}</div>
      <div class="en">{esc(t['title_en'])} · ~{minutes} min read</div>
    </div>
    <div class="toolbar">
      <button class="tbtn" id="t-pinyin">拼音 Pinyin</button>
      <button class="tbtn" id="t-en">🌐 English</button>
      <button class="tbtn" id="t-play">▶ Play all</button>
      <button class="tbtn" id="t-speed">🐢 Slow</button>
      <select class="tbtn" id="t-voice" title="Choose voice"></select>
    </div>
    <div class="text-body">
{body_sents}
    </div>
    <div class="notice">🔊 Audio uses your device's Chinese voice for now —
      teacher recordings are coming. Tap any word to see its meaning.</div>
    <section class="vocab">
      <h2>Key words 生词</h2>
      <table>{vocab_rows}</table>
    </section>
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
        cards.append(f"""
    <a class="card" data-l="{t['level']}" href="texts/{t['slug']}.html">
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
        <h1>Read real Chinese,<br>one <span class="zh">短文</span> at a time.</h1>
        <p>Pinyin, tap-to-translate and audio in every reading. Free forever.</p>
        <a class="cta" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">
          Follow the daily lessons →</a>
      </div>
{featured_slides}
    </div>
    <div class="dots" id="hero-dots">{dots}</div>
  </section>
  <div class="levels"><div class="seg">{''.join(chips)}</div></div>
  <section class="cards">{''.join(cards)}
  </section>"""
    return page(f"{SITE['site_name']} — Free graded Chinese readings (HSK 1-6)",
                SITE["description"], body)


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
    for t in texts:
        open(os.path.join(OUT, "texts", f"{t['slug']}.html"), "w",
             encoding="utf-8").write(build_reader(t))
    print(f"built {len(texts)} readings -> docs/")


if __name__ == "__main__":
    main()
