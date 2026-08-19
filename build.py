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
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
SITE_PATH = os.path.join(ROOT, "content", "site.json")
SITE = json.load(open(SITE_PATH, encoding="utf-8"))

LEVEL_WORDS = {1: "Newbie", 2: "Elementary", 3: "Intermediate",
               4: "Upper Int.", 5: "Advanced", 6: "Fluent"}
LEVEL_COLORS = {1: "#3e9464", 2: "#2f7fa8", 3: "#7b5fc0",
                4: "#cf7622", 5: "#c73e2a", 6: "#6d4434"}
LEVEL_ZH = {1: "入门", 2: "基础", 3: "进阶", 4: "提高", 5: "高级", 6: "精通"}
LEVEL_NUM_ZH = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}

# Per-level page copy. Level pages target the head terms ("HSK 3 reading
# practice"), and a page that is only a card grid is thin for those. Each entry
# gives the page real substance plus an FAQ block that also ships as FAQPage
# JSON-LD. Word counts are the cumulative HSK 2.0 vocabulary targets.
LEVEL_SEO = {
    1: {
        "vocab": 150, "cefr": "A1",
        "covers": "greetings, family, numbers, time, weather, food and simple shopping",
        "grammar": "basic subject-verb-object order, 是 sentences, 有 for existence, "
                   "and question words like 什么 and 哪儿",
        "shape": "4-6 short sentences",
        "faq": [
            ("How many Chinese words do you need for HSK 1?",
             "150 words. That is small enough to finish in a few weeks, and it is "
             "enough to read about yourself, your family, your day and simple "
             "shopping — which is exactly what these readings cover."),
            ("Can I read these if I don't know any characters yet?",
             "Yes. Every character carries pinyin above it, and tapping any word "
             "shows its meaning and plays the audio. Most learners start by leaning "
             "on the pinyin and find they need it less after ten or fifteen texts."),
            ("How long does HSK 1 take?",
             "At 20-30 minutes a day, most learners reach HSK 1 in two to three "
             "months. Reading one short text daily is the part people skip, and it "
             "is the part that makes the vocabulary stick."),
        ],
    },
    2: {
        "vocab": 300, "cefr": "A2",
        "covers": "getting around, ordering food, shopping, health, hobbies and making plans",
        "grammar": "the particle 了 for completed actions, modal verbs like 会 and 能, "
                   "comparisons with 比, and time-then-verb word order",
        "shape": "5-7 sentences",
        "faq": [
            ("What is the difference between HSK 1 and HSK 2?",
             "HSK 2 doubles the vocabulary to 300 words and adds the grammar you need "
             "to talk about the past and the future — 了, 要, 想, and comparisons. "
             "Sentences get longer, but the structures stay simple."),
            ("Is HSK 2 enough to talk to people in China?",
             "It is enough for transactions: ordering, buying, asking directions, "
             "small talk about weather and family. It is not yet enough to follow a "
             "conversation between two native speakers."),
            ("Should I finish all HSK 1 readings first?",
             "No need to finish all of them, but the HSK 2 texts assume you are "
             "comfortable with the HSK 1 words. If a text feels slow, drop back a "
             "level for a week — reading below your level is how you build speed."),
        ],
    },
    3: {
        "vocab": 600, "cefr": "B1",
        "covers": "work, study, travel, health, relationships and cultural topics like festivals",
        "grammar": "resultative and directional complements, 把 sentences, 因为…所以…, "
                   "and 虽然…但是… for linking ideas across a paragraph",
        "shape": "6-8 sentences with a beginning, middle and end",
        "faq": [
            ("Is HSK 3 the hardest jump?",
             "Most learners say yes. The vocabulary doubles to 600 words, but the real "
             "shift is structural: sentences start carrying complements and linking "
             "words, so meaning is spread across a clause instead of sitting in one verb."),
            ("What does HSK 3 let me do?",
             "Handle most situations that come up while travelling or working in China, "
             "and read short texts on familiar topics without a dictionary for every line."),
            ("How do I stop translating in my head?",
             "Re-read. Take a text you already understand and read it again out loud "
             "until it flows. Understanding a sentence and reading it fluently are "
             "different skills, and only the second one survives a real conversation."),
        ],
    },
    4: {
        "vocab": 1200, "cefr": "B2",
        "covers": "opinions, work culture, technology, city life, travel and light social commentary",
        "grammar": "abstract connectives such as 不但…而且…, 无论…都…, 尽管, plus the "
                   "first four-character idioms (成语) in ordinary use",
        "shape": "6-9 sentences that argue a point rather than just narrate",
        "faq": [
            ("What level is HSK 4 in real terms?",
             "Roughly CEFR B2. With 1,200 words you can discuss a topic, give reasons "
             "for an opinion and follow most everyday conversation, though news and "
             "TV drama still move too fast."),
            ("Do I need to learn 成语 at HSK 4?",
             "A handful, yes. The exam includes common ones and native speakers use "
             "them constantly in ordinary speech. Learn them the way you meet them "
             "here — inside a sentence, not from a list."),
            ("How is HSK 4 reading different from HSK 3?",
             "The texts stop being pure narration. They compare, qualify and conclude, "
             "which means the connective words carry as much meaning as the nouns do."),
        ],
    },
    5: {
        "vocab": 2500, "cefr": "C1",
        "covers": "society, economy, technology, education, tradition and modern change",
        "grammar": "written-register patterns, 之所以…是因为…, 与其…不如…, dense noun "
                   "phrases, and idioms used precisely rather than decoratively",
        "shape": "7-10 sentences in an essay register, built around one concrete example",
        "faq": [
            ("Is HSK 5 enough to study at a Chinese university?",
             "It is the usual minimum for undergraduate admission, often alongside HSK 6 "
             "for competitive programmes. Reading speed matters more than the certificate: "
             "lectures assume you can process written Chinese without subvocalising."),
            ("Why does HSK 5 feel so much harder than HSK 4?",
             "The vocabulary doubles again, and the register changes. HSK 5 texts are "
             "written Chinese, not spoken Chinese written down — shorter sentences carry "
             "more information and drop the connective padding."),
            ("How many new words should I add a day?",
             "Fifteen to twenty is sustainable at this level, and only if you meet each "
             "one in context several times. Reading one text a day gives you that "
             "repetition without a separate flashcard session."),
        ],
    },
    6: {
        "vocab": 5000, "cefr": "C2",
        "covers": "philosophy, science, culture, language itself, and arguments that turn "
                  "on a distinction rather than a fact",
        "grammar": "classical residue in modern writing (以, 而, 之), tightly compressed "
                   "clauses, and idioms and allusions used as shorthand for a whole argument",
        "shape": "7-10 sentences of genuine commentary, with a thesis and a counterpoint",
        "faq": [
            ("What can you actually do with HSK 6?",
             "Read newspapers, essays and most non-technical books; follow lectures and "
             "debates; work in Chinese. It is the top level of the old HSK, but it is a "
             "floor for professional use, not a ceiling."),
            ("How do I keep improving after HSK 6?",
             "Stop studying Chinese and start using it for something else — read about a "
             "field you care about, in Chinese. At this level, breadth of subject matter "
             "does more than another vocabulary list."),
            ("Are these texts as hard as the real HSK 6 exam?",
             "Comparable in vocabulary and register, shorter in length. Exam passages run "
             "much longer and test endurance as much as comprehension, so treat these as "
             "daily maintenance rather than a mock exam."),
        ],
    },
}


