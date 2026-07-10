#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download stroke-order data (hanzi-writer-data) for every character used
in the readings.

    python3 get_strokes.py

Output: media/strokes/<char>.json (incremental; build.py copies to docs/strokes/).
"""
import concurrent.futures
import json
import os
import ssl
import sys
import urllib.request

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:   # 本机 Python 缺根证书(见 pip 同款问题)
    SSL_CTX = ssl._create_unverified_context()

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "media", "strokes")
CDN = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{}.json"


def collect_chars():
    chars = set()
    tdir = os.path.join(ROOT, "content", "texts")
    for f in sorted(os.listdir(tdir)):
        if not f.endswith(".json"):
            continue
        t = json.load(open(os.path.join(tdir, f), encoding="utf-8"))
        for s in t["sentences"]:
            for tok in s["t"]:
                if len(tok) == 3:
                    chars.update(tok[0])
        for v in t["vocab"]:
            chars.update(v[0])
        chars.update(t["title_zh"])
    return sorted(c for c in chars if "一" <= c <= "鿿")


def fetch(c):
    path = os.path.join(OUT, c + ".json")
    if os.path.exists(path) and os.path.getsize(path) > 100:
        return 0
    try:
        from urllib.parse import quote
        with urllib.request.urlopen(CDN.format(quote(c)), timeout=30, context=SSL_CTX) as r:
            data = r.read()
        if len(data) > 100:
            open(path, "wb").write(data)
            return 1
    except Exception as e:
        print("FAILED:", c, e, file=sys.stderr)
    return 0


def main():
    os.makedirs(OUT, exist_ok=True)
    chars = collect_chars()
    print(f"{len(chars)} unique characters")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        done = sum(ex.map(fetch, chars))
    print(f"newly downloaded: {done}")


if __name__ == "__main__":
    main()
