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
import re
import shutil
import statistics
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
SITE_PATH = os.path.join(ROOT, "content", "site.json")
SITE = json.load(open(SITE_PATH, encoding="utf-8"))
# The teacher's YouTube uploads, snapshotted by fetch_youtube.py from the
# channel's public RSS feed. Absent file = no videos page, no home block.
TOPICS_PATH = os.path.join(ROOT, "content", "text-topics.json")
TOPICS = (json.load(open(TOPICS_PATH, encoding="utf-8"))
          if os.path.exists(TOPICS_PATH) else {"labels": {}, "texts": {}})
VIDEOS_PATH = os.path.join(ROOT, "content", "videos.json")


def _asset_v(name):
    """Content hash for cache-busting. The service worker serves static assets
    cache-first, so after a deploy a returning visitor used to get new HTML with
    the old style.css (new sections rendered unstyled). A changed file now gets a
    changed URL, which is a cache miss by definition."""
    import hashlib
    fp = os.path.join(ROOT, "assets", name)
    return hashlib.md5(open(fp, "rb").read()).hexdigest()[:10] if os.path.exists(fp) else "0"


ASSET_V = {n: _asset_v(n) for n in ("style.css", "reader.js", "auth.js")}
VIDEOS = (json.load(open(VIDEOS_PATH, encoding="utf-8"))
          if os.path.exists(VIDEOS_PATH) else [])

# 语法点 -> 学习者会问出口的那句英文。AI 答案引擎匹配的是问题的措辞,不是语法
# 术语,所以「A 是 B」这条要在页面上自己说出 "how do you say is in Chinese"。
# 文件缺失或某个点没配都不影响构建,只是少渲染一行。
_GQ_PATH = os.path.join(ROOT, "content", "grammar-questions.json")
GRAM_Q = (json.load(open(_GQ_PATH, encoding="utf-8"))["questions"]
          if os.path.exists(_GQ_PATH) else {})

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


def pick_related(t, pool, n=6):
    """同级别里共享生词最多的几篇。内链要语义相关才有价值 —— 随机凑数的
    'you might also like' 对读者和爬虫都是噪音。"""
    mine = {w[0] for w in t["vocab"]}
    scored = []
    for o in pool:
        if o["slug"] == t["slug"]:
            continue
        scored.append((-len(mine & {w[0] for w in o["vocab"]}), o["slug"], o))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [o for _, _, o in scored[:n]]


def related_html(t, related):
    """课文页底部的同级别推荐。315 篇课文此前几乎不互相传递权重 —— 每页
    只有一条回级别页的链接。"""
    if not related:
        return ""
    items = "".join(
        f'<a class="mr-item" href="{o["slug"]}.html">'
        f'<span class="mr-zh">{esc(o["title_zh"])}</span>'
        f'<span class="mr-en">{esc(o["title_en"])}</span></a>'
        for o in related)
    return f"""
    <section class="more-readings">
      <h2>More HSK {t['level']} reading practice</h2>
      <div class="mr-grid">{items}</div>
      <a class="mr-all" href="../hsk{t['level']}.html">All HSK {t['level']} readings →</a>
    </section>"""


def card_html(t, lesson_no=None, heading=True):
    """Reading card. lesson_no -> course-style 'Lesson N' chip instead of the
    (redundant on a level page) HSK badge. heading=False 用于首页隐藏的搜索
    结果池 —— 那 315 张卡是搜索功能的载体,不是页面主体,不该占 h2。"""
    n_words = sum(len(s["t"]) for s in t["sentences"])
    blob = " ".join([t["title_zh"], t["title_py"], t["title_en"]] +
                    [w[0] + " " + w[1] + " " + w[2] for w in t["vocab"]]).lower()
    chip = (f'<span class="badge l{t["level"]}">Lesson {lesson_no}</span>'
            if lesson_no else
            f'<span class="badge l{t["level"]}">HSK {t["level"]}</span>')
    ht = "h2" if heading else "div"
    return f"""
    <a class="card" data-l="{t['level']}" data-search="{esc(blob)}" href="texts/{t['slug']}.html">
      <div class="tile">{esc(t['title_zh'][0])}</div>
      <div class="card-main">
        <{ht} class="card-title">
          <span class="zh-title">{esc(t['title_zh'])}</span>
          <span class="py-title">{esc(t['title_py'])}</span>
          <span class="en-title">{esc(t['title_en'])}</span>
        </{ht}>
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
               f'<script type="module" src="{rel}assets/auth.js?v={ASSET_V["auth.js"]}"></script>'
               if fb else "")
    verify = "\n".join(
        f'<meta name="{"p:domain_verify" if k == "pinterest" else k}" content="{esc(v)}">'
        for k, v in (SITE.get("site_verification") or {}).items() if v)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
{redir}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{verify}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{seo}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%23c73e2a'/><text x='50' y='72' font-size='62' text-anchor='middle' fill='white' font-family='serif' font-weight='bold'>读</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700;900&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700;900&display=swap"></noscript>
<link rel="stylesheet" href="{rel}assets/style.css?v={ASSET_V['style.css']}">
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
      {'<a class="nav-link" href="' + rel + 'videos.html"><span class="ni">▶️</span><span class="nl"> Videos</span></a>' if VIDEOS else ''}
      {explore_nav(rel)}
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
      {'<a href="' + esc(SITE['youtube_url']) + '" target="_blank" rel="noopener">YouTube</a>' if SITE.get('youtube_url') else ''}
      <a href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">Book a lesson</a>
      <a href="{rel}about.html">About</a>
      <a href="{rel}rss.xml">RSS</a>
    </div>
    <div style="margin-top:6px">
      <a href="{rel}hsk-levels.html">HSK levels compared</a>
      <a href="{rel}quiz.html">Comprehension questions</a>
      <a href="{rel}graded-readers.html">Graded readers</a>
    </div>
    <div style="margin-top:6px">
      <a href="{rel}pinyin.html">Pinyin chart</a>
      <a href="{rel}pairs.html">Word pairs</a>
      <a href="{rel}topics.html">Words by topic</a>
      <a href="{rel}idioms.html">Idioms</a>
      <a href="{rel}festivals.html">Festivals</a>
    </div>
  </footer>
</div>
<div id="pop"></div>
<script src="{rel}assets/reader.js?v={ASSET_V['reader.js']}"></script>
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


def tutor_poster(rel="", eyebrow=None, title=None, tone="", slot=""):
    """Preply 海报位 —— 首页顶部 / 首页 FAQ 前 / 课文页生词表前共用。
    rel 是该页到站根的相对前缀(课文页是 "../")。标题用 span 而不是 h2,
    广告不该进页面的标题大纲。"""
    st = SITE.get("teacher_stats") or {}
    name = esc(SITE["teacher_name"])
    bits = []
    if st.get("rating"):
        bits.append(f'<span class="tp-rate">\u2605 {esc(str(st["rating"]))}</span>')
    if st.get("lessons"):
        bits.append(f'<span>{esc(str(st["lessons"]))} lessons taught</span>')
    if st.get("reviews"):
        bits.append(f'<span>{esc(str(st["reviews"]))} student reviews</span>')
    eyebrow = eyebrow or "One-on-one lessons \u00b7 Preply"
    title = title or f'Learn Mandarin with <span class="tp-name">{name}</span>'
    stats = "".join(bits)
    cls = "tutor-poster" + (f" {tone}" if tone else "")
    return f"""  <aside class="{cls}" data-slot="{slot}">
    <a class="tp-link" href="{esc(SITE['preply_url'])}" target="_blank" rel="noopener">
      <img class="tp-photo" src="{rel}assets/teacher.jpg"
           alt="{name} \u2014 Mandarin teacher"
           width="112" height="112" loading="lazy" decoding="async">
      <div class="tp-body">
        <span class="tp-eyebrow">{esc(eyebrow)}</span>
        <div class="tp-title">{title}</div>
        <div class="tp-stats">{stats}</div>
      </div>
      <span class="tp-btn">Book a trial lesson <span class="tp-arrow">\u2192</span></span>
    </a>
  </aside>"""


def build_reader(t, next_t=None, related=None):
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
    related_sec = related_html(t, related or [])
    body = f"""
  <article class="reading" style="--sc:{LEVEL_COLORS[t['level']]}">
    <div class="reader-banner" data-char="{esc(t['title_zh'][0])}">
      <span class="feat-tag">HSK {t['level']} · {LEVEL_WORDS[t['level']]}</span>
      <h1>{esc(t['title_zh'])}<span class="h1-py">{esc(t['title_py'])}</span><span class="h1-en">{esc(t['title_en'])}</span></h1>
      <div class="b-en">HSK {t['level']} reading practice · {n_words} words · ~{minutes} min</div>
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
{tutor_poster(rel='../', eyebrow='After this reading · Preply',
                 title='Turn this text into a <span class="tp-name">conversation</span>',
                 tone='tp-level', slot='reader-top')}
    <section class="vocab">
      <h2>Key words <span class="zh">生词</span></h2>
      <div class="vgrid">{vocab_rows}</div>
    </section>
{grammar_html}
{quiz_html}
{tutor_poster(rel='../', eyebrow='Before you go · Preply',
                 title='Ready to <span class="tp-name">speak</span> what you just read?',
                 tone='tp-gold', slot='reader-bottom')}
{related_sec}
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


def yt_thumb(vid):
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


def yt_watch(vid):
    return f"https://www.youtube.com/watch?v={vid}"