def card_html(t, lesson_no=None):
    """Reading card. lesson_no -> course-style 'Lesson N' chip instead of the
    (redundant on a level page) HSK badge."""
    n_words = sum(len(s["t"]) for s in t["sentences"])
    blob = " ".join([t["title_zh"], t["title_py"], t["title_en"]] +
                    [w[0] + " " + w[1] + " " + w[2] for w in t["vocab"]]).lower()
    chip = (f'<span class="badge l{t["level"]}">Lesson {lesson_no}</span>'
            if lesson_no else
            f'<span class="badge l{t["level"]}">HSK {t["level"]}</span>')
    return f"""
    <a class="card" data-l="{t['level']}" data-search="{esc(blob)}" href="texts/{t['slug']}.html">
      <div class="tile">{esc(t['title_zh'][0])}</div>
      <div class="card-main">
        <div class="zh-title">{esc(t['title_zh'])}</div>
        <div class="py-title">{esc(t['title_py'])}</div>
        <div class="en-title">{esc(t['title_en'])}</div>
        <div class="meta">{chip}
          <span>{n_words} words</span><span class="go">读 →</span></div>
      </div>
    </a>"""


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, desc, body, rel="", path=None, noindex=False, ld=None):
    """rel  = prefix to reach site root ('' at root, '../' inside texts/).
    path = this page's path from site root ('' for home), used for canonical
           + og:url. None = skip those tags.
    ld   = list of schema.org dicts emitted as JSON-LD."""
    name = esc(SITE["site_name"])
    fb = SITE.get("firebase") or {}
    auth_btn = ('<button class="nav-link" id="t-auth">Sign in</button>'
                if fb else "")
    canon = (SITE.get("canonical_url") or "").rstrip("/")
    redir = ""
    if canon:
        redir = ('<script>if(location.hostname.endsWith("github.io")){location.replace("'
                 + canon
                 + '"+location.pathname.replace(/^\\/learn-chinese/,"")'
                 + '+location.search+location.hash)}</script>')
    seo = ""
    if canon and path is not None:
        url = canon + "/" + path
        seo = (f'<link rel="canonical" href="{esc(url)}">\n'
               f'<meta property="og:url" content="{esc(url)}">\n'
               f'<meta property="og:type" content="website">\n'
               f'<meta property="og:site_name" content="{name}">\n'
               f'<meta property="og:image" content="{esc(canon)}/assets/og-cover.png">\n'
               f'<meta name="twitter:card" content="summary_large_image">\n')
    if noindex:
        seo += '<meta name="robots" content="noindex,follow">\n'
    for block in (ld or []):
        seo += ('<script type="application/ld+json">'
                + json.dumps(block, ensure_ascii=False) + '</script>\n')
    providers = SITE.get("auth_providers", ["google"])
    auth_js = (f'<script>window.RCD_FB={json.dumps(fb)};'
               f'window.RCD_PROVIDERS={json.dumps(providers)};</script>\n'
               f'<script type="module" src="{rel}assets/auth.js"></script>'
               if fb else "")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
{redir}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{seo}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%23c73e2a'/><text x='50' y='72' font-size='62' text-anchor='middle' fill='white' font-family='serif' font-weight='bold'>读</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700;900&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700;900&display=swap"></noscript>
<link rel="stylesheet" href="{rel}assets/style.css">
<link rel="alternate" type="application/rss+xml" title="{name} — new readings" href="{rel}rss.xml">
<link rel="manifest" href="{rel}manifest.webmanifest">
<link rel="apple-touch-icon" href="{rel}assets/icon-180.png">
<meta name="theme-color" content="#c73e2a">
<script>try{{if(localStorage.getItem("rcd-theme")==="dark")document.documentElement.setAttribute("data-theme","dark");if(localStorage.getItem("rcd-auth"))document.documentElement.setAttribute("data-auth","1")}}catch(e){{}}</script>
</head>
<body data-audio-base="{rel}audio/">
<div class="wrap">
  <header class="top">
    <a class="brand" href="{rel}index.html"><span class="seal">读</span><span class="bname">{name}</span></a>
    <button class="nav-burger" id="nav-burger" aria-label="Menu">☰</button>
    <nav class="nav-menu" id="nav-menu">
      <button class="nav-close" id="nav-close" aria-label="Close">✕</button>
      <div class="menu-head"><span class="mh-seal">读</span>
        <div class="mh-t"><b>{name}</b><i>Real Chinese, 5 min a day</i></div></div>
      {auth_btn}
      <div class="menu-sec">Learn</div>
      <a class="nav-link" href="{rel}words.html"><span class="ni">📖</span><span class="nl"> Words</span></a>
      <a class="nav-link" href="{rel}grammar.html"><span class="ni">🧩</span><span class="nl"> Grammar</span></a>
      <a class="nav-link" href="{rel}wordbook.html" title="My wordbook"><span class="ni">⭐</span><span class="nl"> My Wordbook</span></a>
      <a class="nav-link" href="{rel}progress.html" title="My progress"><span class="ni">🏆</span><span class="nl"> Progress</span></a>
      <div class="menu-sec">More</div>
      <button class="nav-link" id="t-theme" title="Dark mode"><span class="ni" id="t-theme-i">🌙</span><span class="nl"> Dark mode</span></button>
      <a class="nav-link" href="{rel}about.html"><span class="ni">👋</span><span class="nl"> About</span></a>
      <a class="nav-cta nav-cta-book" href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M12 3 2 8l10 5 8-4v6h2V8L12 3zM6 12.2V16c0 1.7 2.7 3 6 3s6-1.3 6-3v-3.8l-6 3-6-3z"/></svg>
        <span class="nc-t">Book a lesson</span></a>
      <a class="nav-cta" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M13.4 21v-8.2h2.8l.4-3.2h-3.2V7.5c0-.9.3-1.6 1.7-1.6h1.7V3.1c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.3v3.2h2.8V21h3.3z"/></svg>
        <span class="nc-t">Follow</span></a>
    </nav>
    <div class="nav-backdrop" id="nav-backdrop"></div>
  </header>
{body}
  <footer class="footer">
    <div>© {name} · Original graded readings, free to read.</div>
    <div style="margin-top:6px">
      <a href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">Facebook</a>
      <a href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a lesson</a>
      <a href="{rel}about.html">About</a>
      <a href="{rel}rss.xml">RSS</a>
    </div>
  </footer>
