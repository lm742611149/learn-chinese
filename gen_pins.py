#!/usr/bin/env python3
"""为 Pinterest 生成 1000x1500 的词汇图卡(每篇课文一张,含该课 5 个生词)。

用法: python3 gen_pins.py            默认取每级最新 5 篇 → dist/pins/
      python3 gen_pins.py hsk1 12    指定级别和张数
图上不放 URL 以外的任何广告语;链接靠 Pinterest 的 destination link 走。
"""
import json, glob, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 1500
BG, INK, ACCENT, MUTED = "#fffdf8", "#1a1a1a", "#b4643c", "#7a7a7a"
FONT = "/System/Library/Fonts/PingFang.ttc"
OUT = "dist/pins"

def f(size, idx=2):                       # idx: 2=Regular 4=Medium 6=Semibold
    return ImageFont.truetype(FONT, size, index=idx)

def center(d, y, text, font, fill):
    w = d.textbbox((0, 0), text, font=font)[2]
    d.text(((W - w) // 2, y), text, font=font, fill=fill)

def pin(t, path):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    center(d, 78, f"HSK {t['level']}", f(34, 4), ACCENT)
    center(d, 132, t["title_en"], f(52, 6), INK)
    d.line([(W // 2 - 60, 232), (W // 2 + 60, 232)], fill=ACCENT, width=3)

    y = 312
    for w, py, en in t["vocab"][:5]:
        center(d, y, w, f(84, 4), INK)
        center(d, y + 112, py, f(38), ACCENT)
        center(d, y + 164, en, f(32), MUTED)
        y += 198

    d.rectangle([(0, H - 116), (W, H)], fill=ACCENT)
    center(d, H - 88, "readmandarin.com", f(40, 6), "#fffdf8")
    center(d, H - 40, "free HSK graded readings · no signup", f(24), "#f6e0d2")

    os.makedirs(OUT, exist_ok=True)
    im.save(path, quality=92)

if __name__ == "__main__":
    lv = sys.argv[1] if len(sys.argv) > 1 else None
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    texts = [json.load(open(p)) for p in sorted(glob.glob("content/texts/*.json"))]
    if lv:
        texts = [t for t in texts if t["slug"].startswith(lv)][:n]
    else:
        texts = [t for l in range(1, 7)
                 for t in [x for x in texts if x["level"] == l][:n]]
    for t in texts:
        p = f"{OUT}/{t['slug']}.jpg"
        pin(t, p)
    print(f"{len(texts)} 张 → {OUT}/")
