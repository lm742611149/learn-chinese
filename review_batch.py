#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新写课文的批量复核。schema 校验(validate_texts)和超纲检查(check_vocab)之外,
这里查的是**机器看不出、只有人读才发现**的那几类问题 —— 前几批实际踩过的:

  1. 套话收尾      第一批 9 篇里 8 篇以「很高兴」结尾、4 篇一字不差「我们都很高兴」
  2. quiz 写成中文  读者是英语母语初学者,读不懂中文题干(站内 80% 是英文)
  3. quiz 答案扎堆  三题答案都在同一个位置
  4. 结尾互相雷同   跨篇重复,单看一篇发现不了
  5. 疑似超纲高级词  词池会被旧课文的历史超纲洗白,这里额外点名常见的几个
  6. 格式不统一     t 数组被写成多行展开(站内惯例是单行紧凑)
  7. 句内副词重复   「我终于上车了,心里终于不那么紧张」

    python3 review_batch.py hsk2-i-miss-you hsk2-lets-go ...
"""
import json, glob, re, sys, os, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
CLICHE = ["我们都很高兴", "很高兴", "我很高兴"]
# 说教式收尾:agent 被禁掉「很高兴」之后换的另一种套话,HSK3+ 尤其爱写
PREACHY = ["我懂了", "我明白", "现在我知道", "从那以后", "这次以后",
           "以后我还会", "没有用", "才有用", "我学会了"]
# 第三代套话:禁掉前两种后,agent 改用「笑着说」制造温暖收尾。
# 单篇不算错,但一批里超过三分之一就是模板腔 —— 按整批比例报,不按单篇。
SMILEY = ["笑着说", "笑了，说", "笑着", "笑了"]
SUSPECT = ["项目", "付", "挑食", "消息", "紧张", "满意", "计划", "决定", "情况",
           "经验", "机会", "习惯", "方法", "环境", "支持", "参加", "重要"]

def text_of(d):
    return "".join("".join(t[0] for t in s["t"]) for s in d["sentences"])

def main():
    slugs = sys.argv[1:]
    if not slugs:
        print("用法: python3 review_batch.py <slug> [slug...]"); return 2
    docs = {}
    for s in slugs:
        p = os.path.join(ROOT, "content/texts/%s.json" % s)
        if not os.path.exists(p):
            print("✗ 找不到 %s" % s); return 2
        docs[s] = json.load(open(p, encoding="utf-8"))

    issues = 0
    print("── 1. 结尾句(查套话 / 查雷同)")
    ends = {}
    for s, d in docs.items():
        e = "".join(t[0] for t in d["sentences"][-1]["t"])
        ends[s] = e
        bad = [c for c in CLICHE if c in e] + [c for c in PREACHY if c in e]
        if bad: issues += 1
        print("  %s %-30s %s" % ("✗" if bad else " ", s, e))
    dup = [e for e, n in collections.Counter(ends.values()).items() if n > 1]
    if dup:
        issues += 1; print("  ✗ 结尾完全相同: %s" % dup)

    smiley = [s for s, e in ends.items() if any(c in e for c in SMILEY)]
    if len(docs) >= 5 and len(smiley) > len(docs) / 3:
        issues += 1
        print("  ✗ %d/%d 篇以「笑着说」类收尾 —— 又一种模板腔,改掉一半"
              % (len(smiley), len(docs)))
    elif smiley:
        print("  · 结尾带「笑」的 %d/%d 篇(过三分之一才算问题)" % (len(smiley), len(docs)))

    n_cliche = sum(1 for d in docs.values() if any(c in text_of(d) for c in CLICHE))
    print("  正文含「很高兴」类套话的: %d / %d" % (n_cliche, len(docs)))

    print("\n── 2. quiz 语言(题干主体必须是英文)")
    for s, d in docs.items():
        # 选项本身是中文短语是合理的(考"朋友喊的是哪句"),只看题干主体。
        # 题干里**引号内**的中文是被考的目标短语,也不算 —— 例如
        # `What does "这个用中文怎么说？" mean?` 框架是英文,不该报。
        QUOTE = "[\u201c\u201d\u0022\u2018\u2019\u0027]"
        stem = lambda q: re.sub(QUOTE + ".*?" + QUOTE, "", q)
        zh = [q["q"] for q in d["quiz"] if len(re.findall(r"[一-鿿]", stem(q["q"]))) > 6]
        if zh:
            issues += 1
            print("  ✗ %-30s %s" % (s, zh[0][:40]))
    print("  (题干里引用中文词是允许的,这里只抓整题中文)")

    print("\n── 3. quiz 答案分布")
    allc = []
    for s, d in docs.items():
        cs = [q["c"] for q in d["quiz"]]
        allc += cs
        if len(set(cs)) == 1:
            issues += 1; print("  ✗ %-30s 三题都在 %d" % (s, cs[0]))
    print("  全批分布: %s" % dict(sorted(collections.Counter(allc).items())))

    print("\n── 4. 疑似超纲高级词(词池挡不住的,逐个人工确认)")
    hit = False
    for w in SUSPECT:
        who = [s for s, d in docs.items() if w in text_of(d)]
        if who:
            hit = True; print("  ? %-4s → %s" % (w, " ".join(who)))
    if not hit: print("  无")

    print("\n── 5. 格式(t 数组必须单行)")
    for s in docs:
        raw = open(os.path.join(ROOT, "content/texts/%s.json" % s), encoding="utf-8").read()
        n = raw.count('"t": [[')
        if n != len(docs[s]["sentences"]):
            issues += 1; print("  ✗ %-30s 单行 %d / 共 %d 句" % (s, n, len(docs[s]["sentences"])))
    print("  (无输出即全部合规)")

    print("\n── 6. 对话密度(连着全是「X说:…」会读成练习册)")
    for slug, d in docs.items():
        sents = ["".join(t[0] for t in x["t"]) for x in d["sentences"]]
        # 只算"纯对话句":引号前只有「X说:」,没有动作或叙述。
        # 「服务员看了看,说:…」「我问朋友,朋友说:…」带了动作,不算。
        def pure(x):
            head = re.split(r"[“”]", x)[0]
            if not re.search(r"[说问答]：\s*$", head):
                return False
            return len(re.findall(r"[一-鿿]", head)) <= 4
        talky = [pure(x) for x in sents]
        run = mx = 0
        for x in talky:
            run = run + 1 if x else 0
            mx = max(mx, run)
        if mx >= 4:
            print("  ? %-30s 连续 %d 句是光秃秃的「X说:…」,考虑加个动作或叙述"
                  % (slug, mx))
    print("  (只提示不计错 —— 对话密集不一定是毛病,自己看一眼)")

    print("\n── 7. 同一句里副词重复")
    for s, d in docs.items():
        for i, sent in enumerate(d["sentences"], 1):
            ws = [t[0] for t in sent["t"] if len(t) == 3]
            for w, n in collections.Counter(ws).items():
                if n > 1 and w in ("终于", "马上", "已经", "还", "又", "才", "就", "真", "非常", "特别"):
                    issues += 1
                    print("  ✗ %s 第%d句「%s」出现 %d 次" % (s, i, w, n))
    print("\n%s 共 %d 处待处理。" % ("⚠" if issues else "✓", issues))
    return 1 if issues else 0

if __name__ == "__main__":
    sys.exit(main())