</div>
<div id="pop"></div>
<script src="{rel}assets/reader.js"></script>
<script>if("serviceWorker" in navigator)navigator.serviceWorker.register("{rel}sw.js");</script>
{auth_js}
{SITE.get("analytics_snippet", "")}
</body>
</html>"""


OPENING_PUNCT = set("“‘(《【〈「『")


def sentence_html(sent, slug=None, idx=None):
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
    audio = (f' data-audio="../audio/{slug}/{idx}.mp3"'
             if slug is not None and idx is not None else "")
    return (f'<div class="sent">'
            f'<div class="zh-line" data-say="{say_txt}"{audio}>{parts}'
            f'<button class="s-play" data-say="{say_txt}"{audio} title="Play sentence">🔊</button></div>'
            f'<div class="en-line">{esc(sent["en"])}</div></div>')


def reader_desc(t, limit=158):
    """课文页 meta description: 用课文开头的英译当摘要,每篇独一无二。

    模板化的描述 255 篇长得一模一样,搜索结果里没有点击理由,也白白丢掉长尾词。
    """
    tail = f" — HSK {t['level']} graded reading with pinyin & audio."
    room = limit - len(tail)
    body = ""
    for s in t["sentences"]:
        nxt = (body + " " + s["en"]).strip()
        if body and len(nxt) > room:
            break
        body = nxt
        if len(body) >= room * 0.6:      # 够长了就停,避免整篇塞进去
            break
    if len(body) > room:                 # 首句就超长 → 切到词边界
        body = body[:room].rsplit(" ", 1)[0].rstrip(",;:.") + "…"
    return body + tail


def build_reader(t, next_t=None):
    n_words = sum(len(s["t"]) for s in t["sentences"])
    minutes = max(1, round(n_words / 60))
    body_sents = "\n".join(sentence_html(s, t["slug"], i) for i, s in enumerate(t["sentences"]))
    vocab_rows = "\n".join(
        f'<div class="vitem"><button class="s-play" data-say="{esc(z)}">🔊</button>'
        f'<div class="vtext"><span class="vzh">{esc(z)}</span>'
        f'<span class="vpy">{esc(p)}</span>'
        f'<span class="ven">{esc(e)}</span></div></div>'
        for z, p, e in t["vocab"])

    grammar_html = ""
    if t.get("grammar"):
        gitems = "".join(
            f'<div class="gitem"><div class="gp">{esc(g.get("p", ""))}</div>'
            f'<p>{esc(g.get("e", ""))}</p>'
            + (f'<div class="gx">{esc(g["x"])}</div>' if g.get("x") else "")
            + '</div>'
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
    if next_t:
        nxt = {"url": f"{next_t['slug']}.html", "zh": next_t["title_zh"],
               "en": next_t["title_en"], "lvl": next_t["level"]}
        next_js = f'<script>window.RCD_NEXT={json.dumps(nxt, ensure_ascii=False)};</script>'
        next_foot = (f'<a class="tbtn" href="{nxt["url"]}">Next: {esc(nxt["zh"])} →</a>')
    else:
        next_js, next_foot = "", ""
    body = f"""
  <article class="reading" style="--sc:{LEVEL_COLORS[t['level']]}">
    <div class="reader-banner" data-char="{esc(t['title_zh'][0])}">
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
      <select class="tb-rate" id="t-speed" title="Playback speed" aria-label="Playback speed">
        <option value="0.5">0.5×</option><option value="0.6">0.6×</option>
        <option value="0.7">0.7×</option><option value="0.8">0.8×</option>
        <option value="0.9">0.9×</option><option value="1" selected>1×</option>
        <option value="1.25">1.25×</option>
      </select>
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
    <section class="book-cta">
      <img class="bc-photo" src="../assets/teacher.jpg"
           alt="{esc(SITE['teacher_name'])} — Mandarin teacher"
           width="88" height="88" loading="lazy" decoding="async">
      <div class="bc-body">
        <div class="bc-eyebrow">After this reading</div>
        <h2>Reading is the easy part. Speaking is where you get stuck.</h2>
        <p>I'm {esc(SITE['teacher_name'])}, and I teach Mandarin one-on-one on Preply.
          Bring this text to a trial lesson — we'll fix your tones and turn it
          into a real conversation.</p>
        <a class="bc-btn" href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a trial lesson →</a>
      </div>
    </section>
    <div class="reader-foot">
      <a class="tbtn" href="../hsk{t['level']}.html">← HSK {t['level']} readings</a>
      {next_foot}
      <a class="nav-cta" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M13.4 21v-8.2h2.8l.4-3.2h-3.2V7.5c0-.9.3-1.6 1.7-1.6h1.7V3.1c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.3v3.2h2.8V21h3.3z"/></svg>
        Follow for daily lessons</a>
    </div>
  </article>
{next_js}"""
    # 不带站名 —— 中文标题占的显示宽度大,加站名会被搜索结果截断
    title = f"{t['title_zh']} {t['title_en']} — HSK {t['level']} Reading"
    desc = reader_desc(t)
    base = (SITE.get("canonical_url") or "").rstrip("/")
    ld = [{
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": f"{t['title_zh']} — {t['title_en']}",
        "url": f"{base}/texts/{t['slug']}",
        "inLanguage": "zh-CN",
        "learningResourceType": "graded reading",
        "educationalLevel": f"HSK {t['level']}",
        "teaches": ", ".join(w[0] for w in t["vocab"]),
        "timeRequired": f"PT{max(1, minutes)}M",
        "isAccessibleForFree": True,
        "inDefinedTermSet": "HSK (Chinese Proficiency Test)",
        "author": {"@type": "Person", "name": SITE["teacher_name"]},
        "publisher": {"@type": "Organization", "name": SITE["site_name"],
                      "url": base or None},
    }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["site_name"],
             "item": f"{base}/"},
            {"@type": "ListItem", "position": 2,
             "name": f"HSK {t['level']} — {LEVEL_WORDS[t['level']]}",
             "item": f"{base}/hsk{t['level']}"},
            {"@type": "ListItem", "position": 3, "name": t["title_en"]},
        ],
    }]
    return page(title, desc, body, rel="../",
                path=f"texts/{t['slug']}", ld=ld)


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
    counts = {}
    for t in texts:
        counts[t["level"]] = counts.get(t["level"], 0) + 1
    lvlcards = []
    for i in range(1, 7):
        n = counts.get(i, 0)
        lvlcards.append(f"""
    <a class="lvlcard" href="hsk{i}.html" style="--sc:{LEVEL_COLORS[i]}" data-l="{i}" data-n="{n}">
      <div class="lv-top"><span class="lv-tag">HSK {i}</span>
        <span class="lv-zh">{LEVEL_ZH[i]}</span></div>
      <div class="lv-name">{LEVEL_WORDS[i]}</div>
      <div class="lv-meta"><span class="lv-done">{n} readings</span><span class="lv-go">→</span></div>
      <div class="lv-bar"><i></i></div>
    </a>""")
    all_cards = "".join(card_html(t) for t in
                        sorted(texts, key=lambda x: (x["level"], x["slug"])))
    levels_map = {t["slug"]: t["level"] for t in texts}
    recent = sorted(texts, key=lambda x: (-x.get("_mtime", 0), x["slug"]))[:6]
    latest_cards = "".join(card_html(t) for t in recent)
    n_words = len({w[0] for t in texts for w in t["vocab"]})
    n_chars = len({c for t in texts for s in t["sentences"]
                   for w in s["t"] for c in w[0]
                   if "一" <= c <= "鿿"})
    faqs = [
        ("What is HSK?",
         "HSK (汉语水平考试) is the official Chinese proficiency test. Levels 1 to 6 "
         "run from roughly 150 words up to 5,000+. Every reading here is graded to "
         "one of those levels, so the vocabulary and grammar stay inside the range "
         "you're actually studying."),
        ("Which level should I start with?",
         "If you're new to Chinese, start at HSK 1 — the readings are short and use "
         "the most common characters. If you can already read a menu or a text "
         "message, try HSK 3. Nothing is locked, so you can switch levels any time."),
        ("Is it really free?",
         "Yes. Every reading, the audio, the pinyin and the tap-to-translate lookups "
         "are free, and you don't need an account. I teach paid one-on-one lessons "
         "on Preply — that's what pays for this site."),
        ("Do I need to sign up?",
         "No. Sign in only if you want your wordbook and reading streak to follow you "
         "across devices."),
        ("How long does it take to see progress?",
         "Most students who read one text a day notice a difference in about a month "
         "— not because a month is magic, but because daily short reading beats a "
         "three-hour session once a week."),
        ("Can I practise with a real teacher?",
         "Yes. Reading builds vocabulary quickly, but speaking needs a person on the "
         "other side. Bring any reading from this site to a trial lesson and we'll "
         "work through it out loud."),
    ]
    faq_html = "".join(
        f"""
      <div class="faq-item">
        <h3>{esc(q)}</h3>
        <p>{esc(a)}</p>
      </div>""" for q, a in faqs)
    faq_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in faqs],
    }, ensure_ascii=False)
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
    placeholder="Search all readings — 汉字 / pinyin / English…" autocomplete="off"></div>
  <section class="today-wrap" id="today-wrap" hidden>
    <h2 class="home-h">Today's picks <span class="zh">今日推荐</span></h2>
    <div class="tstack" id="today-slot"></div>
    <div class="tdots" id="today-dots"></div>
  </section>
  <section class="lvlgrid" id="lvlgrid">{''.join(lvlcards)}
  </section>
  <section class="cards" id="search-results" hidden>{all_cards}
  </section>
  <section class="latest" id="latest-wrap">
    <h2 class="home-h">Just added <span class="zh">最新课文</span></h2>
    <div class="cards latest-cards">{latest_cards}</div>
    <a class="latest-more" href="words.html">Browse every word in the library →</a>
  </section>
  <section class="how" id="home-how">
    <h2 class="home-h">How it works <span class="zh">怎么用</span></h2>
    <ol class="how-list">
      <li>
        <div>
          <h3>Pick your level</h3>
          <p>HSK 1 to 6, each reading graded so the words stay inside what you're
            actually studying. Not sure? Start at HSK 1 and move up.</p>
        </div>
      </li>
      <li>
        <div>
          <h3>Read for five minutes</h3>
          <p>Tap any word for pinyin and meaning, play the audio to hear it,
            toggle the English when you want to check yourself.</p>
        </div>
      </li>
      <li>
        <div>
          <h3>Keep the new words</h3>
          <p>Star what's new and it goes to your wordbook for flashcard practice.
            Come back tomorrow — the streak does the rest.</p>
        </div>
      </li>
    </ol>
  </section>
  <section class="faq" id="home-faq">
    <h2 class="home-h">Common questions <span class="zh">常见问题</span></h2>
    <div class="faq-grid">{faq_html}
    </div>
  </section>
  <script type="application/ld+json">{faq_ld}</script>
  <section class="book-cta">
    <img class="bc-photo" src="assets/teacher.jpg"
         alt="{esc(SITE['teacher_name'])} — Mandarin teacher"
         width="88" height="88" loading="lazy" decoding="async">
    <div class="bc-body">
      <div class="bc-eyebrow">Your teacher</div>
      <h2>I wrote all {len(texts)} readings on this site</h2>
      <p>你好! I'm {esc(SITE['teacher_name'])}. {esc(SITE['teacher_bio'])}</p>
      <a class="bc-btn" href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a trial lesson →</a>
      <a class="bc-alt" href="about.html">More about me →</a>
    </div>
  </section>
  <script>window.RCD_LEVELS={json.dumps(levels_map)};</script>"""
    base = (SITE.get("canonical_url") or "").rstrip("/")
    st = SITE.get("teacher_stats") or {}
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": SITE["teacher_name"],
        "jobTitle": "Mandarin teacher",
        "url": f"{base}/about",
        "image": f"{base}/assets/teacher.jpg",
        "sameAs": [SITE["preply_url"], SITE["facebook_url"]],
    }
    # No aggregateRating here, deliberately. Google's review-snippet feature
    # does not support Person as the reviewed item (GSC flagged it 2026-08-18),
    # and these numbers are Preply's, not ratings collected on this site —
    # marking up a third party's aggregate score is against the policy either
    # way. The figures still appear as plain text on /about, which is fine.
    ld = [{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE["site_name"],
        "url": f"{base}/",
        "description": SITE["description"],
        "inLanguage": "en",
        "author": {"@type": "Person", "name": SITE["teacher_name"]},
    }, person]
    return page(f"{SITE['site_name']} — Free graded Chinese readings (HSK 1-6)",
                SITE["description"], body, path="", ld=ld)


