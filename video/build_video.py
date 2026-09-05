#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把课文 + 素材拼装成 9:16 竖版教学视频。

    python3 video/build_video.py hsk1-buying-fruit [-o out.mp4]

读 video/<slug>/shots.json 的分镜表，逐镜头产出统一规格的中间片段
(720x1280 / 24fps / aac 48k stereo)，最后 concat 成片。

镜头类型:
  title     程序化片头卡
  clip      已有视频素材（AI 生成或实拍），裁到指定时长
  kenburns  静态图慢推，用于素材缺位时兜底
  vocab     片尾生词卡，逐词高亮 + 站里现成的单词 TTS

素材可随时替换：把新 mp4 丢进 clips/ 并改 shots.json 的 src 即可重跑。
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24
W, H = vlib.W, vlib.H
VCODEC = ["-c:v", "h264_videotoolbox", "-b:v", "10M", "-pix_fmt", "yuv420p", "-r", str(FPS)]
ACODEC = ["-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k"]
LEAD = 0.25          # 旁白入点延迟，避免一切镜就说话
TAIL = 0.55          # 生词卡每词后的停顿

SCALE = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
         f"crop={W}:{H},fps={FPS},setsar=1")

SHOT_DIR = None      # 由 build() 设为 video/<slug>/
CFG = {}             # shots.json 顶层配置


def run(args, desc=""):
    p = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args,
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg 失败 [{desc}]\n{' '.join(args)}\n{p.stderr[-2500:]}")


