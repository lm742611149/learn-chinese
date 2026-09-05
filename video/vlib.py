#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""课文视频的画面渲染层：字幕条、片头卡、生词卡。

全部输出 RGBA 全画布 PNG（透明底），交给 ffmpeg overlay 叠到视频上。
数据源是 content/texts/<slug>.json —— 每个 token 形如 [汉字, 拼音, 释义]
或 [标点]，因此拼音可以逐词对齐到汉字正上方，而不是整句糊一行。

版面按 720x1280 的设计稿写死，再用 px() 缩放到实际输出分辨率，
所以改 W/H 出 1080p 时字幕是原生渲染的，不是把 720p 字幕放大。
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/System/Library/Fonts/PingFang.ttc"
# PingFang.ttc 内的字重索引（SC = 简体）
SC_LIGHT, SC_REG, SC_MED, SC_BOLD = 11, 2, 5, 8

W, H = 1080, 1920          # 输出分辨率
BASE_W = 720               # 设计稿基准宽


def px(v):
    """设计稿像素 → 实际输出像素。"""
    return int(round(v * W / BASE_W))


# 配色
WHITE = (255, 255, 255, 255)
PINYIN = (255, 233, 168, 255)      # 浅黄
ENGLISH = (216, 222, 230, 255)     # 灰白
SHADOW = (0, 0, 0, 255)
SPEAKER = {                        # 对话镜头的说话人色（汉字行）
    "girl": (255, 255, 255, 255),
    "man": (191, 227, 255, 255),
}

# 全角标点的字形只占 advance 的左下角，按 advance 排版会撑出大洞
NARROW = "，。、；：！？"

_cache = {}


def font(size, index=SC_MED):
    key = (size, index)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONT, size, index=index)
    return _cache[key]


def _w(draw, text, f):
    return draw.textbbox((0, 0), text, font=f)[2]


def _bg(img):
    """深色渐变底，给片头/片尾卡用。"""
    d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)],
               fill=(int(14 + 24 * t), int(18 + 30 * t), int(28 + 46 * t), 255))
    return d


def _wrap_tokens(draw, tokens, f_zh, f_py, max_w, gap):
    """按 token 折行，返回 [[(zh, py, unit_w, is_punct), ...], ...]。标点不落行首。"""
    lines, cur, cur_w = [], [], 0
    for tok in tokens:
        zh = tok[0]
        py = tok[1] if len(tok) >= 2 else ""
        is_punct = not py
        uw = max(_w(draw, zh, f_zh), _w(draw, py, f_py))
        if is_punct and zh in NARROW:
            uw *= 0.55
        if cur and not is_punct and cur_w + gap + uw > max_w:
            lines.append(cur)
            cur, cur_w = [], 0
        # 标点紧贴前一个词，不吃 gap
        cur_w += uw if is_punct else (uw + gap)
        cur.append((zh, py, uw, is_punct))
    if cur:
        lines.append(cur)
    return lines