def video_card(v, rel="", heading=True, desc=False, dup=False):
    """One upload, linking out to YouTube. No embed: an iframe per card pulls
    ~1 MB of player each, sets YouTube cookies before anyone pressed play, and
    the click goes to the channel either way, which is where the subscribe
    button is. Title first, date under it (same rule as the reading cards).

    heading=False renders the title as a span: the home marquee repeats every
    card once for the seamless loop, and a page should not grow 20 extra h2s
    for that. desc=True adds the description as an overlay that slides up over
    the thumbnail on hover. dup=True marks the loop copy as decoration."""
    short = v.get("kind") == "short"
    date = time.strftime("%b %-d, %Y", time.strptime(v["published"], "%Y-%m-%d"))
    tag = "h2" if heading else "span"
    d = (v.get("description") or "").strip()
    if desc and d:
        if len(d) > 150:
            d = d[:150].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
        desc_html = f'<span class="vdesc">{esc(d)}</span>'
    else:
        desc_html = ""
    extra = ' tabindex="-1" aria-hidden="true"' if dup else ""
    return (f'<a class="vcard{" vshort" if short else ""}" href="{yt_watch(v["id"])}" '
            f'target="_blank" rel="noopener" title="{esc(v["title"])}"{extra}>'
            f'<span class="vthumb"><img src="{yt_thumb(v["id"])}" alt="" loading="lazy" '
            f'width="480" height="360"><span class="vplay" aria-hidden="true"></span>{desc_html}</span>'
            f'<span class="vbody"><{tag} class="vtitle">{esc(v["title"])}</{tag}>'
            f'<span class="vmeta">{esc(date)}{" · Short" if short else ""}</span></span></a>')


def home_videos():
    """Home block: every full-length lesson in one horizontal row, the way
    YouTube and Netflix lay out a shelf. Hard edges with a partial card showing
    at the right (that is the affordance), arrows that appear on hover, native
    swipe on touch. reader.js adds the arrows' behaviour and a gentle auto-
    advance of one card every few seconds that stops the moment the visitor
    touches the row. Hovering a card pops it and slides its description up
    over the thumbnail."""
    full = [v for v in VIDEOS if v.get("kind") != "short"][:12]
    if not full:
        return ""
    cards = "".join(video_card(v, heading=False) for v in full)
    return f"""
  <section class="latest videos-home" id="home-videos">
    <h2 class="home-h">Watch a lesson <span class="zh">视频课</span></h2>
    <p class="videos-lead">The teacher behind these readings explains pronunciation, grammar
      and the things textbooks skip — one short video a week, in English.</p>
    <div class="vrow">
      <button class="vnav vprev" type="button" aria-label="Previous videos" hidden>
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></button>
      <div class="vscroller" tabindex="0" aria-label="Video lessons, scroll horizontally">
        <div class="vtrack">{cards}</div>
      </div>
      <button class="vnav vnext" type="button" aria-label="Next videos">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></button>
    </div>
    <a class="latest-more" href="videos.html">All {len(VIDEOS)} videos and Shorts →</a>
  </section>"""


