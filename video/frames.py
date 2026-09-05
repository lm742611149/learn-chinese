#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽帧工具 —— 给「首尾帧衔接」用。

镜头 N 的末帧当作镜头 N+1 的首帧，两段在切点上就是连续的，
这是消除 AI 视频「拼接感」最有效的一招。

    python3 video/frames.py in.mp4 --last            # 末帧 → in-last.png
    python3 video/frames.py in.mp4 --first           # 首帧
    python3 video/frames.py in.mp4 --at 3.5          # 指定秒
    python3 video/frames.py in.mp4 --last --delogo 566,1118,90,88   # 顺手抹水印
    python3 video/frames.py in.mp4 --grid 8          # 均匀抽 8 帧拼成一张，用来挑帧

抽出来的 PNG 直接喂 Flow 的 image-to-video / Frames to Video。
"""
import argparse
import os
import subprocess
import sys


def run(args):
    p = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args,
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg 失败:\n{p.stderr[-1500:]}")


def duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(p.stdout.strip())


def vf_chain(delogo):
    if not delogo:
        return []
    try:
        x, y, w, h = [int(v) for v in delogo.split(",")]
    except ValueError:
        sys.exit("--delogo 格式应为 x,y,w,h")
    return ["-vf", f"delogo=x={x}:y={y}:w={w}:h={h}"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--last", action="store_true", help="末帧（接下一镜头用）")
    g.add_argument("--first", action="store_true", help="首帧")
    g.add_argument("--at", type=float, metavar="SEC", help="指定秒数")
    g.add_argument("--grid", type=int, metavar="N", help="均匀抽 N 帧拼一张，用来挑帧")
    ap.add_argument("--delogo", metavar="x,y,w,h", help="抽帧同时抹掉水印区")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    if not os.path.exists(a.video):
        sys.exit(f"找不到 {a.video}")
    stem = os.path.splitext(a.video)[0]
    vf = vf_chain(a.delogo)

    if a.grid:
        out = a.out or f"{stem}-grid.png"
        dur = duration(a.video)
        n = a.grid
        cols = min(n, 4)
        rows = (n + cols - 1) // cols
        # 每 dur/n 秒取一帧，缩到 1/3 再平铺
        sel = f"select='not(mod(n\\,{max(1, int(dur * 24 / n))}))'"
        filt = f"{sel},scale=iw/3:ih/3,tile={cols}x{rows}"
        if a.delogo:
            filt = vf[1] + "," + filt
        run(["-i", a.video, "-vf", filt, "-frames:v", "1", "-fps_mode", "vfr", out])
        print(f"{out}  ({n} 帧，{dur:.1f}s 均匀取样)")
        return

    if a.last:
        out = a.out or f"{stem}-last.png"
        # -sseof 从文件末尾倒数，比算时间戳可靠
        run(["-sseof", "-0.25", "-i", a.video] + vf + ["-frames:v", "1", "-q:v", "1", out])
        label = "末帧"
    elif a.first:
        out = a.out or f"{stem}-first.png"
        run(["-i", a.video] + vf + ["-frames:v", "1", "-q:v", "1", out])
        label = "首帧"
    else:
        out = a.out or f"{stem}-{a.at:g}s.png"
        run(["-ss", str(a.at), "-i", a.video] + vf + ["-frames:v", "1", "-q:v", "1", out])
        label = f"{a.at:g}s"

    print(f"{out}  ({label}{'，已抹水印' if a.delogo else ''})")


if __name__ == "__main__":
    main()
