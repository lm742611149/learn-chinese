#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-generate MP3 audio for every sentence and word via Microsoft neural TTS.

    python3 gen_audio.py [voice]        # default zh-CN-XiaoxiaoNeural

Output goes to media/audio/ (build.py copies it into docs/audio/):
    media/audio/<slug>/<sentence-index>.mp3
    media/audio/w/<word>.mp3
Incremental: existing non-empty files are skipped, so re-running only fills
in new readings/words. Requires: pip install edge-tts (network to Microsoft).
"""
import asyncio
import json
import os
import sys

import edge_tts

VOICE = sys.argv[1] if len(sys.argv) > 1 else "zh-CN-XiaoxiaoNeural"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "media", "audio")

sem = asyncio.Semaphore(8)


async def gen(text, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return 0
    async with sem:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, VOICE).save(path)
                return 1
            except Exception:
                try:
                    os.remove(path)
                except OSError:
                    pass
                await asyncio.sleep(2 * (attempt + 1))
    print("FAILED:", path, text[:24], file=sys.stderr)
    return 0


def collect_jobs():
    jobs, words = [], set()
    tdir = os.path.join(ROOT, "content", "texts")
    for f in sorted(os.listdir(tdir)):
        if not f.endswith(".json"):
            continue
        t = json.load(open(os.path.join(tdir, f), encoding="utf-8"))
        d = os.path.join(OUT, t["slug"])
        os.makedirs(d, exist_ok=True)
        for i, s in enumerate(t["sentences"]):
            text = "".join(tok[0] for tok in s["t"])
            jobs.append((text, os.path.join(d, f"{i}.mp3")))
        for s in t["sentences"]:
            for tok in s["t"]:
                if len(tok) == 3:
                    words.add(tok[0])
        for v in t["vocab"]:
            words.add(v[0])
    wd = os.path.join(OUT, "w")
    os.makedirs(wd, exist_ok=True)
    for w in sorted(words):
        jobs.append((w, os.path.join(wd, w + ".mp3")))
    return jobs


async def main():
    jobs = collect_jobs()
    print(f"{len(jobs)} clips total, voice={VOICE}")
    done = await asyncio.gather(*[gen(t, p) for t, p in jobs])
    print(f"newly generated: {sum(done)} / {len(jobs)}")


if __name__ == "__main__":
    asyncio.run(main())