def build_videos():
    full = [v for v in VIDEOS if v.get("kind") != "short"]
    shorts = [v for v in VIDEOS if v.get("kind") == "short"]
    base = (SITE.get("canonical_url") or "").rstrip("/")
    sub = f'{SITE["youtube_url"]}?sub_confirmation=1'
    shorts_html = f"""
  <section class="videos-sec">
    <h2 class="home-h">Shorts <span class="zh">短视频</span></h2>
    <p class="videos-lead">One word or one mix-up per clip, under a minute each.</p>
    <div class="vgrid vgrid-shorts">{''.join(video_card(v) for v in shorts)}</div>
  </section>""" if shorts else ""
    body = f"""
  <section class="about">
    <h1>Video lessons <span style="font-family:var(--serif);color:var(--red)">视频课</span></h1>
    <p class="vhead-who"><b>{esc(SITE["teacher_name"])}</b> · {esc(SITE.get("teacher_role", "Mandarin teacher"))}</p>
    <p>{len(VIDEOS)} videos from my YouTube channel — the same teacher who writes the
      readings on this site. Pronunciation, grammar, and the things textbooks skip,
      explained in English for learners from complete beginner to HSK 5.</p>
    <p>Each video pairs with the readings: watch how a pattern works, then meet it in a
      graded text. New video every week.</p>
    <a class="cta v-sub" href="{esc(sub)}" target="_blank" rel="noopener">Subscribe on YouTube →</a>
  </section>
  <section class="videos-sec">
    <h2 class="home-h">Lessons <span class="zh">课</span></h2>
    <div class="vgrid">{''.join(video_card(v) for v in full)}</div>
  </section>
  {shorts_html}"""
    ld = [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{SITE['site_name']} video lessons",
        "numberOfItems": len(VIDEOS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {
                 "@type": "VideoObject",
                 "name": v["title"],
                 "description": v.get("description") or v["title"],
                 "thumbnailUrl": yt_thumb(v["id"]),
                 "uploadDate": v["published"],
                 "url": yt_watch(v["id"]),
                 "embedUrl": f"https://www.youtube.com/embed/{v['id']}",
             }}
            for i, v in enumerate(VIDEOS)
        ],
    }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["site_name"], "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": "Video lessons"},
        ],
    }]
    return page(f"Chinese Video Lessons — Pronunciation & Grammar in English | {SITE['site_name']}",
                f"{len(full)} short Chinese lessons and {len(shorts)} Shorts from a native Mandarin "
                f"teacher: pronunciation, grammar and the things textbooks skip, explained in English.",
                body, path="videos", ld=ld)


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
    all_cards = "".join(card_html(t, heading=False) for t in
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
{tutor_poster(slot='home-top')}
  <div class="searchbar"><input type="search" id="search"
    placeholder="Search all readings — 汉字 / pinyin / English…" autocomplete="off"></div>
  <section class="today-wrap" id="today-wrap" hidden>
    <h2 class="home-h">Today's picks <span class="zh">今日推荐</span></h2>
    <div class="tstack" id="today-slot"></div>
    <div class="tdots" id="today-dots"></div>
  </section>
  <section class="lvlgrid" id="lvlgrid">{''.join(lvlcards)}
  </section>
{home_explore()}
  <section class="cards" id="search-results" hidden>{all_cards}
  </section>
{home_videos()}
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
{tutor_poster(eyebrow='After the readings · Preply',
                 title='Speaking is where you get <span class="tp-name">stuck</span>',
                 tone='tp-gold', slot='home-faq')}
  <section class="faq" id="home-faq">
    <h2 class="home-h">Common questions <span class="zh">常见问题</span></h2>
    <div class="faq-grid">{faq_html}
    </div>
  </section>
  <script type="application/ld+json">{faq_ld}</script>
  <script>window.RCD_LEVELS={json.dumps(levels_map)};</script>"""
    base = (SITE.get("canonical_url") or "").rstrip("/")
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": SITE["teacher_name"],
        "jobTitle": "Mandarin teacher",
        "url": f"{base}/about",
        "image": f"{base}/assets/teacher.jpg",
        "sameAs": [u for u in (SITE["preply_url"], SITE["facebook_url"],
                               SITE.get("youtube_url")) if u],
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


def _text_len(t):
    """(sentences, characters) of one reading; punctuation tokens don't count."""
    n = len(t["sentences"])
    c = sum(len(tok[0]) for s in t["sentences"] for tok in s["t"] if len(tok) >= 2)
    return n, c


def level_extras(texts, mine, lvl):
    """Below-the-fold sections for the upper level pages (HSK 4-6), all derived
    from the corpus itself so nothing here can drift out of date or be made up:
    how long the texts run (vs the level below), one real opening sentence, the
    grammar patterns that recur most in these readings, and one of the actual
    comprehension questions. Bing's search log and Copilot's citations both show
    the upper-level index pages being asked for 'sample text' and 'comprehension
    sample questions', and a card grid answers neither."""
    def stats(ts):
        pairs = [_text_len(t) for t in ts]
        sents = statistics.median(n for n, _ in pairs)
        chars = statistics.median(c for _, c in pairs)
        per = statistics.median(c / n for n, c in pairs if n)
        return sents, chars, per
    sents, chars, per = stats(mine)
    below = [t for t in texts if t["level"] == lvl - 1]
    cmp_html = ""
    if below:
        b_sents, b_chars, b_per = stats(below)
        cmp_html = (f' At HSK {lvl - 1} the same figures are {b_sents:.0f} sentences, '
                    f'{b_chars:.0f} characters and {b_per:.0f} characters per sentence, '
                    f'so the step up is mostly in how much each sentence carries, not in '
                    f'how many there are.')

    # one real opening line, from the first reading (by slug) with a full sentence
    sample = next((t for t in mine if len([x for x in t["sentences"][0]["t"] if len(x) >= 2]) >= 5),
                  mine[0])
    s0 = sample["sentences"][0]
    zh = "".join(tok[0] for tok in s0["t"])
    py = " ".join(tok[1] for tok in s0["t"] if len(tok) >= 2)
    sample_html = f"""
      <figure class="lvl-sample">
        <blockquote lang="zh">{esc(zh)}</blockquote>
        <div class="ls-py">{esc(py)}</div>
        <div class="ls-en">{esc(s0["en"])}</div>
        <figcaption>Opening line of <a href="texts/{esc(sample["slug"])}.html">{esc(sample["title_zh"])} —
          {esc(sample["title_en"])}</a>, one of the {len(mine)} HSK {lvl} readings.</figcaption>
      </figure>"""

    # grammar that recurs across these readings, most frequent first
    gram = {}
    for t in mine:
        for g in t.get("grammar", []):
            pat = (g.get("p") or "").strip()
            if not pat:
                continue
            e = gram.setdefault(gram_key(pat), {"p": pat, "e": "", "n": 0})
            e["n"] += 1
            for f in ("p", "e"):
                v = (pat if f == "p" else g.get("e", "")) or ""
                if len(v) > len(e[f]):
                    e[f] = v
    top = sorted(gram.values(), key=lambda d: (-d["n"], d["p"]))[:8]
    gram_html = "".join(
        f'<li><span class="lg-p">{esc(d["p"])}</span>'
        f'<span class="lg-n">{d["n"]} readings</span>'
        f'<span class="lg-e">{esc(d["e"])}</span></li>'
        for d in top)

    # one real comprehension question, answer folded
    quiz_html = ""
    qz = (sample.get("quiz") or [None])[0]
    if qz and qz.get("a"):
        opts = "".join(f'<li>{esc(a)}</li>' for a in qz["a"])
        ans = qz["a"][qz.get("c", 0)] if 0 <= qz.get("c", 0) < len(qz["a"]) else ""
        quiz_html = f"""
      <h2>What the comprehension questions look like</h2>
      <p>Every HSK {lvl} reading ends with three questions in English about what the
        text actually said — not vocabulary drills. Here is the first one from
        <a href="texts/{esc(sample["slug"])}.html">{esc(sample["title_en"])}</a>:</p>
      <div class="lvl-quiz">
        <p class="lq-q">{esc(qz["q"])}</p>
        <ol class="lq-a">{opts}</ol>
        <details><summary>Show answer</summary><p>{esc(ans)}</p></details>
      </div>
      <p><a href="quiz-hsk{lvl}.html">More HSK {lvl} comprehension questions with answers →</a></p>"""

    return f"""
      <h2>What an HSK {lvl} text looks like here</h2>
      <p>Across the {len(mine)} readings on this page the typical text runs {sents:.0f} sentences
        and {chars:.0f} characters, about {per:.0f} characters per sentence.{cmp_html}</p>
      {sample_html}

      <h2>Grammar you will meet in these readings</h2>
      <p>The patterns below turn up most often across the HSK {lvl} texts. Each reading
        explains its own patterns under the text; the full list with example sentences
        is on the <a href="grammar-hsk{lvl}.html">HSK {lvl} grammar page</a>.</p>
      <ul class="lvl-gram">{gram_html}</ul>
      {quiz_html}"""


def level_topics(mine, lvl):
    """'Readings by topic': the level's readings grouped by the hand-reviewed
    topic map in content/text-topics.json. Answers 'HSK 1 text about my
    family' style questions with a direct list instead of a 60-card grid."""
    groups = {}
    for t in mine:
        k = TOPICS["texts"].get(t["slug"])
        if k:
            groups.setdefault(k, []).append(t)
    if not groups:
        return ""
    order = list(TOPICS["labels"])
    blocks = []
    for k in sorted(groups, key=lambda k: (-len(groups[k]), order.index(k) if k in order else 99)):
        links = "".join(
            f'<li><a href="texts/{esc(t["slug"])}.html">{esc(t["title_en"])}'
            f' <span class="lt-zh">{esc(t["title_zh"])}</span></a></li>'
            for t in groups[k])
        blocks.append(f'<div class="lvl-topic" id="topic-{esc(k)}">'
                      f'<h3>{esc(TOPICS["labels"].get(k, k))} <span class="lt-n">{len(groups[k])}</span></h3>'
                      f'<ul>{links}</ul></div>')
    return f"""
      <h2>HSK {lvl} readings by topic</h2>
      <p>The same {len(mine)} readings, grouped by what they are about.</p>
      <div class="lvl-topics">{''.join(blocks)}</div>"""


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
      {level_extras(texts, mine, lvl) if lvl >= 4 else ""}
      <p class="lvl-how"><strong>Practice questions:</strong> every reading ends with a
        three-question comprehension check. A sample of them, with answers, is on the
        <a href="quiz-hsk{lvl}.html">HSK {lvl} reading comprehension questions</a> page.
        How this level compares with the others: <a href="hsk-levels.html">HSK 1-6 side by side</a>.</p>
      {level_topics(mine, lvl)}

      <h2>HSK {lvl} questions</h2>
      <div class="faq">{faq_html}</div>
    </section>"""
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[lvl]}" data-char="{LEVEL_NUM_ZH[lvl]}">
      <span class="feat-tag">HSK {lvl} · {LEVEL_WORDS[lvl]}</span>
      <h1>HSK {lvl} Reading Practice <span class="lv-h-zh">{LEVEL_ZH[lvl]}</span></h1>
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
    # HSK 4 is the one level page Bing shows a lot and nobody clicks (63 impressions,
    # 0 clicks at position 5 as of 2026-09-24), and its queries ask for "reading
    # comprehension sample questions". Lead with that for this level only, so the
    # other levels stay as a control.
    if lvl == 4:
        desc = (f"Free HSK {lvl} reading practice with comprehension questions: {len(mine)} "
                f"original graded texts inside the {s['vocab']}-word HSK {lvl} list, each "
                f"with pinyin, audio and a 3-question quiz.")
    else:
        desc = (f"Free HSK {lvl} reading practice: {len(mine)} original graded texts inside "
                f"the {s['vocab']}-word HSK {lvl} list, with pinyin, audio, "
                f"tap-to-translate and quizzes.")
    return page(f"HSK {lvl} Reading Practice — {len(mine)} Free Graded Readings | {SITE['site_name']}",
                desc, body, path=f"hsk{lvl}", ld=ld)


# ---------------------------------------------------------------------------
# Answer pages. Bing's query log shows Copilot asking for "HSK N reading
# comprehension sample questions", "HSK 1 2 3 compared", "graded readers for
# HSK 5". Each page below answers one of those directly; everything except the
# third-party reader list is computed from the readings themselves.
# ---------------------------------------------------------------------------

QUIZ_PER_LEVEL = 30


def pick_quiz(mine):
    """Up to QUIZ_PER_LEVEL questions, one per reading, spread across topics
    (round-robin) so the page is not thirty questions about food."""
    groups = {}
    for t in mine:
        if t.get("quiz"):
            groups.setdefault(TOPICS["texts"].get(t["slug"], "_"), []).append(t)
    picked, i = [], 0
    while len(picked) < QUIZ_PER_LEVEL and any(groups.values()):
        for k in sorted(groups):
            if groups[k] and len(picked) < QUIZ_PER_LEVEL:
                t = groups[k].pop(0)
                # English question stems only: a few older readings wrote the
                # quiz in Chinese, which a sample page for English speakers
                # should not lead with. Start at a rotating offset for variety.
                qs = t["quiz"][i % len(t["quiz"]):] + t["quiz"][:i % len(t["quiz"])]
                q = next((x for x in qs if re.search(r"[A-Za-z]{3}", x.get("q", ""))
                          and x.get("a") and 0 <= x.get("c", 0) < len(x["a"])), None)
                if q:
                    picked.append((t, q))
        i += 1
    return picked


def build_quiz_level(texts, lvl):
    mine = [t for t in sorted(texts, key=lambda x: x["slug"]) if t["level"] == lvl]
    picked = pick_quiz(mine)
    total_q = sum(len(t.get("quiz", [])) for t in mine)
    items = []
    for n, (t, q) in enumerate(picked, 1):
        opts = "".join(f"<li>{esc(a)}</li>" for a in q["a"])
        ans = q["a"][q["c"]]
        items.append(f"""
      <li class="qz-item">
        <h3 class="qz-q">{esc(q["q"])}</h3>
        <ol class="qz-a" type="A">{opts}</ol>
        <details><summary>Answer</summary><p><b>{"ABC"[q["c"]]}.</b> {esc(ans)}</p></details>
        <div class="qz-src">From <a href="texts/{esc(t["slug"])}.html">{esc(t["title_zh"])} — {esc(t["title_en"])}</a></div>
      </li>""")
    chips = "".join(
        f'<a class="lvl-chip{" on" if i == lvl else ""}" data-l="{i}" href="quiz-hsk{i}.html">HSK {i}</a>'
        for i in range(1, 7))
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[lvl]}" data-char="{LEVEL_NUM_ZH[lvl]}">
      <span class="feat-tag">HSK {lvl} · {LEVEL_WORDS[lvl]}</span>
      <h1>HSK {lvl} Reading Comprehension Questions <span class="lv-h-zh">阅读理解</span></h1>
      <div class="b-en">{len(picked)} sample questions with answers, each taken from a free graded reading.</div>
    </div>
    <div class="levels"><div class="seg">{chips}</div></div>
    <section class="lvl-intro qz-intro">
      <p>Every HSK {lvl} reading on this site ends with three multiple-choice questions in
        English about what the text actually said. There are {total_q} of them across
        {len(mine)} readings; below is one from each of {len(picked)} readings, spread across
        topics. Try to answer before opening the answer, then read the text it came from.</p>
      <p>These are comprehension checks written for learners, not official HSK exam items.
        The <a href="hsk{lvl}.html">HSK {lvl} reading practice</a> page has every reading.</p>
    </section>
    <ol class="qz-list">{''.join(items)}
    </ol>
  </article>"""
    base = (SITE.get("canonical_url") or "").rstrip("/")
    ld = [{
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["site_name"], "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": f"HSK {lvl} reading practice", "item": f"{base}/hsk{lvl}"},
            {"@type": "ListItem", "position": 3, "name": "Comprehension questions"},
        ]}]
    return page(f"HSK {lvl} Reading Comprehension Questions with Answers ({len(picked)} Samples) | {SITE['site_name']}",
                f"{len(picked)} HSK {lvl} reading comprehension sample questions with answers, each from a "
                f"free graded Chinese reading with pinyin and audio.",
                body, path=f"quiz-hsk{lvl}", ld=ld)


