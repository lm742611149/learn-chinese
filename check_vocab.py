#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查课文用词是否超出本级"已验证词池"。

词池 = 站上现有的本级及以下课文用过的所有词(动态计算,不依赖外部词表)。
被检查的课文自身会从池子里排除,否则它自己的生造词会把自己洗白。

    python3 check_vocab.py hsk2-no-problem hsk3-be-careful
    python3 check_vocab.py            # 全站体检

注意: 池子只能证明"用过的一定安全",不能证明"没用过的就超纲" ——
池外词仍需人工对照官方 HSK 词表,脚本只负责把它们挑出来。
"""
import json, glob, sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))
MAX_OOV = 2          # 每篇允许的池外词上限
LEVELS = (1, 2, 3)   # 只有低级别才有"必须卡在词表内"的硬要求

def words_of(d):
    ws = [w[0] for s in d["sentences"] for w in s["t"] if len(w) == 3]
    return ws + [w[0] for w in d["vocab"]]

def main():
    targets = sys.argv[1:]
    texts = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "content/texts/*.json"))):
        texts[os.path.basename(p)[:-5]] = json.load(open(p, encoding="utf-8"))

    sel = [s for s in texts if not targets or any(t in s for t in targets)]
    bad = 0
    for slug in sorted(sel):
        d = texts[slug]
        lv = d["level"]
        if lv not in LEVELS:
            continue
        pool = set()
        for other, od in texts.items():
            if other == slug or od["level"] > lv:
                continue
            pool.update(words_of(od))
        voc = {w[0] for w in d["vocab"]}
        oov, seen = [], set()
        for s in d["sentences"]:
            for w in s["t"]:
                if len(w) == 3 and w[0] not in pool and w[0] not in seen:
                    seen.add(w[0]); oov.append(w[0])
        unlisted = [w for w in oov if w not in voc]
        ok = len(oov) <= MAX_OOV and not unlisted
        if not ok:
            bad += 1
        print("%s %-36s 池外 %d: %s%s" % ("✓" if ok else "✗", slug, len(oov),
              " ".join(oov) or "无",
              "   ⚠ 未进 vocab: " + " ".join(unlisted) if unlisted else ""))
    print("\n共 %d 篇,%d 篇超标(池外词 >%d,或池外词没进 vocab)。" % (len(sel), bad, MAX_OOV))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
