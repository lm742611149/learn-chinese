#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把站点 URL 推给 IndexNow(Bing / Yandex 等共享这一个端点)。

爬虫自己发现新页可能要几周 —— 2026-09-06 时 Bing 只知道 121 个 URL,而站上有 437 个,
最后一次抓取停在 9/2。IndexNow 是主动推送,提交后通常几天内就会来抓。

    python3 indexnow.py            # 推送 sitemap 里的全部 URL
    python3 indexnow.py --since 2  # 只推送最近 2 天改过的课文(增量,日常用这个)
    python3 indexnow.py --dry      # 只打印不发送

密钥在 .indexnow-key,对应的凭证文件 <key>.txt 在仓库根,build.py 会拷进 docs/ 根,
Bing 会去 https://readmandarin.com/<key>.txt 校验所有权。
"""
import json, os, ssl, sys, time, urllib.request, re

try:                      # 本机 Python 缺根证书,与 get_strokes.py 同款处理
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl._create_unverified_context()

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST = "readmandarin.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000   # 协议单次上限

def urls_from_sitemap():
    p = os.path.join(ROOT, "docs", "sitemap.xml")
    return re.findall(r"<loc>([^<]+)</loc>", open(p, encoding="utf-8").read())

def recent_urls(days):
    """最近 N 天改过的课文,按源 JSON 的 mtime 算。"""
    cut = time.time() - days * 86400
    out = []
    d = os.path.join(ROOT, "content", "texts")
    for f in os.listdir(d):
        if f.endswith(".json") and os.path.getmtime(os.path.join(d, f)) > cut:
            out.append("https://%s/texts/%s" % (HOST, f[:-5]))
    return out

def push(urls, key, dry=False):
    for i in range(0, len(urls), BATCH):
        chunk = urls[i:i + BATCH]
        body = json.dumps({
            "host": HOST,
            "key": key,
            "keyLocation": "https://%s/%s.txt" % (HOST, key),
            "urlList": chunk,
        }).encode()
        if dry:
            print("[dry] 会推送 %d 条,前 3 条: %s" % (len(chunk), chunk[:3]))
            continue
        req = urllib.request.Request(ENDPOINT, data=body,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
                # 200/202 都算成功;202 = 已收下,待校验 key
                print("推送 %d 条 -> HTTP %d %s" % (len(chunk), r.status, r.reason))
        except urllib.error.HTTPError as e:
            print("推送 %d 条 -> HTTP %d %s" % (len(chunk), e.code, e.reason))
            print("  返回:", e.read()[:300].decode(errors="ignore"))
            return 1
    return 0

def main():
    key_path = os.path.join(ROOT, ".indexnow-key")
    if not os.path.exists(key_path):
        print("✗ 找不到 .indexnow-key"); return 2
    key = open(key_path).read().strip()

    args = sys.argv[1:]
    dry = "--dry" in args
    if "--since" in args:
        days = float(args[args.index("--since") + 1])
        urls = recent_urls(days)
        print("最近 %g 天改动的课文: %d 条" % (days, len(urls)))
    else:
        urls = urls_from_sitemap()
        print("sitemap 全量: %d 条" % len(urls))
    if not urls:
        print("没有要推送的 URL"); return 0
    return push(urls, key, dry)

if __name__ == "__main__":
    sys.exit(main())