def build_levels_compare(texts, gram):
    rows, rows_ld = [], []
    prev_vocab = 0
    for lvl in range(1, 7):
        mine = [t for t in sorted(texts, key=lambda x: x["slug"]) if t["level"] == lvl]
        pairs = [_text_len(t) for t in mine]
        sents = statistics.median(n for n, _ in pairs)
        chars = statistics.median(c for _, c in pairs)
        per = statistics.median(c / n for n, c in pairs if n)
        s = LEVEL_SEO[lvl]
        n_gram = sum(1 for g in gram.values() if g["lvl"] == lvl)
        sample = next((t for t in mine if len([x for x in t["sentences"][0]["t"] if len(x) >= 2]) >= 5), mine[0])
        zh = "".join(tok[0] for tok in sample["sentences"][0]["t"])
        rows.append(f"""
        <tr style="--sc:{LEVEL_COLORS[lvl]}">
          <th scope="row"><a href="hsk{lvl}.html">HSK {lvl}</a><span>{LEVEL_ZH[lvl]}</span></th>
          <td>{s["vocab"]:,}</td><td>{s["vocab"] - prev_vocab:,}</td><td>{esc(s["cefr"])}</td>
          <td>{sents:.0f}</td><td>{chars:.0f}</td><td>{per:.0f}</td>
          <td><a href="grammar-hsk{lvl}.html">{n_gram}</a></td>
          <td><a href="hsk{lvl}.html">{len(mine)}</a></td>
        </tr>""")
        rows_ld.append((lvl, s, sents, chars, per, zh, sample))
        prev_vocab = s["vocab"]
    samples = "".join(
        f'<li style="--sc:{LEVEL_COLORS[l]}"><span class="cmp-l">HSK {l}</span>'
        f'<span class="cmp-zh" lang="zh">{esc(zh)}</span>'
        f'<span class="cmp-en">{esc(smp["sentences"][0]["en"])}</span>'
        f'<a href="texts/{esc(smp["slug"])}.html">{esc(smp["title_en"])} →</a></li>'
        for l, s, _, _, _, zh, smp in rows_ld)
    r1, r3, r4, r6 = rows_ld[0], rows_ld[2], rows_ld[3], rows_ld[5]
    faqs = [
        ("How many words do you need for each HSK level?",
         "Under HSK 2.0: 150 words for HSK 1, 300 for HSK 2, 600 for HSK 3, 1,200 for HSK 4, "
         "2,500 for HSK 5 and 5,000 for HSK 6. Each level roughly doubles the one before."),
        ("How much harder do the texts get from level to level?",
         f"On this site the typical HSK 1 reading is {r1[2]:.0f} sentences and {r1[3]:.0f} characters; "
         f"HSK 3 is {r3[2]:.0f} sentences and {r3[3]:.0f} characters; HSK 6 is {r6[2]:.0f} sentences and "
         f"{r6[3]:.0f} characters. The number of sentences barely changes. What grows is how much each "
         f"sentence carries: about {r1[4]:.0f} characters per sentence at HSK 1, {r4[4]:.0f} at HSK 4 and "
         f"{r6[4]:.0f} at HSK 6."),
        ("Which HSK level is the biggest jump?",
         "Most learners find HSK 3 and HSK 5 the hardest steps. HSK 3 is where sentences start carrying "
         "complements and linking words; HSK 5 is where the register switches from spoken Chinese written "
         "down to written Chinese."),
        ("Does this use HSK 2.0 or HSK 3.0?",
         "The word counts and levels here are HSK 2.0, the six-level scheme these readings are graded "
         "against. The newer HSK 3.0 standard (2021) regroups the levels into nine bands with larger word "
         "lists. If you are preparing for a specific exam sitting, check which version it uses."),
    ]
    faq_html = "".join(f'<details class="faq-q"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
                       for q, a in faqs)
    body = f"""
  <section class="about cmp-head">
    <h1>HSK 1 to 6 compared <span style="font-family:var(--serif);color:var(--red)">六级对比</span></h1>
    <p>What changes from one HSK level to the next: the word list, the CEFR band it roughly
      matches, and how long and dense the reading texts get. The text figures are medians
      measured across the {len(texts)} graded readings on this site, not estimates.</p>
  </section>
  <div class="cmp-wrap">
    <table class="cmp">
      <thead><tr>
        <th scope="col">Level</th><th scope="col">Words (total)</th><th scope="col">New words</th>
        <th scope="col">CEFR (approx.)</th><th scope="col">Sentences per text</th>
        <th scope="col">Characters per text</th><th scope="col">Characters per sentence</th>
        <th scope="col">Grammar patterns</th><th scope="col">Readings</th>
      </tr></thead>
      <tbody>{''.join(rows)}
      </tbody>
    </table>
  </div>
  <section class="lvl-intro cmp-body">
    <h2>The same kind of sentence at each level</h2>
    <p>The opening line of one reading per level. Read down the list and the step up is easy to
      see: longer clauses, more linking words, then written-register phrasing.</p>
    <ul class="cmp-samples">{samples}</ul>
    <h2>Questions</h2>
    <div class="faq">{faq_html}</div>
  </section>"""
    base = (SITE.get("canonical_url") or "").rstrip("/")
    ld = [{"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q,
                           "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": SITE["site_name"], "item": f"{base}/"},
               {"@type": "ListItem", "position": 2, "name": "HSK levels compared"}]}]
    return page(f"HSK 1-6 Levels Compared: Words, CEFR and Reading Difficulty | {SITE['site_name']}",
                "HSK 1 to 6 side by side: vocabulary size, new words, approximate CEFR level, and how long "
                "and dense the reading texts get, measured across 415 graded Chinese readings.",
                body, path="hsk-levels", ld=ld)


# Third-party facts are kept deliberately coarse (format, how it is graded, how
# it is paid for) because prices and catalogue sizes change. Review before
# changing: nothing here should be a number we cannot stand behind.
GRADED_READERS = [
    ("Read Mandarin", "https://readmandarin.com/", "Website", "HSK 1-6",
     "Free", "Pinyin over every character, tap-to-translate, audio, quizzes",
     "Short daily reading at an exact HSK level", True),
    ("Mandarin Companion", "https://mandarincompanion.com/", "Books & ebooks",
     "Own levels by character count (about 150 to 450 characters)", "Paid",
     "Full-length stories, many adapted from Western classics",
     "Your first complete novel at HSK 2-4", False),
    ("Chinese Breeze 汉语风", "https://www.pup.cn/", "Books", "Eight levels by word count, from 300 words up",
     "Paid", "Original stories written for learners, Peking University Press",
     "Longer original stories with a gentle word curve", False),
    ("Du Chinese", "https://www.duchinese.net/", "App & website", "HSK 1-6",
     "Subscription, some free lessons", "Pinyin toggle, audio, tap-to-translate",
     "Mobile reading with audio on the go", False),
    ("The Chairman's Bao", "https://www.thechairmansbao.com/", "App & website", "HSK levels",
     "Subscription", "News articles rewritten by level",
     "HSK 4 and up who want current events", False),
    ("HSK Reading", "https://hskreading.com/", "Website", "HSK 1-6", "Free",
     "Short passages with questions", "Exam-style reading practice", False),
    ("Chinese Graded Reader", "https://chinesegradedreader.com/", "Website", "HSK 1-4", "Free",
     "Short stories with audio", "Beginner stories", False),
]


def build_graded_readers(texts):
    counts = {}
    for t in texts:
        counts[t["level"]] = counts.get(t["level"], 0) + 1
    rows = "".join(
        f"""
        <tr{' class="gr-self"' if own else ''}>
          <th scope="row"><a href="{esc(url)}"{'' if own else ' target="_blank" rel="nofollow noopener"'}>{esc(name)}</a></th>
          <td>{esc(fmt)}</td><td>{esc(grade)}</td><td>{esc(cost)}</td><td>{esc(feat)}</td><td>{esc(best)}</td>
        </tr>"""
        for name, url, fmt, grade, cost, feat, best, own in GRADED_READERS)
    per_level = " · ".join(f'<a href="hsk{l}.html">HSK {l}: {counts.get(l, 0)}</a>' for l in range(1, 7))
    picks = [
        ("HSK 1-2", "Start with short graded texts where every character has pinyin, and read one a day. "
                    "A full novel is too long at this stage; finishing matters more than length."),
        ("HSK 3-4", "This is the right time for a first complete book. Character-count graded novels such as "
                    "Mandarin Companion or Chinese Breeze work well alongside daily short readings."),
        ("HSK 5-6", "Move toward real-world material: news rewritten by level, essays, and eventually native "
                    "novels and newspapers. Graded readers get thin at the top end."),
    ]
    picks_html = "".join(f'<div class="gr-pick"><h3>{esc(l)}</h3><p>{esc(t)}</p></div>' for l, t in picks)
    body = f"""
  <section class="about">
    <h1>Chinese graded readers by HSK level <span style="font-family:var(--serif);color:var(--red)">分级读物</span></h1>
    <p>The main options for graded Chinese reading, side by side: books, apps and free websites.
      We run one of them (this site), so it is listed first and marked; the rest are here because
      they are the ones learners actually ask about. Check each site for current prices.</p>
  </section>
  <div class="cmp-wrap">
    <table class="cmp gr-table">
      <thead><tr><th scope="col">Reader</th><th scope="col">Format</th><th scope="col">How it is graded</th>
        <th scope="col">Cost</th><th scope="col">What you get</th><th scope="col">Best for</th></tr></thead>
      <tbody>{rows}
      </tbody>
    </table>
  </div>
  <section class="lvl-intro">
    <h2>What to read at each stage</h2>
    <div class="gr-picks">{picks_html}</div>
    <h2>Free readings on this site</h2>
    <p>{len(texts)} original graded readings: {per_level}. Each has pinyin, audio, tap-to-translate and
      three comprehension questions. <a href="hsk-levels.html">Compare the levels</a> to find where to start.</p>
  </section>"""
    return page(f"Chinese Graded Readers by HSK Level: Books, Apps and Free Sites | {SITE['site_name']}",
                "Chinese graded readers compared by HSK level: Mandarin Companion, Chinese Breeze, Du Chinese, "
                "The Chairman's Bao and free graded reading sites, with what to read at each stage.",
                body, path="graded-readers")


def build_quiz_index(texts):
    cards = "".join(
        f'<a class="lvlcard" href="quiz-hsk{i}.html" style="--sc:{LEVEL_COLORS[i]}">'
        f'<div class="lv-top"><span class="lv-tag">HSK {i}</span><span class="lv-zh">{LEVEL_ZH[i]}</span></div>'
        f'<div class="lv-name">{LEVEL_WORDS[i]}</div>'
        f'<div class="lv-meta"><span class="lv-done">{min(QUIZ_PER_LEVEL, sum(1 for t in texts if t["level"] == i and t.get("quiz")))} questions</span>'
        f'<span class="lv-go">→</span></div></a>' for i in range(1, 7))
    body = f"""
  <section class="about">
    <h1>Chinese reading comprehension questions <span style="font-family:var(--serif);color:var(--red)">阅读理解</span></h1>
    <p>Sample comprehension questions with answers for every HSK level, each taken from a free
      graded reading on this site. Pick a level.</p>
  </section>
  <section class="lvlgrid">{cards}</section>"""
    return page(f"Chinese Reading Comprehension Questions by HSK Level | {SITE['site_name']}",
                "Chinese reading comprehension sample questions with answers for HSK 1 to 6, each from a free "
                "graded reading with pinyin and audio.", body, path="quiz")


# ---------------------------------------------------------------------------
# Explore section (2026-09-24): word pairs, pinyin chart, words by topic,
# idioms, festivals. Each is data in content/*.json plus examples pulled from
# the readings, so nothing here repeats what the readings already say.
# ---------------------------------------------------------------------------