def build_level(texts, lvl):
    mine = [t for t in sorted(texts, key=lambda x: x["slug"])
            if t["level"] == lvl]
    counts = {}
    for t in texts:
        counts[t["level"]] = counts.get(t["level"], 0) + 1
    cards = "".join(card_html(t, i + 1) for i, t in enumerate(mine))
    chips = [f'<a class="lvl-chip" data-l="0" href="index.html">All</a>'] + [
        f'<a class="lvl-chip{" on" if i == lvl else ""}" data-l="{i}" '
        f'href="hsk{i}.html">HSK {i}<span class="n">{counts.get(i, 0)}</span></a>'
        for i in range(1, 7)]

    # Below-the-fold copy: the card grid alone is thin for "HSK N reading
    # practice", which is what this page is trying to rank for.
    s = LEVEL_SEO[lvl]
    new_words = s["vocab"] - (LEVEL_SEO[lvl - 1]["vocab"] if lvl > 1 else 0)
    scope = (f'a vocabulary of {s["vocab"]} words'if lvl == 1 else
             f'a cumulative vocabulary of {s["vocab"]} words — {new_words} new ones '
             f'on top of HSK {lvl - 1}')
    faq_html = "".join(
        f'<details class="faq-q"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
        for q, a in s["faq"])
    intro = f"""
    <section class="lvl-intro">
      <h2>What HSK {lvl} covers</h2>
      <p>HSK {lvl} works with {scope}, roughly CEFR {esc(s["cefr"])}. It covers
        {esc(s["covers"])}. The grammar that defines the level is
        {esc(s["grammar"])}.</p>
      <p>The {len(mine)} readings on this page are written for exactly that boundary.
        Every one is original — no textbook passages — and stays inside the HSK {lvl}
        word list; anything above the level is listed in the vocabulary panel under the
        text. Each is {esc(s["shape"])}, with pinyin over every character,
        tap-to-translate, audio you can slow down, a three-question comprehension check
        and a short grammar note.</p>
      <p class="lvl-how"><strong>A routine that works:</strong> read once without looking
        anything up, then tap the words you missed, then listen and read along a second
        time. Five minutes a day beats an hour on Sunday.</p>

      <h2>HSK {lvl} questions</h2>
      <div class="faq">{faq_html}</div>
    </section>"""
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[lvl]}" data-char="{LEVEL_NUM_ZH[lvl]}">
      <span class="feat-tag">HSK {lvl} · {LEVEL_WORDS[lvl]}</span>
      <h1>HSK {lvl} Readings <span class="lv-h-zh">{LEVEL_ZH[lvl]}</span></h1>
      <div class="b-en">{len(mine)} graded readings — read them in order, like a course.
        ✓ marks what you've finished.</div>
    </div>
    <div class="levels"><div class="seg"><span class="seg-ind"></span>{''.join(chips)}</div></div>
    <div class="searchbar"><input type="search" id="search"
      placeholder="Search HSK {lvl} readings…" autocomplete="off"></div>
    <section class="cards">{cards}
    </section>
{intro}
  </article>"""
    base = (SITE.get("canonical_url") or "").rstrip("/")
    ld = [{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["site_name"],
             "item": f"{base}/"},
            {"@type": "ListItem", "position": 2,
             "name": f"HSK {lvl} — {LEVEL_WORDS[lvl]}"},
        ],
    }, {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"HSK {lvl} graded Chinese readings",
        "numberOfItems": len(mine),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "url": f"{base}/texts/{x['slug']}",
             "name": f"{x['title_zh']} — {x['title_en']}"}
            for i, x in enumerate(mine)
        ],
    }, {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in s["faq"]
        ],
    }]
    return page(f"HSK {lvl} Reading Practice — {len(mine)} Free Graded Readings | {SITE['site_name']}",
                f"Free HSK {lvl} reading practice: {len(mine)} original graded texts inside "
                f"the {s['vocab']}-word HSK {lvl} list, with pinyin, audio, "
                f"tap-to-translate and quizzes.", body,
                path=f"hsk{lvl}", ld=ld)


def word_examples(texts, words):
    """{'s': sentence pool (each [tokenPairs, en, slug, title_zh]),
        'w': word -> {'ex': [pool indices ×≤2], 'us': [[pattern, expl]×≤2]}}
    Sentences are pooled once and referenced by index — embedding per-word
    HTML blew the JSON up to 1 MB; ruby markup is assembled client-side."""
    pool, pool_idx = [], {}
    occurs, us = {}, {}
    for t in texts:
        for s in t["sentences"]:
            toks = s["t"]
            plain = "".join(tok[0] for tok in toks)
            idx = pool_idx.get(plain)
            if idx is None:
                idx = len(pool)
                pool_idx[plain] = idx
                pool.append([[[x[0], x[1]] if len(x) == 3 else [x[0]]
                              for x in toks], s["en"], t["slug"], t["title_zh"]])
            seen = set()
            for tok in toks:
                if len(tok) == 3 and tok[0] in words and tok[0] not in seen:
                    seen.add(tok[0])
                    occurs.setdefault(tok[0], []).append((len(plain), idx))
        for g in t.get("grammar", []):
            for w in words:
                if w in g["p"] and len(us.get(w, [])) < 2 and \
                        not any(u[0] == g["p"] for u in us.get(w, [])):
                    us.setdefault(w, []).append([g["p"], g["e"]])
    perword = {}
    for w in words:
        picks = sorted(set(occurs.get(w, [])))[:2]   # shortest read easiest
        perword[w] = {"ex": [i for _, i in picks], "us": us.get(w, [])}
    return {"s": pool, "w": perword}


def collect_words(texts):
    """Every unique word across all readings, tagged with the level it first
    appears at."""
    words = {}
    for t in sorted(texts, key=lambda x: x["level"]):
        pool = [tok for s in t["sentences"] for tok in s["t"] if len(tok) == 3]
        pool += [list(v) for v in t["vocab"]]
        for zh, py, en in pool:
            if zh not in words:
                words[zh] = (t["level"], py, en)
    return words


def word_row(zh, lvl, py, en, wex, badge=True):
    blob = f"{zh} {py} {en}".lower()
    # detail content itself stays in word-examples.json and is built lazily on
    # tap — inlining it ballooned the page past 1 MB
    d = wex["w"].get(zh, {"ex": [], "us": []})
    has_d = bool(d["ex"] or d["us"])
    more = '<span class="vmore"></span>' if has_d else ""
    bdg = f'<span class="badge l{lvl}">HSK {lvl}</span>' if badge else ""
    return (f'<div class="vitem{" vx" if has_d else ""}" data-l="{lvl}" '
            f'data-search="{esc(blob)}">'
            f'<button class="s-play" data-say="{esc(zh)}">🔊</button>'
            f'<div class="vtext"><span class="vzh">{esc(zh)}</span>'
            f'<span class="vpy">{esc(py)}</span>{bdg}'
            f'<span class="ven">{esc(en)}</span></div>{more}'
            f'<button class="wstar" data-z="{esc(zh)}" data-p="{esc(py)}" '
            f'data-e="{esc(en)}" title="Save to wordbook">☆</button></div>')


def sec_chips(cur, base, home):
    """Level chips as real links — one URL per level, so each is indexable."""
    # data-l is required: reader.js applyFilters() reads it off the active chip,
    # and a missing attribute makes every row fail the level test.
    out = [f'<a class="lvl-chip{"" if cur else " on"}" data-l="0" '
           f'href="{home}">All</a>']
    out += [f'<a class="lvl-chip{" on" if i == cur else ""}" data-l="{i}" '
            f'href="{base}{i}.html">HSK {i}</a>' for i in range(1, 7)]
    return ('<div class="levels"><div class="seg"><span class="seg-ind"></span>'
            f'{"".join(out)}</div></div>')


def build_words_index(words):
    """Overview page. Deliberately does NOT inline the 5000-row list — that is
    what made words.html a 2.1 MB download."""
    counts = {i: sum(1 for z in words if words[z][0] == i) for i in range(1, 7)}
    cards = "".join(
        f'<a class="lvlcard" href="words-hsk{i}.html" style="--sc:{LEVEL_COLORS[i]}">'
        f'<div class="lv-top"><span class="lv-tag">HSK {i}</span>'
        f'<span class="lv-zh">{LEVEL_ZH[i]}</span></div>'
        f'<div class="lv-name">{LEVEL_WORDS[i]}</div>'
        f'<div class="lv-meta"><span class="lv-done">{counts[i]} words</span>'
        f'<span class="lv-go">→</span></div></a>'
        for i in range(1, 7))
    body = f"""
  <section class="about">
    <h1>Vocabulary <span style="font-family:var(--serif);color:var(--red)">词汇表</span></h1>
    <p>All {len(words)} words that appear across our graded readings, split by
      HSK level. Tap any word for real example sentences pulled from the texts,
      🔊 to hear it, ☆ to save it to your wordbook.</p>
    <p>These lists are built from the readings themselves — so
      every word here is one you will actually meet in a text on this site,
      not an abstract syllabus dump.</p>
  </section>
  {sec_chips(0, "words-hsk", "words.html")}
  <section class="lvlgrid">{cards}</section>"""
    return page(f"Chinese Vocabulary Lists by HSK Level (1-6) | {SITE['site_name']}",
                f"{len(words)} Chinese words with pinyin, audio and example "
                f"sentences, organised by HSK level 1 to 6.",
                body, path="words")


def build_words_level(words, wex, lvl):
    mine = sorted((z for z in words if words[z][0] == lvl),
                  key=lambda z: words[z][1].lower())
    rows = "".join(word_row(z, lvl, words[z][1], words[z][2], wex, badge=False)
                   for z in mine)
    cum = sum(1 for z in words if words[z][0] <= lvl)
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[lvl]}" data-char="{LEVEL_NUM_ZH[lvl]}">
      <span class="feat-tag">HSK {lvl} · {LEVEL_WORDS[lvl]}</span>
      <h1>HSK {lvl} Vocabulary <span class="lv-h-zh">{LEVEL_ZH[lvl]}词汇</span></h1>
      <div class="b-en">{len(mine)} words introduced at this level —
        {cum} cumulative from HSK 1 to {lvl}.</div>
    </div>
    {sec_chips(lvl, "words-hsk", "words.html")}
    <div class="searchbar"><input type="search" id="search"
      placeholder="Search HSK {lvl} words — 汉字 / pinyin / English…" autocomplete="off"></div>
    <div class="wlist">{rows}</div>
    <section class="lvl-intro">
      <h2>About this list</h2>
      <p>These {len(mine)} words are the ones that first appear at HSK {lvl} in our
        readings. Each row plays audio on 🔊, expands to show a real sentence from
        one of the texts, and saves to your wordbook on ☆.</p>
      <p>Words are listed alphabetically by pinyin. A word is filed at the level
        of the first reading it appears in, so a word you meet in an HSK {lvl}
        text but which also occurs later stays here rather than being repeated.</p>
      <p class="lvl-how"><strong>How to use it:</strong> don't study this list top
        to bottom. Read the <a href="hsk{lvl}.html">HSK {lvl} readings</a> first,
        then come here to review the words you tripped over.</p>
    </section>
  </article>"""
    return page(f"HSK {lvl} Vocabulary List — {len(mine)} Words with Pinyin & Audio | {SITE['site_name']}",
                f"Complete HSK {lvl} vocabulary list: {len(mine)} Chinese words with "
                f"pinyin, audio and example sentences from free graded readings.",
                body, path=f"words-hsk{lvl}")



