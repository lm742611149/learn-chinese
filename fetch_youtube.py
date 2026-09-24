#!/usr/bin/env python3
"""Pull the channel's public RSS feed into content/videos.json.

No API key: YouTube publishes the latest 15 uploads of any channel at
  https://www.youtube.com/feeds/videos.xml?channel_id=<id>
with title, publish date, description and view count. Older videos fall off the
feed, so this merges into the existing file instead of overwriting it — once a
video has been seen it stays, and its title/views/description are refreshed
whenever it is still in the feed.

  python3 fetch_youtube.py          # update content/videos.json, then run build.py
  python3 fetch_youtube.py --dry    # print what would change, write nothing

"kind" is "short" or "video". The feed carries no duration, so a Short is
recognised by how the channel writes them: hashtag-only titles and no
description. Fix by hand in the JSON if one is misfiled; hand edits to "kind"
are kept across refreshes.
"""
import json, os, re, ssl, sys, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "content", "videos.json")
NS = {"a": "http://www.w3.org/2005/Atom",
      "yt": "http://www.youtube.com/xml/schemas/2015",
      "m": "http://search.yahoo.com/mrss/"}

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()


def guess_kind(title, desc):
    if not desc.strip() or "#" in title:
        return "short"
    return "video"


def fetch(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        root = ET.fromstring(r.read())
    out = []
    for e in root.findall("a:entry", NS):
        g = e.find("m:group", NS)
        desc = (g.findtext("m:description", default="", namespaces=NS) or "") if g is not None else ""
        stats = g.find("m:community/m:statistics", NS) if g is not None else None
        title = e.findtext("a:title", default="", namespaces=NS).strip()
        out.append({
            "id": e.findtext("yt:videoId", namespaces=NS),
            "title": title,
            "published": e.findtext("a:published", namespaces=NS)[:10],
            "views": int(stats.get("views", 0)) if stats is not None else 0,
            "description": re.sub(r"\s+", " ", desc).strip()[:300],
            "kind": guess_kind(title, desc),
        })
    return out


def main():
    dry = "--dry" in sys.argv
    cid = SITE.get("youtube_channel_id")
    if not cid:
        sys.exit("site.json needs youtube_channel_id")
    fresh = fetch(cid)
    old = {}
    if os.path.exists(OUT):
        old = {v["id"]: v for v in json.load(open(OUT, encoding="utf-8"))}
    merged = dict(old)
    added = updated = 0
    for v in fresh:
        if v["id"] in old:
            keep = old[v["id"]]
            v["kind"] = keep.get("kind", v["kind"])      # hand-fixed kind wins
            if keep != v:
                updated += 1
        else:
            added += 1
        merged[v["id"]] = v
    vids = sorted(merged.values(), key=lambda v: (v["published"], v["id"]), reverse=True)
    print(f"feed {len(fresh)} · known {len(old)} · added {added} · refreshed {updated} · total {len(vids)}")
    for v in vids[:len(fresh)]:
        print(f"  {v['published']}  {v['kind']:5s}  {v['views']:>6}  {v['title'][:70]}")
    if dry:
        return
    json.dump(vids, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