def _load(name, default):
    p = os.path.join(ROOT, "content", name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

PAIRS = _load("word-pairs.json", {"pairs": []})["pairs"]
FESTIVALS = _load("festivals.json", {"festivals": []})["festivals"]
PINYIN = _load("pinyin.json", {"syllables": {}})["syllables"]
IDIOMS = _load("idioms.json", {"stories": [], "idioms": []})

EXPLORE = [
    ("pinyin", "🔤", "Pinyin chart", "Every syllable in all four tones, with audio"),
    ("pairs", "⚖️", "Word pairs", "预订 or 预定? 再 or 又? Easily confused words"),
    ("topics", "🗂️", "Words by topic", "Food, travel, work… vocabulary from the readings"),
    ("idioms", "🐉", "Idiom stories", "Chengyu and the stories behind them"),
    ("festivals", "🏮", "Festivals", "Spring Festival to Mid-Autumn: greetings and words"),
    ("quiz", "✅", "Practice questions", "Reading comprehension questions with answers"),
    ("hsk-levels", "📊", "HSK levels compared", "HSK 1-6 side by side"),
    ("graded-readers", "📚", "Graded readers", "Books, apps and free sites by level"),
]


def explore_nav(rel):
    links = "".join(
        f'<a class="nd-item" href="{rel}{slug}.html"><span class="nd-i">{icon}</span>'
        f'<span class="nd-t"><b>{esc(name)}</b><i>{esc(desc)}</i></span></a>'
        for slug, icon, name, desc in EXPLORE)
    return (f'<div class="nav-drop" id="nav-drop">'
            f'<button class="nav-link nav-drop-btn" id="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true">'
            f'<span class="ni">🗺️</span><span class="nl"> Explore</span><span class="nd-caret" aria-hidden="true">▾</span></button>'
            f'<div class="nav-drop-panel" role="menu">{links}</div></div>')


def home_explore():
    counts = {"pairs": len(PAIRS), "festivals": len(FESTIVALS),
              "idioms": len(IDIOMS["idioms"]), "pinyin": len(PINYIN)}
    tiles = "".join(
        f'<a class="xtile" href="{slug}.html"><span class="xt-i">{icon}</span>'
        f'<span class="xt-b"><b>{esc(name)}</b><i>{esc(desc)}</i></span></a>'
        for slug, icon, name, desc in EXPLORE)
    return f"""
  <section class="explore-home" id="home-explore">
    <h2 class="home-h">Explore <span class="zh">更多</span></h2>
    <div class="xgrid">{tiles}</div>
  </section>"""


class Corpus:
    """Token index over the readings, for pulling real example sentences."""
    def __init__(self, texts):
        self.idx = {}
        for t in sorted(texts, key=lambda x: (x["level"], x["slug"])):
            for s in t["sentences"]:
                toks = s["t"]
                for i, tok in enumerate(toks):
                    if len(tok) == 3:
                        self.idx.setdefault(tok[0], []).append((t, s, i))

    def examples(self, word, py=None, n=3, maxlen=40, exclude=()):
        out, seen = [], set()
        cands = [(t, s, i) for t, s, i in self.idx.get(word, [])
                 if (py is None or s["t"][i][1].lower() == py) and t["slug"] not in exclude]
        cands.sort(key=lambda c: (c[0]["level"], len("".join(x[0] for x in c[1]["t"]))))
        for t, s, i in cands:
            plain = "".join(x[0] for x in s["t"])
            if plain in seen or len(plain) > maxlen:
                continue
            seen.add(plain)
            out.append((t, s, i))
            if len(out) >= n:
                break
        return out


def ex_html(t, s, i, blank=False):
    zh = "".join(
        ('<b class="hl">___</b>' if blank else f'<b class="hl">{esc(x[0])}</b>') if j == i else esc(x[0])
        for j, x in enumerate(s["t"]))
    return (f'<li class="ex"><span class="ex-zh" lang="zh">{zh}</span>'
            + ('' if blank else f'<span class="ex-en">{esc(s["en"])}</span>')
            + f'<a class="ex-src" href="texts/{esc(t["slug"])}.html">HSK {t["level"]} · {esc(t["title_zh"])}</a></li>')


def video_by_id(vid):
    return next((v for v in VIDEOS if v["id"] == vid), None)


def crumbs(name):
    base = (SITE.get("canonical_url") or "").rstrip("/")
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": SITE["site_name"], "item": f"{base}/"},
                {"@type": "ListItem", "position": 2, "name": name}]}


# ---------- word pairs ----------

def pair_quiz(corpus, p, n=6):
    words = p["words"]
    per = max(1, n // len(words))
    items = []
    for w in words:
        py = p["match"].get(w, {}).get("py")
        got = 0
        for t, s, i in sorted(corpus.idx.get(w, []), key=lambda c: (c[0]["level"], len(c[1]["t"]))):
            if t["level"] > 3 or got >= per:
                continue
            if py and s["t"][i][1].lower() != py:
                continue
            # skip sentences that contain another word of the set: one blank only
            others = [j for j, x in enumerate(s["t"]) if len(x) == 3 and x[0] in words and j != i]
            if others or len("".join(x[0] for x in s["t"])) > 30:
                continue
            items.append((t, s, i, w))
            got += 1
    return items


def build_pair(corpus, p):
    words = p["words"]
    rows = "".join(f'<tr><th scope="row" lang="zh">{esc(a)}</th><td>{esc(b)}</td></tr>' for a, b in p["points"])
    ex_blocks = []
    for w, py_disp in zip(words, p["pinyin"]):
        m = p["match"].get(w, {})
        found = corpus.examples(w, py=m.get("py"), n=3)
        if found:
            lis = "".join(ex_html(t, s, i) for t, s, i in found)
            note = "From the readings on this site"
        else:
            lis = "".join(f'<li class="ex"><span class="ex-zh" lang="zh">{esc(zh).replace(esc(w), f"<b class=hl>{esc(w)}</b>", 1)}</span>'
                          f'<span class="ex-en">{esc(en)}</span></li>' for zh, en in p["examples"].get(w, []))
            note = "Example sentences"
        if lis:
            ex_blocks.append(f'<div class="pair-ex"><h2><span lang="zh">{esc(w)}</span> <span class="pe-py">{esc(py_disp)}</span></h2>'
                             f'<p class="pe-note">{note}</p><ul class="exlist">{lis}</ul></div>')
    quiz_html = ""
    if p.get("quiz"):
        qs = pair_quiz(corpus, p)
        if qs:
            opts = " / ".join(words)
            qli = "".join(
                f'<li class="qz-item"><div class="ex-zh" lang="zh">{"".join(("<b class=hl>___</b>" if j == i else esc(x[0])) for j, x in enumerate(s["t"]))}</div>'
                f'<div class="pq-opts">{esc(opts)}</div>'
                f'<details><summary>Answer</summary><p><b lang="zh">{esc(w)}</b> — {esc(s["en"])}</p></details>'
                f'<div class="qz-src">From <a href="texts/{esc(t["slug"])}.html">{esc(t["title_zh"])} — {esc(t["title_en"])}</a></div></li>'
                for t, s, i, w in qs)
            quiz_html = f'<h2>Practice: fill in the blank</h2><p>Each sentence is from a reading on this site. Which word goes in the gap?</p><ol class="qz-list pq-list">{qli}</ol>'
    vid = video_by_id(p.get("video", "")) if p.get("video") else None
    video_html = (f'<h2>Watch the lesson</h2><div class="vgrid pair-video">{video_card(vid)}</div>' if vid else "")
    others = "".join(f'<li><a href="pairs-{esc(o["id"])}.html" lang="zh">{esc(" vs ".join(o["words"]))}</a></li>'
                     for o in PAIRS if o["id"] != p["id"])
    q = f"What is the difference between {' and '.join(words)}?"
    body = f"""
  <article class="pair">
    <div class="reader-banner" style="--sc:{LEVEL_COLORS.get(p['level'], '#8a6d3b')}" data-char="{esc(words[0][0])}">
      <span class="feat-tag">Word pairs · from HSK {p['level']}</span>
      <h1>{esc(p['title'])}</h1>
      <div class="b-en">{esc(p['short'])}</div>
    </div>
    <section class="lvl-intro pair-body">
      <h2>{esc(q)}</h2>
      <p>{esc(p['summary'])}</p>
      <div class="cmp-wrap"><table class="cmp pair-table"><tbody>{rows}</tbody></table></div>
      {''.join(ex_blocks)}
      {quiz_html}
      {video_html}
      <h2>More word pairs</h2>
      <ul class="pair-more">{others}</ul>
    </section>
  </article>"""
    ld = [{"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q,
                           "acceptedAnswer": {"@type": "Answer", "text": p["summary"]}}]},
          crumbs("Word pairs")]
    return page(f"{p['title']} | {SITE['site_name']}",
                f"{p['summary'][:150].rsplit(' ', 1)[0]}…", body, path=f"pairs-{p['id']}", ld=ld)


def build_pairs_index():
    cards = "".join(
        f'<a class="pcard" href="pairs-{esc(p["id"])}.html">'
        f'<span class="pc-w" lang="zh">{esc(" · ".join(p["words"]))}</span>'
        f'<span class="pc-t">{esc(p["title"].split(":", 1)[-1].strip())}</span>'
        f'<span class="pc-s">{esc(p["short"])}</span>'
        f'<span class="pc-m">From HSK {p["level"]}{" · ▶ video" if p.get("video") else ""}</span></a>'
        for p in sorted(PAIRS, key=lambda x: x["level"]))
    body = f"""
  <section class="about">
    <h1>Easily confused Chinese words <span style="font-family:var(--serif);color:var(--red)">易混词</span></h1>
    <p>{len(PAIRS)} pairs of Chinese words that learners mix up, each explained in plain English with real
      example sentences from the readings on this site. Some come with a short video lesson.</p>
  </section>
  <section class="pgrid">{cards}</section>"""
    return page(f"Easily Confused Chinese Words: {len(PAIRS)} Pairs Explained | {SITE['site_name']}",
                "Commonly confused Chinese words explained: 的 得 地, 再 vs 又, 了 vs 过, 会 能 可以, 二 vs 两 and more, "
                "with example sentences and practice.", body, path="pairs", ld=[crumbs("Word pairs")])


# ---------- pinyin ----------