def collect_grammar(texts):
    """791 grammar notes live inside the readings and nowhere else. Fold them
    into one index, keyed by pattern, each carrying the readings it appears in."""
    gram = {}
    for t in sorted(texts, key=lambda x: (x["level"], x["slug"])):
        for g in t.get("grammar", []):
            pat = (g.get("p") or "").strip()
            if not pat:
                continue
            e = gram.setdefault(pat, {"e": g.get("e", ""), "x": g.get("x", ""),
                                      "lvl": t["level"], "srcs": []})
            # keep the first explanation; later readings only add sources
            if not e["e"]:
                e["e"] = g.get("e", "")
            if not e["x"]:
                e["x"] = g.get("x", "")
            e["srcs"].append((t["slug"], t["title_zh"], t["title_en"]))
    return gram


def gram_item(pat, d, show_lvl=False):
    srcs = "".join(
        f'<a href="texts/{esc(slug)}.html">{esc(zh)}</a>'
        for slug, zh, en in d["srcs"][:4])
    extra = f' +{len(d["srcs"]) - 4}' if len(d["srcs"]) > 4 else ""
    bdg = (f'<span class="badge l{d["lvl"]}">HSK {d["lvl"]}</span>'
           if show_lvl else "")
    return (f'<div class="gitem">'
            f'<div class="gp">{esc(pat)}{bdg}</div>'
            f'<p>{esc(d["e"])}</p>'
            + (f'<div class="gx">{esc(d["x"])}</div>' if d["x"] else "")
            + f'<div class="g-src">Seen in {srcs}{extra}</div></div>')