def _wrap_plain(draw, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if cur and _w(draw, trial, f) > max_w:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def render_scrim(height=None, strength=190):
    """底部渐变压暗层：保证字幕在任何画面上都读得清，也压掉平台 UI 干扰区。"""
    height = height or px(330)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(height):
        y = H - height + i
        a = int(strength * (i / height) ** 1.6)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    return img


def quote_only(sentence):
    """取出「我说：“…”」里引号内的部分。

    对话镜头的配音只念引号内容（为了对口型），字幕必须跟着裁，否则音画不同步。
    """
    toks = sentence["t"]
    try:
        a = next(i for i, t in enumerate(toks) if t[0] == "“")
        b = next(i for i in range(len(toks) - 1, -1, -1) if toks[i][0] == "”")
    except StopIteration:
        return sentence
    en = sentence.get("en", "")
    for lq, rq in (("“", "”"), ('"', '"')):
        if lq in en and rq in en[en.index(lq) + 1:]:
            en = en[en.index(lq) + 1:en.rindex(rq)]
            break
    return {"t": toks[a + 1:b], "en": en}


def render_subtitle(sentence, speaker="girl", bottom=None, max_w=None):
    """三行式字幕条：拼音（逐词对齐）/ 汉字 / 英文。返回全画布 RGBA。"""
    bottom = bottom or px(170)
    max_w = max_w or px(660)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    f_zh = font(px(46), SC_BOLD)
    f_py = font(px(26), SC_REG)
    f_en = font(px(27), SC_REG)
    gap, py_h, zh_h, en_h = px(10), px(34), px(60), px(36)
    sw_zh, sw_sm = px(4), px(3)

    zh_color = SPEAKER.get(speaker, WHITE)
    lines = _wrap_tokens(d, sentence["t"], f_zh, f_py, max_w, gap)
    en_lines = _wrap_plain(d, sentence.get("en", ""), f_en, max_w)

    block_h = len(lines) * (py_h + zh_h) + len(en_lines) * en_h + px(10)
    y = H - bottom - block_h

    for line in lines:
        total = sum(u if p else u + gap for _, _, u, p in line) - gap
        x = (W - total) / 2
        for zh, py, uw, is_punct in line:
            cx = x + uw / 2
            if py:
                d.text((cx, y), py, font=f_py, fill=PINYIN, anchor="ma",
                       stroke_width=sw_sm, stroke_fill=SHADOW)
            # 全角标点靠左绘制，抵消其右侧空白
            d.text((x if is_punct else cx, y + py_h), zh, font=f_zh, fill=zh_color,
                   anchor="la" if is_punct else "ma", stroke_width=sw_zh, stroke_fill=SHADOW)
            x += uw if is_punct else uw + gap
        y += py_h + zh_h

    y += px(10)
    for ln in en_lines:
        d.text((W // 2, y), ln, font=f_en, fill=ENGLISH, anchor="ma",
               stroke_width=sw_sm, stroke_fill=SHADOW)
        y += en_h
    return img


def render_title_card(text):
    """片头卡：HSK 级别 + 中文标题 + 拼音 + 英文。"""
    img = Image.new("RGBA", (W, H), (14, 18, 28, 255))
    d = _bg(img)
    cy = H // 2
    d.text((W // 2, cy - px(190)), f"HSK {text['level']}", font=font(px(30), SC_MED),
           fill=PINYIN, anchor="ma")
    d.text((W // 2, cy - px(120)), text["title_zh"], font=font(px(88), SC_BOLD),
           fill=WHITE, anchor="ma")
    d.text((W // 2, cy + px(10)), text["title_py"], font=font(px(38), SC_REG),
           fill=PINYIN, anchor="ma")
    d.text((W // 2, cy + px(70)), text["title_en"], font=font(px(32), SC_LIGHT),
           fill=ENGLISH, anchor="ma")
    d.line([(W // 2 - px(60), cy - px(40)), (W // 2 + px(60), cy - px(40))],
           fill=(255, 233, 168, 120), width=max(1, px(2)))
    return img


def render_vocab_card(text, highlight=-1):
    """片尾生词卡；highlight 为当前朗读到的词序号（-1 = 全部常态）。"""
    img = Image.new("RGBA", (W, H), (14, 18, 28, 255))
    d = _bg(img)
    d.text((W // 2, px(150)), "生词 · New Words", font=font(px(34), SC_MED),
           fill=PINYIN, anchor="ma")

    y = px(290)
    for i, v in enumerate(text["vocab"][:7]):
        on = (i == highlight)
        d.text((px(70), y), v[0], font=font(px(56 if on else 50), SC_BOLD),
               fill=PINYIN if on else WHITE)
        d.text((px(70), y + px(66)), v[1], font=font(px(26), SC_REG), fill=PINYIN)
        d.text((px(330), y + px(14)), v[2], font=font(px(28), SC_LIGHT), fill=ENGLISH)
        y += px(118)
    return img