INITIALS = ["", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x",
            "zh", "ch", "sh", "r", "z", "c", "s"]
FINALS = ["a", "o", "e", "i", "er", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "ong",
          "ia", "ie", "iao", "iu", "ian", "in", "iang", "ing", "iong",
          "u", "ua", "uo", "uai", "ui", "uan", "un", "uang", "ueng",
          "ü", "üe", "üan", "ün"]
ZERO = {"yi": "i", "ya": "ia", "ye": "ie", "yao": "iao", "you": "iu", "yan": "ian", "yin": "in",
        "yang": "iang", "ying": "ing", "yong": "iong", "wu": "u", "wa": "ua", "wo": "uo", "wai": "uai",
        "wei": "ui", "wan": "uan", "wen": "un", "wang": "uang", "weng": "ueng", "yu": "ü", "yue": "üe",
        "yuan": "üan", "yun": "ün"}
TONE_MARK = {"a": "āáǎà", "o": "ōóǒò", "e": "ēéěè", "i": "īíǐì", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def split_syl(syl):
    if syl in ZERO:
        return "", ZERO[syl]
    for ini in sorted(INITIALS, key=len, reverse=True):
        if ini and syl.startswith(ini):
            fin = syl[len(ini):]
            if ini in ("j", "q", "x") and fin.startswith("u"):
                fin = "ü" + fin[1:]
            return ini, fin
    return "", syl


def mark_tone(syl, tone):
    if tone not in "1234":
        return syl
    for v in ("a", "e"):
        if v in syl:
            return syl.replace(v, TONE_MARK[v][int(tone) - 1], 1)
    if "ou" in syl:
        return syl.replace("o", TONE_MARK["o"][int(tone) - 1], 1)
    for idx in range(len(syl) - 1, -1, -1):
        if syl[idx] in TONE_MARK:
            return syl[:idx] + TONE_MARK[syl[idx]][int(tone) - 1] + syl[idx + 1:]
    return syl


def tone_pairs(corpus):
    """Two-syllable words from the readings by tone pattern (1-4 x 1-4 + neutral).
    Words with 一 or 不 are skipped: their written tone is not the spoken one."""
    marks = {c: str(k + 1) for v in TONE_MARK.values() for k, c in enumerate(v)}
    freq = {w: len(v) for w, v in corpus.idx.items()}
    pyof = {}
    for w, v in corpus.idx.items():
        t, s, i = v[0]
        pyof[w] = s["t"][i][1]
    cells = {}
    for w, py in pyof.items():
        if len(w) != 2 or not all("一" <= c <= "鿿" for c in w) or "一" in w or "不" in w:
            continue
        if not os.path.exists(os.path.join(ROOT, "media", "audio", "w", w + ".mp3")):
            continue
        tones = [(k, marks[c]) for k, c in enumerate(py) if c in marks]
        if len(tones) == 2:
            key = tones[0][1] + tones[1][1]
        elif len(tones) == 1 and tones[0][0] < len(py) / 2:
            key = tones[0][1] + "5"
        else:
            continue
        cells.setdefault(key, []).append((freq[w], w, py))
    return {k: [x[1:] for x in sorted(v, reverse=True)[:3]] for k, v in cells.items()}


def build_pinyin(corpus):
    have = {}
    for syl, tones in PINYIN.items():
        ini, fin = split_syl(syl)
        have[(ini, fin)] = (syl, tones)
    head = "".join(f'<th scope="col">{esc(i) if i else "–"}</th>' for i in INITIALS)
    rows = []
    for fin in FINALS:
        cells = []
        for ini in INITIALS:
            if (ini, fin) in have:
                syl, tones = have[(ini, fin)]
                chars = " ".join(f"{mark_tone(syl, t)} {c}" for t, c in tones.items())
                cells.append(f'<td><button class="py-cell" type="button" data-s="{esc(syl)}" data-t="{"".join(tones)}" '
                             f'title="{esc(chars)}">{esc(syl)}</button></td>')
            else:
                cells.append("<td></td>")
        rows.append(f'<tr><th scope="row">{esc(fin)}</th>{"".join(cells)}</tr>')
    tp = tone_pairs(corpus)
    tnames = {"1": "1st", "2": "2nd", "3": "3rd", "4": "4th", "5": "neutral"}
    tp_head = "".join(f'<th scope="col">+ {tnames[b]}</th>' for b in "12345")
    tp_rows = []
    for a in "1234":
        tds = []
        for b in "12345":
            words = tp.get(a + b, [])
            inner = "".join(f'<button class="tp-w" type="button" data-w="{esc(w)}"><span lang="zh">{esc(w)}</span><i>{esc(py)}</i></button>'
                            for w, py in words[:2])
            tds.append(f"<td>{inner}</td>")
        tp_rows.append(f'<tr><th scope="row">{tnames[a]} tone</th>{"".join(tds)}</tr>')
    vids = [v for v in (video_by_id("K5z2KzKvfts"), video_by_id("aHRpbTJNevI")) if v]
    vid_html = f'<div class="vgrid pair-video">{"".join(video_card(v) for v in vids)}</div>' if vids else ""
    ma = PINYIN.get("ma", {})
    tone_demo = "".join(
        f'<button class="py-tone" type="button" data-s="ma" data-t="{t}"><b>{mark_tone("ma", t)}</b><span lang="zh">{esc(ma.get(t, ""))}</span><i>{d}</i></button>'
        for t, d in (("1", "high and level"), ("2", "rising"), ("3", "low, dipping"), ("4", "falling")))
    n_clips = sum(len(v) for v in PINYIN.values())
    body = f"""
  <section class="about">
    <h1>Pinyin chart with audio <span style="font-family:var(--serif);color:var(--red)">拼音表</span></h1>
    <p>All {len(PINYIN)} Mandarin syllables in one table. Tap a syllable to hear it in each of its tones
      ({n_clips} recordings), and hover to see a common character for each tone.</p>
  </section>
  <section class="lvl-intro py-intro">
    <h2>The four tones</h2>
    <p>The same syllable means different things in different tones. Tap to hear 妈 mother, 麻 hemp, 马 horse, 骂 to scold.</p>
    <div class="py-tones">{tone_demo}</div>
    {('<h2>Pronunciation lessons</h2><p>zh ch sh, j q x and z c s are where most learners get stuck. Two short lessons from the teacher behind this site:</p>' + vid_html) if vid_html else ''}
  </section>
  <h2 class="home-h py-h">Syllable chart <span class="zh">声母 × 韵母</span></h2>
  <p class="videos-lead">Columns are initials (– means no initial), rows are finals. Empty cells are combinations that do not exist in Mandarin.</p>
  <div class="cmp-wrap py-wrap"><table class="py-table"><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
  <section class="lvl-intro">
    <h2>Tone pairs</h2>
    <p>Most Chinese words have two syllables, so tones are really learned in pairs. Each cell has real words from the
      readings on this site; tap to hear them. Two rules change what you hear: a 3rd tone before another 3rd tone is
      spoken as a 2nd tone (你好 sounds like ní hǎo), and a 3rd tone before any other tone only dips, it does not rise again.</p>
  </section>
  <div class="cmp-wrap"><table class="cmp tp-table"><thead><tr><th></th>{tp_head}</tr></thead><tbody>{''.join(tp_rows)}</tbody></table></div>
  <script>
  (function(){{
    var au=new Audio(), q=[];
    function next(){{ if(!q.length) return; au.src=q.shift(); au.play().catch(function(){{}}); }}
    au.addEventListener("ended", function(){{ setTimeout(next, 180); }});
    function play(list){{ q=list.slice(); au.pause(); next(); }}
    document.addEventListener("click", function(e){{
      var b=e.target.closest(".py-cell,.py-tone,.tp-w"); if(!b) return;
      document.querySelectorAll(".py-on").forEach(function(x){{ x.classList.remove("py-on"); }});
      b.classList.add("py-on");
      if(b.dataset.w) return play(["audio/w/"+encodeURIComponent(b.dataset.w)+".mp3"]);
      play(b.dataset.t.split("").map(function(t){{ return "audio/py/"+encodeURIComponent(b.dataset.s)+t+".mp3"; }}));
    }});
  }})();
  </script>"""
    return page(f"Pinyin Chart with Audio: All Mandarin Syllables and Tones | {SITE['site_name']}",
                f"Interactive pinyin chart: all {len(PINYIN)} Mandarin syllables with audio in every tone, the four "
                f"tones, and tone pairs with real example words.", body, path="pinyin", ld=[crumbs("Pinyin chart")])


# ---------- words by topic ----------

def topic_words(texts):
    by_slug = {t["slug"]: t for t in texts}
    out = {}
    for slug, k in TOPICS["texts"].items():
        t = by_slug.get(slug)
        if not t:
            continue
        for zh, py, en in t["vocab"]:
            cur = out.setdefault(k, {}).get(zh)
            if cur is None or t["level"] < cur[2]:
                out[k][zh] = (py, en, t["level"], t)
    return {k: v for k, v in out.items() if len(v) >= 12}


def build_topic_words(k, words):
    label = TOPICS["labels"].get(k, k)
    rows = "".join(
        f'<tr><th scope="row"><span lang="zh">{esc(zh)}</span></th><td>{esc(py)}</td><td>{esc(en)}</td>'
        f'<td><span class="badge l{lv}">HSK {lv}</span></td>'
        f'<td><a href="texts/{esc(t["slug"])}.html">{esc(t["title_zh"])}</a></td></tr>'
        for zh, (py, en, lv, t) in sorted(words.items(), key=lambda x: (x[1][2], x[1][0])))
    others = "".join(f'<a class="tchip{" on" if kk == k else ""}" href="words-topic-{esc(kk)}.html"'
                     f'{" aria-current=page" if kk == k else ""}>{esc(TOPICS["labels"].get(kk, kk))}</a>'
                     for kk in TOPICS["labels"] if kk in TOPIC_WORDS)
    body = f"""
  <section class="about">
    <h1>{esc(label)}: Chinese vocabulary <span style="font-family:var(--serif);color:var(--red)">主题词汇</span></h1>
    <p>{len(words)} words about {esc(label.lower())}, taken from the key-word lists of the graded readings on this site
      and sorted by HSK level. Each word links to the reading where it is used, so you can see it in a real sentence.</p>
  </section>
  <div class="topic-chips">{others}</div>
  <div class="cmp-wrap"><table class="cmp tw-table"><thead><tr><th scope="col">Word</th><th scope="col">Pinyin</th>
    <th scope="col">Meaning</th><th scope="col">Level</th><th scope="col">Reading</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return page(f"{label} in Chinese: {len(words)} Words with Pinyin | {SITE['site_name']}",
                f"{len(words)} Chinese words for {label.lower()} with pinyin, meaning, HSK level and a graded reading "
                f"that uses each one.", body, path=f"words-topic-{k}", ld=[crumbs(f"{label} vocabulary")])


def build_topics_index():
    cards = "".join(
        f'<a class="pcard" href="words-topic-{esc(k)}.html"><span class="pc-t">{esc(TOPICS["labels"].get(k, k))}</span>'
        f'<span class="pc-s">{len(TOPIC_WORDS[k])} words</span></a>'
        for k in TOPICS["labels"] if k in TOPIC_WORDS)
    body = f"""
  <section class="about">
    <h1>Chinese vocabulary by topic <span style="font-family:var(--serif);color:var(--red)">主题词汇</span></h1>
    <p>Words grouped by what they are about, from food and travel to work and ideas, each linked to a graded reading
      that uses it. For words by HSK level, see the <a href="words.html">word lists</a>.</p>
  </section>
  <section class="pgrid">{cards}</section>"""
    return page(f"Chinese Vocabulary by Topic | {SITE['site_name']}",
                "Chinese vocabulary grouped by topic, with pinyin, meaning, HSK level and a graded reading for every word.",
                body, path="topics", ld=[crumbs("Words by topic")])


# ---------- idioms ----------

def build_idioms(texts, corpus):
    by_slug = {t["slug"]: t for t in texts}
    stories = [(by_slug[s["slug"]], s["idiom"]) for s in IDIOMS["stories"] if s["slug"] in by_slug]
    story_html = "".join(
        f'<a class="pcard" href="texts/{esc(t["slug"])}.html"><span class="pc-w" lang="zh">{esc(i)}</span>'
        f'<span class="pc-t">{esc(t["title_en"].replace("Idiom Story: ", ""))}</span>'
        f'<span class="pc-m">HSK {t["level"]} reading</span></a>' for t, i in stories)
    items = []
    for w in IDIOMS["idioms"]:
        hits = corpus.idx.get(w)
        if not hits:
            continue
        t, s, i = hits[0]
        py, en = s["t"][i][1], re.sub(r"\s*\(idiom\)", "", s["t"][i][2])
        items.append((t["level"], py, w, en, t, s, i))
    items.sort(key=lambda x: (x[0], x[1]))
    groups = {}
    for it in items:
        groups.setdefault(it[0], []).append(it)
    sec = []
    for lv, its in sorted(groups.items()):
        lis = "".join(
            f'<li class="idm" id="i-{esc(w)}"><div class="idm-h"><h3 lang="zh">{esc(w)}</h3><span class="idm-py">{esc(py)}</span>'
            f'<span class="idm-en">{esc(en)}</span></div><ul class="exlist">{ex_html(t, s, i)}</ul></li>'
            for _, py, w, en, t, s, i in its)
        sec.append(f'<h2>Idioms in HSK {lv} readings <span class="lt-n">{len(its)}</span></h2><ul class="idm-list">{lis}</ul>')
    body = f"""
  <section class="about">
    <h1>Chinese idioms (chengyu) and their stories <span style="font-family:var(--serif);color:var(--red)">成语</span></h1>
    <p>Chengyu are four-character idioms, many of them the one-line summary of an old story. Start with the stories,
      told as graded readings, then browse the {len(items)} idioms that appear in the readings on this site, each
      with the sentence it is used in.</p>
  </section>
  <h2 class="home-h">Idiom stories <span class="zh">成语故事</span></h2>
  <section class="pgrid">{story_html}</section>
  <section class="lvl-intro idm-body">{''.join(sec)}</section>"""
    return page(f"Chinese Idioms (Chengyu) with Stories and Examples | {SITE['site_name']}",
                f"Chinese idioms explained: {len(stories)} chengyu stories as graded readings and {len(items)} idioms with "
                f"pinyin, meaning and a real example sentence.", body, path="idioms", ld=[crumbs("Chinese idioms")])


# ---------- festivals ----------

def build_festivals(texts):
    by_slug = {t["slug"]: t for t in texts}
    nav = "".join(f'<a class="tchip" href="#{esc(f["id"])}"><span lang="zh">{esc(f["zh"])}</span></a>' for f in FESTIVALS)
    secs = []
    for f in FESTIVALS:
        gr = "".join(f'<tr><th scope="row" lang="zh">{esc(z)}</th><td>{esc(p)}</td><td>{esc(e)}</td></tr>' for z, p, e in f["greetings"])
        wd = "".join(f'<tr><th scope="row" lang="zh">{esc(z)}</th><td>{esc(p)}</td><td>{esc(e)}</td></tr>' for z, p, e in f["words"])
        rd = [by_slug[s] for s in f.get("readings", []) if s in by_slug]
        rd_html = ("<p class='fe-read'><b>Read about it:</b> " + " · ".join(
            f'<a href="texts/{esc(t["slug"])}.html">{esc(t["title_zh"])} {esc(t["title_en"])} (HSK {t["level"]})</a>' for t in rd) + "</p>") if rd else ""
        vid = video_by_id(f.get("video", "")) if f.get("video") else None
        v_html = f'<div class="vgrid pair-video">{video_card(vid)}</div>' if vid else ""
        secs.append(f"""
      <section class="fest" id="{esc(f['id'])}">
        <h2><span lang="zh">{esc(f['zh'])}</span> {esc(f['en'])} <span class="fe-py">{esc(f['py'])}</span></h2>
        <p class="fe-when"><b>When:</b> {esc(f['when'])}</p>
        <p>{esc(f['about'])}</p>
        {('<h3>What to say</h3><table class="fe-t">' + gr + '</table>') if gr else ''}
        <h3>Words</h3><table class="fe-t">{wd}</table>
        {rd_html}{v_html}
      </section>""")
    body = f"""
  <section class="about">
    <h1>Chinese festivals: greetings and words <span style="font-family:var(--serif);color:var(--red)">节日</span></h1>
    <p>The main Chinese festivals, when they fall, what people say and the words you will hear, with graded readings
      and videos where we have them. Most traditional festivals follow the lunar calendar, so their Western dates move
      from year to year.</p>
  </section>
  <div class="topic-chips">{nav}</div>
  <div class="lvl-intro fest-body">{''.join(secs)}</div>"""
    return page(f"Chinese Festivals: Greetings, Words and When They Are | {SITE['site_name']}",
                "Chinese festivals explained for learners: Spring Festival, Lantern, Qingming, Dragon Boat, Qixi, Mid-Autumn "
                "and more, with greetings, key words and graded readings.", body, path="festivals", ld=[crumbs("Chinese festivals")])


TOPIC_WORDS = {}

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
    into one index, each entry carrying the readings it appears in.

    Keyed by gram_key(), not by the raw pattern string: the same point gets
    written up slightly differently in each reading (都 / 都 — all / both /
    都 (all / both) …), and without folding those together HSK 1 alone shows
    「都」six times. One entry per point, keeping the fullest wording of the
    three fields and pooling every reading it turned up in."""
    gram = {}
    for t in sorted(texts, key=lambda x: (x["level"], x["slug"])):
        for g in t.get("grammar", []):
            pat = (g.get("p") or "").strip()
            if not pat:
                continue
            e = gram.setdefault(gram_key(pat), {"p": pat, "e": "", "x": "",
                                                "lvl": t["level"], "srcs": []})
            # longest wins: the fullest write-up of this point across readings
            for field, val in (("p", pat), ("e", g.get("e", "")), ("x", g.get("x", ""))):
                if len(val or "") > len(e[field]):
                    e[field] = val
            e["srcs"].append((t["slug"], t["title_zh"], t["title_en"]))
    return gram


def gram_item(pat, d, show_lvl=False):
    srcs = "".join(
        f'<a href="texts/{esc(slug)}.html">{esc(zh)}</a>'
        for slug, zh, en in d["srcs"][:4])
    extra = f' +{len(d["srcs"]) - 4}' if len(d["srcs"]) > 4 else ""
    bdg = (f'<span class="badge l{d["lvl"]}">HSK {d["lvl"]}</span>'
           if show_lvl else "")
    q = GRAM_Q.get(gram_key(pat))
    # The pattern itself is the heading, with a stable anchor, so an answer
    # engine looking for one point ("给 + somebody + object") can land on and
    # cite exactly that entry instead of a 180-item page.
    gid = "g-" + re.sub(r"[^0-9a-z\u3400-\u9fff]+", "-", gram_key(pat)).strip("-")
    return (f'<div class="gitem" id="{esc(gid)}">'
            f'<h3 class="gp">{esc(pat)}{bdg}</h3>'
            + (f'<p class="gq">{esc(q)}</p>' if q else "")
            + f'<p>{esc(d["e"])}</p>'
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
    <p>Looking for a particular kind of sentence rather than a level?
      <a href="grammar-topics.html">Browse grammar by topic</a> — if, but, because,
      questions, comparisons, 把 and 被.</p>
  </section>
  {sec_chips(0, "grammar-hsk", "grammar.html")}
  <section class="lvlgrid">{cards}</section>"""
    return page(f"Chinese Grammar Points by HSK Level (1-6) | {SITE['site_name']}",
                f"{len(gram)} Chinese grammar patterns with explanations and example "
                f"sentences from free graded readings, organised by HSK level.",
                body, path="grammar")


def build_grammar_level(gram, lvl):
    mine = sorted((k for k in gram if gram[k]["lvl"] == lvl),
                  key=lambda k: gram[k]["p"])
    items = "".join(gram_item(gram[k]["p"], gram[k]) for k in mine)
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


def gram_key(pat):
    """把同一个语法点的不同写法归成一个 key。
    「一边……一边……」「一边 A，一边 B」「一边…，一边…」都是同一件事,
    不归一化的话它们会在页面上占三行。"""
    s = re.split(r"\s+[\u2014\u2013-]\s+", pat)[0]
    s = re.split(r"[\uff08(]", s)[0].strip().lower()
    s = re.sub(r"verb|\u52a8\u8bcd", "v", s)
    s = re.sub(r"adjective|adj\.?|\u5f62\u5bb9\u8bcd", "adj", s)
    s = re.sub(r"noun|\u540d\u8bcd", "n", s)
    s = re.sub(r"\bsb\b|\bperson\b|someone", "sb", s)
    s = re.sub(r"complement|\u8865\u8bed", "comp", s)
    s = re.sub(r"[\u2026.]{2,}|[\u2026]", "", s)
    s = re.sub(r"(?<![a-z])[ab](?![a-z])", "", s)
    return re.sub(r"[,\uff0c\u3001\uff1f?\u3002\uff01!+\s]", "", s)


def collect_topics(texts, cfg):
    """按功能给核心语法点分组。key->topic 的映射是 content/grammar-topics.json
    里人工定稿的白名单 —— 正则自动分类会把「太…了」判成完成体的「了」、
    把「谁……都不」判成疑问句,在教中文的站上这种错很难看。
    没收进白名单的语法点不会丢,它们仍然在 grammar-hskN 页面里。"""
    key2topic = {k: t["id"] for t in cfg["topics"] for k in t["keys"]}
    buckets = {t["id"]: {} for t in cfg["topics"]}
    for t in sorted(texts, key=lambda x: (x["level"], x["slug"])):
        for g in t.get("grammar", []):
            pat = (g.get("p") or "").strip()
            if not pat:
                continue
            k = gram_key(pat)
            tid = key2topic.get(k)
            if not tid:
                continue
            e = buckets[tid].setdefault(k, {"pat": pat, "e": "", "x": "",
                                            "lvl": t["level"], "srcs": []})
            if not e["e"]:
                e["e"] = g.get("e", "")
            if not e["x"]:
                e["x"] = g.get("x", "")
            if t["level"] < e["lvl"]:
                e["lvl"] = t["level"]
                e["pat"] = pat
            e["srcs"].append((t["slug"], t["title_zh"], t["title_en"]))
    return buckets


def build_topic_index(cfg, buckets):
    live = [t for t in cfg["topics"] if buckets[t["id"]]]
    total = sum(len(buckets[t["id"]]) for t in live)
    items = "".join(
        f'<div class="gitem">'
        f'<div class="gp"><a href="grammar-{t["id"]}.html">{esc(t["title"])}</a></div>'
        f'<p>{esc(t["blurb"])}</p>'
        f'<div class="g-src">{len(buckets[t["id"]])} patterns &middot; '
        f'<a href="grammar-{t["id"]}.html">open</a></div></div>'
        for t in live)
    body = f"""
  <section class="about">
    <h1>Chinese Grammar by Topic
      <span style="font-family:var(--serif);color:var(--red)">\u6309\u7c7b\u578b</span></h1>
    <p>The same {total} core grammar patterns as the HSK pages, but grouped by what
      you are trying to say rather than by which exam level introduces them. If you
      want to know how Chinese handles <em>if</em>, or <em>but</em>, or asking a
      question, start here.</p>
    <p>Every pattern is explained in English and linked to the reading it came from,
      so you can see it working in a real sentence before you try to use it. Browsing
      by level instead? <a href="grammar.html">Grammar by HSK level</a>.</p>
  </section>
  <div class="gwrap">{items}</div>"""
    return page(
        f"Chinese Grammar by Topic \u2014 {len(live)} Ways to Say What You Mean | {SITE['site_name']}",
        "Chinese grammar grouped by what you want to say: if, but, because, "
        "questions, comparisons, \u628a and \u88ab. Each pattern explained in English "
        "with a real example sentence.",
        body, path="grammar-topics")


def build_topic_page(topic, entries):
    ks = sorted(entries, key=lambda k: (entries[k]["lvl"], -len(entries[k]["srcs"])))
    items = "".join(gram_item(entries[k]["pat"], entries[k], show_lvl=True) for k in ks)
    lvls = sorted({entries[k]["lvl"] for k in ks})
    span = (f"HSK {lvls[0]}" if len(lvls) == 1
            else f"HSK {lvls[0]}\u2013{lvls[-1]}")
    body = f"""
  <article>
    <div class="reader-banner" style="--sc:{LEVEL_COLORS[lvls[0]]}" data-char="\u6cd5">
      <span class="feat-tag">Grammar by topic</span>
      <h1>{esc(topic['title'])}</h1>
      <div class="b-en">{esc(topic['blurb'])}</div>
    </div>
    <div class="gwrap">{items}</div>
    <section class="lvl-intro">
      <h2>How to use this page</h2>
      <p>These {len(ks)} patterns all do the same job in Chinese, so they are worth
        seeing side by side \u2014 the differences between them are easier to feel
        when they are next to each other than when they are spread across six
        HSK levels. They range from {span}.</p>
      <p class="lvl-how"><strong>Grammar sticks through reading, not through lists.</strong>
        Each entry links to the reading it was taken from. Skim the page, then go read
        one of them and come back when a sentence stops making sense.</p>
      <p><a href="grammar-topics.html">\u2190 All grammar topics</a>
        &middot; <a href="grammar.html">Grammar by HSK level</a></p>
    </section>
  </article>"""
    return page(f"{topic['title']} | {SITE['site_name']}",
                topic["blurb"] + f" {len(ks)} patterns, each with a real example "
                "sentence from a free graded reading.",
                body, path=f"grammar-{topic['id']}")


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
  <section class="about about-narrow">
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
  <section class="about about-narrow" style="text-align:center; padding:72px 0 84px">
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
    if VIDEOS:
        open(os.path.join(OUT, "videos.html"), "w", encoding="utf-8").write(build_videos())
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
    open(os.path.join(OUT, "hsk-levels.html"), "w", encoding="utf-8").write(
        build_levels_compare(texts, gram))
    open(os.path.join(OUT, "graded-readers.html"), "w", encoding="utf-8").write(
        build_graded_readers(texts))
    open(os.path.join(OUT, "quiz.html"), "w", encoding="utf-8").write(build_quiz_index(texts))
    corpus = Corpus(texts)
    open(os.path.join(OUT, "pairs.html"), "w", encoding="utf-8").write(build_pairs_index())
    for pr in PAIRS:
        open(os.path.join(OUT, f"pairs-{pr['id']}.html"), "w", encoding="utf-8").write(build_pair(corpus, pr))
    if PINYIN:
        open(os.path.join(OUT, "pinyin.html"), "w", encoding="utf-8").write(build_pinyin(corpus))
    TOPIC_WORDS.update(topic_words(texts))
    open(os.path.join(OUT, "topics.html"), "w", encoding="utf-8").write(build_topics_index())
    for k, words in TOPIC_WORDS.items():
        open(os.path.join(OUT, f"words-topic-{k}.html"), "w", encoding="utf-8").write(build_topic_words(k, words))
    open(os.path.join(OUT, "idioms.html"), "w", encoding="utf-8").write(build_idioms(texts, corpus))
    open(os.path.join(OUT, "festivals.html"), "w", encoding="utf-8").write(build_festivals(texts))
    for lvl in range(1, 7):
        open(os.path.join(OUT, f"quiz-hsk{lvl}.html"), "w", encoding="utf-8").write(
            build_quiz_level(texts, lvl))
    for lvl in range(1, 7):
        open(os.path.join(OUT, f"grammar-hsk{lvl}.html"), "w",
             encoding="utf-8").write(build_grammar_level(gram, lvl))
    # 按功能分类的语法索引:同一批语法点,换成"你想说什么"的切法
    tcfg, tlive = None, []
    tpath = os.path.join(ROOT, "content", "grammar-topics.json")
    if os.path.exists(tpath):
        tcfg = json.load(open(tpath, encoding="utf-8"))
        tbuckets = collect_topics(texts, tcfg)
        tlive = [t for t in tcfg["topics"] if tbuckets[t["id"]]]
        open(os.path.join(OUT, "grammar-topics.html"), "w", encoding="utf-8").write(
            build_topic_index(tcfg, tbuckets))
        for t in tlive:
            open(os.path.join(OUT, f'grammar-{t["id"]}.html'), "w",
                 encoding="utf-8").write(build_topic_page(t, tbuckets[t["id"]]))
    open(os.path.join(OUT, "wordbook.html"), "w", encoding="utf-8").write(build_wordbook())
    open(os.path.join(OUT, "progress.html"), "w", encoding="utf-8").write(build_progress(texts))
    for f in ("manifest.webmanifest", "sw.js"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))
    # IndexNow 的所有权凭证:必须能从站点根访问到 https://<domain>/<key>.txt
    for f in os.listdir(ROOT):
        if f.endswith(".txt") and len(f) == 36 and f[:-4].isalnum():
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
        rel = pick_related(t, by_level.get(t["level"], []))
        open(os.path.join(OUT, "texts", f"{t['slug']}.html"), "w",
             encoding="utf-8").write(
                 build_reader(t, next_map.get(t["slug"]), rel))
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
        if VIDEOS:
            urls.append(("videos", "0.7", os.path.getmtime(VIDEOS_PATH)))
        urls += [("hsk-levels", "0.7", newest), ("graded-readers", "0.6", os.path.getmtime(__file__)),
                 ("quiz", "0.6", newest)]
        urls += [(f"quiz-hsk{lvl}", "0.7", newest) for lvl in range(1, 7)]
        urls += [("pinyin", "0.8", newest), ("pairs", "0.7", newest), ("topics", "0.6", newest),
                 ("idioms", "0.7", newest), ("festivals", "0.7", newest)]
        urls += [(f"pairs-{pr['id']}", "0.7", newest) for pr in PAIRS]
        urls += [(f"words-topic-{k}", "0.6", newest) for k in TOPIC_WORDS]
        for lvl in range(1, 7):
            urls.append((f"words-hsk{lvl}", "0.6", newest))
            urls.append((f"grammar-hsk{lvl}", "0.6", newest))
        if tlive:
            urls.append(("grammar-topics", "0.7", newest))
            urls += [(f'grammar-{t["id"]}', "0.6", newest) for t in tlive]
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