def build_grammar_index(gram):
    counts = {i: sum(1 for k in gram if gram[k]["lvl"] == i) for i in range(1, 7)}
    cards = "".join(
        f'<a class="lvlcard" href="grammar-hsk{i}.html" style="--sc:{LEVEL_COLORS[i]}">'
        f'<div class="lv-top"><span class="lv-tag">HSK {i}</span>'
        f'<span class="lv-zh">{LEVEL_ZH[i]}</span></div>'
        f'<div class="lv-name">{LEVEL_WORDS[i]}</div>'
        f'<div class="lv-meta"><span class="lv-done">{counts[i]} patterns</span>'
        f'<span class="lv-go">→</span></div></a>'
        for i in range(1, 7))
    body = f"""
  <section class="about">
    <h1>Grammar <span style="font-family:var(--serif);color:var(--red)">语法点</span></h1>
    <p>{len(gram)} Chinese grammar patterns, each one taken from a reading on this
      site and shown with the sentence it came from. Split by HSK level.</p>
    <p>This is not a reference grammar. Every pattern here earned its place by
      turning up in a real text, and every entry links back to the reading it
      appeared in — so you can see it working before you try to use it.</p>
  </section>
  {sec_chips(0, "grammar-hsk", "grammar.html")}
  <section class="lvlgrid">{cards}</section>"""
    return page(f"Chinese Grammar Points by HSK Level (1-6) | {SITE['site_name']}",
                f"{len(gram)} Chinese grammar patterns with explanations and example "
                f"sentences from free graded readings, organised by HSK level.",
                body, path="grammar")


