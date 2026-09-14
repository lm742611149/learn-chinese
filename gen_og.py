#!/usr/bin/env python3
"""重新生成 assets/og-cover.png —— 全站的分享封面(FB/X/Pinterest/搜索结果都吃它)。

    python3 gen_og.py        # 数字自动从 content/texts/ 数,不用手改

上一版是手工做的,篇数写死在图里,涨到 415 篇了图上还印着 195 —— 每次分享
都在少报一半内容。以后加完课文跑一次这个脚本再 build 就行。
"""
import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
PAPER, INK, INK2 = "#f7f2ea", "#221d18", "#4d453c"
RED, CHIP = "#c73e2a", "#efe7da"
OUT = "assets/og-cover.png"

SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SERIF_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
SERIF_BI = "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf"
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"   # index 0 = Songti SC Black
SANS = "/System/Library/Fonts/PingFang.ttc"


def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def text_w(d, s, f):
    return d.textbbox((0, 0), s, font=f)[2]


def build(n_texts):
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)

    # 右侧巨大的"读"水印,延续站内 hero / 海报的视觉语言
    wm = font(SONG, 620)
    d.text((690, -110), "读", font=wm, fill="#f0e4d6")

    # 左边一条红色书脊
    d.rectangle([(0, 0), (13, H)], fill=RED)

    # logo 方块
    d.rounded_rectangle([(80, 138), (182, 240)], radius=22, fill=RED)
    lf = font(SONG, 62)
    lw = text_w(d, "读", lf)
    d.text((131 - lw // 2, 158), "读", font=lf, fill="#fffdf9")

    # 站名 + 一句话
    d.text((80, 268), "Read Mandarin", font=font(SERIF_B, 74), fill=INK)

    y = 372
    a = font(SERIF, 34)
    b = font(SERIF_BI, 34)
    x = 80
    for s, f, fill in (("Real Chinese in ", a, INK2), ("5 minutes", b, RED),
                       (" a day", a, INK2)):
        d.text((x, y), s, font=f, fill=fill)
        x += text_w(d, s, f)

    # 事实 chip —— 篇数自动
    chips = [f"{n_texts} graded readings", "HSK 1–6", "Pinyin + audio", "Free"]
    cf = font(SANS, 25, index=4)
    x, y = 80, 452
    for c in chips:
        w = text_w(d, c, cf)
        d.rounded_rectangle([(x, y), (x + w + 44, y + 54)], radius=27, fill=CHIP)
        d.text((x + 22, y + 13), c, font=cf, fill=INK2)
        x += w + 44 + 16

    d.text((80, 552), "readmandarin.com", font=font(SANS, 24, index=4), fill="#94897b")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT)
    print(f"{OUT} <- {n_texts} readings")


if __name__ == "__main__":
    n = len(glob.glob("content/texts/*.json"))
    # 顺手确认 JSON 都读得动,免得把坏数据数进去
    for p in glob.glob("content/texts/*.json"):
        json.load(open(p, encoding="utf-8"))
    build(n)
