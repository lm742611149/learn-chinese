#!/usr/bin/env python3
"""从 content/texts/*.json 生成每级一个 Anki 牌组(.apkg)。

用法: python3 export_anki.py            生成全部 6 级到 dist/anki/
      python3 export_anki.py 1 2        只生成指定级别

每张卡 = 一个生词,背面带该词在课文里的真实例句 + 出处链接(readmandarin.com/texts/<slug>)。
有词级音频(media/audio/w/<词>.mp3)的额外生成一张听力卡。
牌组/模板 ID 由名称哈希而来,固定不变 —— 重新导出是"更新"而不是新建牌组。
"""
import json, glob, os, sys, hashlib, collections
import genanki

SITE = "https://readmandarin.com"
AUDIO_W = "media/audio/w"
OUT = "dist/anki"

def sid(s):                      # 稳定 ID(genanki 要 31 位以内正整数)
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

CSS = """
.card { font-family: -apple-system, "PingFang SC", "Helvetica Neue", sans-serif;
        font-size: 20px; text-align: center; color: #1a1a1a; background: #fffdf8; }
.nightMode.card { color: #e8e8e8; background: #1c1c1e; }
.hanzi { font-size: 64px; line-height: 1.3; margin: 12px 0; }
.py { font-size: 24px; color: #b4643c; margin-bottom: 4px; }
.nightMode .py { color: #e2996f; }
.en { font-size: 22px; margin-bottom: 18px; }
hr { border: 0; border-top: 1px solid #ddd; margin: 18px 0; }
.nightMode hr { border-top-color: #444; }
.ex { font-size: 22px; line-height: 1.6; }
.ex b { color: #b4643c; }
.nightMode .ex b { color: #e2996f; }
.exen { font-size: 17px; color: #666; margin-top: 6px; }
.nightMode .exen { color: #aaa; }
.src { font-size: 13px; margin-top: 20px; }
.src a { color: #888; text-decoration: none; }
"""

BACK = """{{FrontSide}}<hr>
<div class="py">{{Pinyin}}</div>
<div class="en">{{English}}</div>
{{#Example}}<div class="ex">{{Example}}</div>
<div class="exen">{{ExampleEn}}</div>{{/Example}}
<div class="src">from <a href="{{SourceUrl}}">{{Source}}</a> · readmandarin.com</div>"""

MODEL = genanki.Model(
    sid("readmandarin-hsk-vocab-v1"),
    "readmandarin HSK vocabulary",
    fields=[{"name": n} for n in
            ("Hanzi", "Pinyin", "English", "Example", "ExampleEn",
             "Source", "SourceUrl", "Audio")],
    css=CSS,
    templates=[
        {"name": "Recognition",
         "qfmt": '<div class="hanzi">{{Hanzi}}</div>{{#Audio}}{{Audio}}{{/Audio}}',
         "afmt": BACK},
        {"name": "Listening",
         "qfmt": '{{#Audio}}<div style="font-size:40px">🔊</div>{{Audio}}{{/Audio}}',
         "afmt": BACK},
    ])


def load():
    """→ {level: [(词, 拼音, 英文, 例句html, 例句英文, 课文标题, url, 音频文件名)]}"""
    texts = [json.load(open(f)) for f in sorted(glob.glob("content/texts/*.json"))]
    seen, per = set(), collections.defaultdict(list)
    for t in texts:
        # 该课文里每个词的最短例句
        best = {}
        for s in t["sentences"]:
            words = [tok[0] for tok in s["t"] if len(tok) > 1]
            for w in set(words):
                if w not in best or len(s["en"]) < len(best[w][1]):
                    best[w] = (s, s["en"])
        for w, py, en in t["vocab"]:
            if w in seen:            # 跨课文去重,保留首次(级别更低/更早)出现
                continue
            seen.add(w)
            ex = exen = ""
            if w in best:
                s = best[w][0]
                ex = "".join(
                    (f"<b>{tok[0]}</b>" if tok[0] == w else tok[0]) for tok in s["t"])
                exen = s["en"]
            mp3 = f"{w}.mp3" if os.path.exists(f"{AUDIO_W}/{w}.mp3") else ""
            per[t["level"]].append(
                (w, py, en, ex, exen,
                 t["title_en"] or t["title_zh"], f"{SITE}/texts/{t['slug']}", mp3))
    return per


def build(level, rows):
    name = (f"HSK {level} Chinese Vocabulary with Example Sentences "
            f"(readmandarin.com)")
    deck = genanki.Deck(sid(f"readmandarin-hsk{level}-v1"), name,
        description=(
            f"{len(rows)} HSK {level} words, each with a real example sentence taken "
            f"from a free graded reading on readmandarin.com, plus native audio.<br><br>"
            f"Every card links back to the full reading it came from, so you can see "
            f"the word in context with pinyin, tap-for-definition and audio: "
            f'<a href="{SITE}/hsk{level}">{SITE}/hsk{level}</a><br><br>'
            f"Free, no account needed."))
    media = []
    for w, py, en, ex, exen, src, url, mp3 in rows:
        deck.add_note(genanki.Note(
            model=MODEL, guid=genanki.guid_for("readmandarin", w),
            fields=[w, py, en, ex, exen, src, url,
                    f"[sound:{mp3}]" if mp3 else ""]))
        if mp3:
            media.append(f"{AUDIO_W}/{mp3}")
    os.makedirs(OUT, exist_ok=True)
    path = f"{OUT}/readmandarin-hsk{level}.apkg"
    genanki.Package(deck, media_files=media).write_to_file(path)
    return path, len(rows), len(media)


if __name__ == "__main__":
    want = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5, 6]
    per = load()
    for lv in want:
        p, n, m = build(lv, per[lv])
        print(f"HSK {lv}: {n} 张卡 / {m} 个音频 → {p} "
              f"({os.path.getsize(p)/1024/1024:.1f} MB)")