def build_grammar_level(gram, lvl):
    mine = sorted((k for k in gram if gram[k]["lvl"] == lvl), key=lambda k: k)
    items = "".join(gram_item(k, gram[k]) for k in mine)
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[lvl]}" data-char="{LEVEL_NUM_ZH[lvl]}">
      <span class="feat-tag">HSK {lvl} · {LEVEL_WORDS[lvl]}</span>
      <h1>HSK {lvl} Grammar <span class="lv-h-zh">{LEVEL_ZH[lvl]}语法</span></h1>
      <div class="b-en">{len(mine)} patterns, each with the reading it came from.</div>
    </div>
    {sec_chips(lvl, "grammar-hsk", "grammar.html")}
    <div class="gwrap">{items}</div>
    <section class="lvl-intro">
      <h2>How to use this page</h2>
      <p>Every pattern below was pulled out of an HSK {lvl} reading on this site.
        The example is the actual sentence it appeared in, and the links under it
        go to the readings where you can see it in context.</p>
      <p class="lvl-how"><strong>Grammar sticks through reading, not through lists.</strong>
        Skim this page to see what {LEVEL_SEO[lvl]["cefr"]}-level Chinese asks of you,
        then go read the <a href="hsk{lvl}.html">HSK {lvl} texts</a> and come back
        when a sentence confuses you.</p>
    </section>
  </article>"""
    return page(f"HSK {lvl} Grammar Points — {len(mine)} Patterns with Examples | {SITE['site_name']}",
                f"All {len(mine)} HSK {lvl} Chinese grammar patterns explained in English, "
                f"each with a real example sentence from a free graded reading.",
                body, path=f"grammar-hsk{lvl}")


def gated(inner, title_zh, blurb):
    """Members-only wrapper: lock panel shown until auth.js reveals content.
    No firebase configured -> page stays public (nothing to sign in with)."""
    if not (SITE.get("firebase") or {}):
        return inner
    return f"""
  <div class="gate" id="gate-panel">
    <div class="gate-seal">读</div>
    <h2>Sign in to unlock <span class="zh">{title_zh}</span></h2>
    <p>{blurb}</p>
    <button class="gate-btn" id="gate-signin">Sign in — it's free</button>
    <p class="gate-sub">Your words and streak sync to every device.</p>
  </div>
  <div id="gated" hidden>{inner}</div>"""


def build_wordbook():
    body = gated("""
  <section class="about">
    <h1>My Wordbook <span style="font-family:var(--serif);color:var(--red)">生词本</span></h1>
    <p>Words you saved with ☆ while reading. Stored on this device.</p>
  </section>
  <div class="wb-actions">
    <button class="tb-play" id="wb-practice">Practice flashcards</button>
  </div>
  <div class="wlist" id="wb-list">""" + '<div class="sk" style="height:64px"></div>' * 6 + """</div>
  <div class="deck" id="deck" hidden>
    <div class="deck-card" id="deck-card"></div>
    <div class="deck-btns">
      <button class="tbtn" id="deck-flip">Show answer</button>
      <button class="tbtn" id="deck-next">Next →</button>
      <button class="tbtn" id="deck-close">Done</button>
    </div>
  </div>""", "生词本",
        "Save words with ☆ while you read, then practice them as flashcards.")
    return page(f"My Wordbook | {SITE['site_name']}",
                "Your saved Chinese words with flashcard practice.", body,
                path="wordbook", noindex=True)


def build_progress(texts):
    totals, levels = {}, {}
    for t in texts:
        totals[t["level"]] = totals.get(t["level"], 0) + 1
        levels[t["slug"]] = t["level"]
    body = gated(f"""
  <section class="about" style="padding-bottom:10px">
    <h1>My Progress <span style="font-family:var(--serif);color:var(--red)">学习记录</span></h1>
    <p>Streak, badges and your reading calendar — synced to your account.</p>
  </section>
  <div class="acct" id="acct" hidden>
    <div class="acct-who">Signed in as <b id="acct-name">…</b></div>
    <button class="acct-out" id="acct-signout">Sign out</button>
  </div>
  <div class="pg-stats" id="pg-stats">{'<div class="sk" style="height:92px"></div>' * 4}</div>
  <section class="pgsec">
    <h2>Badges <span class="zh">徽章</span></h2>
    <div class="badges" id="pg-badges">{'<div class="sk" style="height:96px"></div>' * 6}</div>
  </section>
  <section class="pgsec">
    <h2>Reading calendar <span class="zh">打卡日历</span></h2>
    <div class="cal" id="pg-cal"><div class="sk" style="height:280px"></div></div>
  </section>""", "学习记录",
        "Track your streak, earn badges and fill your reading calendar.") + f"""
  <script>window.RCD_LEVELS={json.dumps(levels)};window.RCD_TOTALS={json.dumps(totals)};</script>"""
    return page(f"My Progress | {SITE['site_name']}",
                "Your Chinese reading streak, badges and check-in calendar.", body,
                path="progress", noindex=True)


def build_about(texts):
    st = SITE.get("teacher_stats") or {}
    stats = ""
    if st:
        stats = f"""
    <div class="ab-stats">
      <div class="ab-stat"><b>{esc(st.get('rating', ''))}</b><span>rating on Preply</span></div>
      <div class="ab-stat"><b>{esc(st.get('reviews', ''))}</b><span>student reviews</span></div>
      <div class="ab-stat"><b>{esc(st.get('lessons', ''))}</b><span>lessons taught</span></div>
    </div>"""
    body = f"""
  <section class="about">
    <div class="teacher-card">
      <img class="teacher-photo" src="assets/teacher.jpg"
           alt="{esc(SITE['teacher_name'])} — Mandarin teacher"
           width="132" height="132" decoding="async">
      <div class="teacher-meta">
        <h1>你好! I'm {esc(SITE['teacher_name'])}</h1>
        <p class="teacher-role">{esc(SITE.get('teacher_role', 'Mandarin teacher on Preply'))}</p>
        <a class="teacher-cta" href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a trial lesson →</a>
      </div>
    </div>
{stats}
    <div class="ab-sec">
      <h2>How I teach <span class="zh">我的课</span></h2>
      <p>My lessons don't run on rote memorisation. I use real-life examples and
        throw in a joke here and there, so you're learning in a relaxed
        atmosphere instead of reciting lists.</p>
      <p>Language isn't only memory — it's understanding and use. So the lessons
        are interactive and practical, built to get you speaking with confidence
        rather than collecting vocabulary you never say out loud.</p>
    </div>
    <div class="ab-sec">
      <h2>Background <span class="zh">我的背景</span></h2>
      <ul class="ab-list">
        <li><b>HSK 5 and HSKK Advanced</b> — solid listening, speaking, reading
          and writing, tested rather than claimed.</li>
        <li><b>Beijing Language University</b> — where I'm studying Chinese
          language and culture now.</li>
        <li><b>Four years teaching English</b> to Chinese children, so I'm used
          to learners of very different ages and starting points.</li>
        <li><b>Chinese, English and Filipino</b> — and I'm still learning
          languages myself, so I know exactly where it gets hard.</li>
      </ul>
      <p class="ab-aside">Off the clock: Muay Thai, swimming, skiing and
        shooting. Staying active is where the energy and the patience for
        teaching come from.</p>
    </div>
    <div class="ab-sec">
      <h2>Why this site exists <span class="zh">为什么做这个站</span></h2>
      <p>Textbooks hand you word lists. Conversation gives you speed. What's
        missing in between is <strong>reading you can actually finish</strong> —
        short, graded, and pitched at the level you're on right now.</p>
      <p>So I write them. All {len(texts)} readings here are original, graded to
        real HSK levels, and free — pinyin, audio and tap-to-translate on every
        word, no account needed.</p>
    </div>
    <div class="ab-cta">
      <h2>Start with a trial lesson</h2>
      <p>We'll talk about what you want to do in Chinese and work out how to get
        there step by step. Bring any reading from this site and we'll go
        through it out loud.</p>
      <a class="bc-btn" href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a trial lesson →</a>
      <a class="bc-alt" href="{esc(SITE['facebook_url'])}" target="_blank" rel="noopener">Daily lessons on Facebook →</a>
    </div>
  </section>"""
    return page(f"About | {SITE['site_name']}",
                f"About {SITE['teacher_name']} — Chinese teacher.", body,
                path="about")


def build_rss(texts):
    """最近 30 篇,按加入时间倒序。日期用文件 mtime —— 内容本身没有发布日期。"""
    import email.utils
    base = (SITE.get("canonical_url") or "").rstrip("/")
    recent = sorted(texts, key=lambda x: -x.get("_mtime", 0))[:30]
    items = []
    for t in recent:
        n_words = sum(len(s["t"]) for s in t["sentences"])
        preview = "".join(w[0] for w in t["sentences"][0]["t"])
        desc = (f"HSK {t['level']} · {n_words} words. {esc(preview)} "
                f"— {esc(t['title_en'])}. Pinyin, audio and English included.")
        items.append(f"""  <item>
    <title>{esc(t['title_zh'])} — {esc(t['title_en'])} (HSK {t['level']})</title>
    <link>{base}/texts/{t['slug']}</link>
    <guid isPermaLink="true">{base}/texts/{t['slug']}</guid>
    <description>{desc}</description>
    <category>HSK {t['level']}</category>
    <pubDate>{email.utils.formatdate(t.get('_mtime', 0), usegmt=True)}</pubDate>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(SITE['site_name'])}</title>
  <link>{base}/</link>
  <atom:link href="{base}/rss.xml" rel="self" type="application/rss+xml"/>
  <description>{esc(SITE['description'])}</description>
  <language>en</language>
{chr(10).join(items)}
</channel>
</rss>
"""


def build_404():
    """CF Pages 自动用 docs/404.html 兜底,并返回真正的 404 状态码。
    rel='/' -> 资源走绝对路径,因为 404 可能在任意深度被触发。"""
    body = """
  <section class="about" style="text-align:center; padding:72px 0 84px">
    <div style="font-family:var(--serif); font-size:6rem; font-weight:900;
      color:var(--red); opacity:.2; line-height:1; user-select:none">读</div>
    <h1 style="margin-top:8px">This page doesn't exist</h1>
    <p>The link may be out of date, or the address has a typo.
      All 225 readings are still here — pick a level and keep going.</p>
    <div style="margin-top:24px">
      <a class="bc-btn" href="/">Back to the readings →</a>
      <a class="bc-alt" href="/words">Browse the word list →</a>
    </div>
  </section>"""
    return page(f"Page not found | {SITE['site_name']}",
                "This page does not exist on Read Mandarin.", body,
                rel="/", noindex=True)


def main():
    texts = []
    tdir = os.path.join(ROOT, "content", "texts")
    for f in sorted(os.listdir(tdir)):
        if f.endswith(".json"):
            fp = os.path.join(tdir, f)
            t = json.load(open(fp, encoding="utf-8"))
            t["_mtime"] = os.path.getmtime(fp)   # 用于首页"最新课文"排序
            texts.append(t)

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "texts"))
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    media_audio = os.path.join(ROOT, "media", "audio")
    if os.path.isdir(media_audio):
        shutil.copytree(media_audio, os.path.join(OUT, "audio"))
    media_strokes = os.path.join(ROOT, "media", "strokes")
    if os.path.isdir(media_strokes):
        shutil.copytree(media_strokes, os.path.join(OUT, "strokes"))

    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(build_index(texts))
    for lvl in range(1, 7):
        open(os.path.join(OUT, f"hsk{lvl}.html"), "w",
             encoding="utf-8").write(build_level(texts, lvl))
    open(os.path.join(OUT, "about.html"), "w", encoding="utf-8").write(build_about(texts))
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(build_404())
    open(os.path.join(OUT, "rss.xml"), "w", encoding="utf-8").write(build_rss(texts))
    words = collect_words(texts)
    wex = word_examples(texts, words)
    json.dump(wex, open(os.path.join(OUT, "assets", "word-examples.json"),
                        "w", encoding="utf-8"), ensure_ascii=False,
              separators=(",", ":"))
    open(os.path.join(OUT, "words.html"), "w", encoding="utf-8").write(
        build_words_index(words))
    for lvl in range(1, 7):
        open(os.path.join(OUT, f"words-hsk{lvl}.html"), "w",
             encoding="utf-8").write(build_words_level(words, wex, lvl))
    gram = collect_grammar(texts)
    open(os.path.join(OUT, "grammar.html"), "w", encoding="utf-8").write(
        build_grammar_index(gram))
    for lvl in range(1, 7):
        open(os.path.join(OUT, f"grammar-hsk{lvl}.html"), "w",
             encoding="utf-8").write(build_grammar_level(gram, lvl))
    open(os.path.join(OUT, "wordbook.html"), "w", encoding="utf-8").write(build_wordbook())
    open(os.path.join(OUT, "progress.html"), "w", encoding="utf-8").write(build_progress(texts))
    for f in ("manifest.webmanifest", "sw.js"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))
    by_level = {}
    for t in sorted(texts, key=lambda x: x["slug"]):
        by_level.setdefault(t["level"], []).append(t)
    next_map = {}
    for lvl, arr in by_level.items():
        for i, t in enumerate(arr):
            if i + 1 < len(arr):
                next_map[t["slug"]] = arr[i + 1]
            else:
                nxt_arr = by_level.get(lvl + 1)
                next_map[t["slug"]] = nxt_arr[0] if nxt_arr else None
    for t in texts:
        open(os.path.join(OUT, "texts", f"{t['slug']}.html"), "w",
             encoding="utf-8").write(build_reader(t, next_map.get(t["slug"])))
    # --- sitemap.xml + robots.txt ------------------------------------
    canon = (SITE.get("canonical_url") or "").rstrip("/")
    n_urls = 0
    if canon:
        # lastmod = 课文源文件的修改日期,让爬虫只重抓真正变过的页
        day = lambda ts: time.strftime("%Y-%m-%d", time.localtime(ts))
        newest = max(t["_mtime"] for t in texts) if texts else time.time()
        urls = [("", "1.0", newest), ("words", "0.7", newest),
                ("grammar", "0.7", newest),
                ("about", "0.5", os.path.getmtime(SITE_PATH))]
        for lvl in range(1, 7):
            urls.append((f"words-hsk{lvl}", "0.6", newest))
            urls.append((f"grammar-hsk{lvl}", "0.6", newest))
        for lvl in range(1, 7):
            lv_ts = [t["_mtime"] for t in texts if t["level"] == lvl]
            urls.append((f"hsk{lvl}", "0.8", max(lv_ts) if lv_ts else newest))
        urls += [(f"texts/{t['slug']}", "0.9", t["_mtime"])
                 for t in sorted(texts, key=lambda x: x["slug"])]
        n_urls = len(urls)
        entries = "\n".join(
            f"  <url><loc>{canon}/{p}</loc>"
            f"<lastmod>{day(ts)}</lastmod><priority>{pr}</priority></url>"
            for p, pr, ts in urls)
        open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n")
        # 个人数据页不进索引
        open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
            "User-agent: *\nAllow: /\n"
            "Disallow: /wordbook\nDisallow: /progress\n\n"
            f"Sitemap: {canon}/sitemap.xml\n")

    print(f"built {len(texts)} readings + words/wordbook -> docs/"
          + (f"\nsitemap: {n_urls} urls -> {canon}/sitemap.xml" if n_urls else ""))


if __name__ == "__main__":
    main()