def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def audio_chain(label, dur, delay=LEAD):
    """把任意音源规整成恰好 dur 秒的 48k 立体声。"""
    return (f"{label}aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"adelay={int(delay * 1000)}|{int(delay * 1000)},apad,atrim=0:{dur:.3f}[a]")


def overlay_chain(layers, dur):
    """base [v0] 之上依次叠各图层，layers 为 [(png, start, end), ...]。"""
    parts, cur = [], "[v0]"
    for i, (_, st, en) in enumerate(layers):
        nxt = "[v]" if i == len(layers) - 1 else f"[vo{i}]"
        parts.append(f"{cur}[{i + 1}:v]overlay=0:0:enable='between(t,{st:.3f},{en:.3f})'{nxt}")
        cur = nxt
    return parts


def make_layers(shot, text, tmp, sid, dur):
    """底部渐变（全程）+ 各条字幕（各自时间窗），返回 [(png, start, end), ...]。"""
    scrim = os.path.join(tmp, "scrim.png")
    if not os.path.exists(scrim):
        vlib.render_scrim().save(scrim)
    layers = [(scrim, 0.0, dur)]
    for i, sp in enumerate(shot.get("subs", [])):
        sent = text["sentences"][sp["sent"]]
        if sp.get("quote"):
            sent = vlib.quote_only(sent)
        path = os.path.join(tmp, f"{sid}_sub{i}.png")
        vlib.render_subtitle(sent, speaker=sp.get("speaker", "girl")).save(path)
        layers.append((path, sp.get("start", 0.0), sp.get("end", dur)))
    return layers


def seg_clip(shot, text, tmp, sid, out):
    src = os.path.join(SHOT_DIR, shot["src"])
    dur = shot["dur"]
    layers = make_layers(shot, text, tmp, sid, dur)

    args = ["-ss", str(shot.get("ss", 0)), "-t", f"{dur:.3f}", "-i", src]
    for p, _, _ in layers:
        args += ["-i", p]

    base = SCALE
    dl = shot.get("delogo", CFG.get("delogo"))
    if dl:  # shots.json 的坐标按 720x1280 设计稿写，跟着输出分辨率缩放
        base += (f",delogo=x={vlib.px(dl['x'])}:y={vlib.px(dl['y'])}"
                 f":w={vlib.px(dl['w'])}:h={vlib.px(dl['h'])}")
    fc = [f"[0:v]{base}[v0]"] + overlay_chain(layers, dur)

    if shot.get("keep_audio"):
        fc.append(audio_chain("[0:a]", dur, delay=0))
    elif shot.get("audio"):
        args += ["-i", os.path.join(SHOT_DIR, shot["audio"])]
        fc.append(audio_chain(f"[{len(layers) + 1}:a]", dur))
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        fc.append(audio_chain(f"[{len(layers) + 1}:a]", dur, delay=0))

    run(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-t", f"{dur:.3f}"] + VCODEC + ACODEC + [out], sid)


def seg_kenburns(shot, text, tmp, sid, out):
    src = os.path.join(SHOT_DIR, shot["src"])
    dur = shot["dur"]
    layers = make_layers(shot, text, tmp, sid, dur)

    args = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", src]
    for p, _, _ in layers:
        args += ["-i", p]

    # 先放大到 2x 再 zoompan，缓解 zoompan 的整数抖动
    kb = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
          f"zoompan=z='min(1+0.0011*on,1.13)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={W}x{H}:fps={FPS},setsar=1")
    fc = [f"[0:v]{kb}[v0]"] + overlay_chain(layers, dur)

    if shot.get("audio"):
        args += ["-i", os.path.join(SHOT_DIR, shot["audio"])]
        fc.append(audio_chain(f"[{len(layers) + 1}:a]", dur))
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        fc.append(audio_chain(f"[{len(layers) + 1}:a]", dur, delay=0))

    run(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-t", f"{dur:.3f}"] + VCODEC + ACODEC + [out], sid)


def seg_card(img_path, dur, out, sid, audio=None, fade=True):
    args = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", img_path]
    if audio:
        args += ["-i", audio]
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    vf = f"{SCALE}"
    if fade:
        vf += f",fade=t=in:st=0:d=0.35,fade=t=out:st={max(dur - 0.35, 0):.3f}:d=0.35"
    fc = [f"[0:v]{vf}[v]", audio_chain("[1:a]", dur, delay=0.15 if audio else 0)]
    run(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-t", f"{dur:.3f}"] + VCODEC + ACODEC + [out], sid)


def build(slug, out_path):
    global SHOT_DIR, CFG
    SHOT_DIR = os.path.join(ROOT, "video", slug)
    text = json.load(open(os.path.join(ROOT, "content", "texts", f"{slug}.json"), encoding="utf-8"))
    cfg = CFG = json.load(open(os.path.join(SHOT_DIR, "shots.json"), encoding="utf-8"))
    tmp = os.path.join(SHOT_DIR, "_build")
    os.makedirs(tmp, exist_ok=True)

    segs, notes = [], []
    for shot in cfg["shots"]:
        sid = shot["id"]
        kind = shot["kind"]

        if kind == "vocab":
            # 每个生词一段，配站里现成的单词 TTS，逐词高亮
            for i, v in enumerate(text["vocab"][:7]):
                wav = os.path.join(ROOT, "media", "audio", "w", f"{v[0]}.mp3")
                has = os.path.exists(wav)
                d = max(probe(wav) + TAIL, 1.1) if has else 1.1
                png = os.path.join(tmp, f"vocab{i}.png")
                vlib.render_vocab_card(text, highlight=i).save(png)
                seg = os.path.join(tmp, f"seg_vocab{i}.mp4")
                seg_card(png, d, seg, f"vocab{i}", audio=wav if has else None,
                         fade=(i == 0 or i == len(text["vocab"][:7]) - 1))
                segs.append(seg)
            continue

        seg = os.path.join(tmp, f"seg_{sid}.mp4")
        if kind == "title":
            png = os.path.join(tmp, "title.png")
            vlib.render_title_card(text).save(png)
            seg_card(png, shot["dur"], seg, sid)
        elif kind == "clip":
            src = os.path.join(SHOT_DIR, shot["src"])
            if not os.path.exists(src):
                sys.exit(f"素材缺失: {src}")
            avail = probe(src) - shot.get("ss", 0)
            if avail + 0.05 < shot["dur"]:
                notes.append(f"{sid}: 素材只剩 {avail:.1f}s，短于计划 {shot['dur']}s")
            seg_clip(shot, text, tmp, sid, seg)
        elif kind == "kenburns":
            seg_kenburns(shot, text, tmp, sid, seg)
        else:
            sys.exit(f"未知镜头类型: {kind}")

        if shot.get("placeholder"):
            notes.append(f"{sid}: 占位镜头（{shot['src']} 慢推），待补真素材")
        segs.append(seg)
        print(f"  ✓ {sid:6s} {probe(seg):5.2f}s")

    lst = os.path.join(tmp, "concat.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    # 视频直接 copy（各段编码参数一致）；音频重编一次做响度归一，
    # -16 LUFS 是 YouTube/TikTok 一档的通行值，否则成片在手机上明显偏轻
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11"] + ACODEC + [out_path], "concat")

    print(f"\n成片: {out_path}  ({probe(out_path):.2f}s)")
    for n in notes:
        print(f"  ! {n}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    build(a.slug, a.out or os.path.join(ROOT, "video", a.slug, f"{a.slug}.mp4"))
