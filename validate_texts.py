#!/usr/bin/env python3
"""校验 content/texts/*.json 是否符合课文 schema。用法: python3 validate_texts.py [slug片段...]"""
import json, glob, sys, re, os

ROOT = os.path.dirname(os.path.abspath(__file__))
SENT_RANGE = {1: (4, 6), 2: (5, 7), 3: (6, 8), 4: (6, 9), 5: (7, 10), 6: (7, 10)}
PUNCT = set("，。？！、；：“”‘’《》—…（）")
TONE = "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ"

def check(path):
    errs, warns = [], []
    name = os.path.basename(path)
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"JSON 解析失败: {e}"], []

    for k in ("slug", "level", "title_zh", "title_py", "title_en", "audio",
              "sentences", "vocab", "quiz", "grammar"):
        if k not in d:
            errs.append(f"缺字段 {k}")
    if errs:
        return errs, warns

    if d["slug"] != name[:-5]:
        errs.append(f"slug({d['slug']}) 与文件名不符")
    lv = d["level"]
    if not isinstance(lv, int) or not 1 <= lv <= 6:
        errs.append(f"level 非法: {lv}")
        return errs, warns
    if not d["slug"].startswith(f"hsk{lv}-"):
        errs.append("slug 前缀与 level 不符")

    # 句数
    lo, hi = SENT_RANGE[lv]
    n = len(d["sentences"])
    if not lo <= n <= hi:
        errs.append(f"句数 {n} 不在 HSK{lv} 要求 {lo}-{hi}")

    # 句子结构
    for i, s in enumerate(d["sentences"], 1):
        if "t" not in s or "en" not in s:
            errs.append(f"第{i}句缺 t/en"); continue
        if not s["en"].strip():
            errs.append(f"第{i}句 en 为空")
        for j, tok in enumerate(s["t"]):
            if not isinstance(tok, list):
                errs.append(f"第{i}句 token{j} 不是数组"); continue
            if len(tok) == 1:
                if not all(c in PUNCT for c in tok[0]):
                    errs.append(f"第{i}句 单元素token 非标点: {tok[0]}")
            elif len(tok) == 3:
                zh, py, en = tok
                if any(c in PUNCT for c in zh):
                    errs.append(f"第{i}句 词token含标点: {zh}")
                if re.search(r"[0-9]", py):
                    errs.append(f"第{i}句 拼音带数字调号: {zh}/{py}")
                if not py.strip() or not en.strip():
                    errs.append(f"第{i}句 拼音或释义为空: {zh}")
                if re.search(r"[一-鿿]", py):
                    errs.append(f"第{i}句 拼音里有汉字: {zh}/{py}")
                if zh in ("不",) and py not in ("bù", "bú"):
                    warns.append(f"第{i}句 不={py}")
            else:
                errs.append(f"第{i}句 token{j} 长度 {len(tok)}(应为1或3): {tok}")

    # vocab
    v = d["vocab"]
    if len(v) != 6:
        errs.append(f"vocab {len(v)} 个(应为6)")
    for w in v:
        if not isinstance(w, list) or len(w) != 3:
            errs.append(f"vocab 条目格式错: {w}")
        elif re.search(r"[0-9]", w[1]):
            errs.append(f"vocab 拼音带数字: {w[0]}/{w[1]}")

    # quiz
    q = d["quiz"]
    if len(q) != 3:
        errs.append(f"quiz {len(q)} 题(应为3)")
    cs = []
    for i, item in enumerate(q, 1):
        if set(item) < {"q", "a", "c"}:
            errs.append(f"quiz{i} 缺字段"); continue
        if len(item["a"]) != 3:
            errs.append(f"quiz{i} 选项 {len(item['a'])} 个(应为3)")
        if not isinstance(item["c"], int) or not 0 <= item["c"] < len(item["a"]):
            errs.append(f"quiz{i} c 索引越界: {item['c']}")
        else:
            cs.append(item["c"])
    if len(cs) == 3 and len(set(cs)) == 1:
        warns.append(f"quiz 答案索引全是 {cs[0]}")

    # grammar
    g = d["grammar"]
    if not 2 <= len(g) <= 3:
        errs.append(f"grammar {len(g)} 条(应为2-3)")
    for i, item in enumerate(g, 1):
        if set(item) < {"p", "e", "x"}:
            errs.append(f"grammar{i} 缺 p/e/x")

    # 标题
    if not any(c in TONE for c in d["title_py"]) and re.search(r"[一-鿿]", d["title_zh"]):
        warns.append(f"title_py 无声调符号: {d['title_py']}")
    if re.search(r"[一-鿿]", d["title_py"]):
        errs.append("title_py 里有汉字")

    return errs, warns

targets = sys.argv[1:]
files = sorted(glob.glob(os.path.join(ROOT, "content/texts/*.json")))
if targets:
    files = [f for f in files if any(t in os.path.basename(f) for t in targets)]

bad = 0
for f in files:
    e, w = check(f)
    if e or w:
        print(f"\n=== {os.path.basename(f)}")
        for x in e:
            print("  ✗", x)
        for x in w:
            print("  ⚠", x)
    if e:
        bad += 1
print(f"\n共 {len(files)} 篇,{bad} 篇有错误。")
sys.exit(1 if bad else 0)
