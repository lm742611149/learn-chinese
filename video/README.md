# 课文 → 竖版视频流水线

把 `content/texts/<slug>.json` 的课文，拼成 9:16 教学短视频（Reels / Shorts / 抖音）。

```bash
python3 video/build_video.py hsk1-buying-fruit
# → video/hsk1-buying-fruit/hsk1-buying-fruit.mp4
```

## 设计前提

**程序化的部分是资产，AI 生成的素材是耗材。** 字幕排版、拼音对齐、片头片尾、
响度归一这些每条视频都要做的事全部代码化；镜头素材可以随时换成新模型的产物，
改 `shots.json` 的 `src` 重跑即可，不影响其它环节。

所以第一版刻意不依赖视频生成模型也能出片 —— 缺素材的镜头用 `kenburns`
（静态图慢推）兜底，成片始终是完整的。

## 文件

| 文件 | 作用 |
|---|---|
| `vlib.py` | 画面渲染层（Pillow）：字幕条、底部渐变、片头卡、生词卡 |
| `build_video.py` | 拼装层（ffmpeg）：逐镜头产片段 → concat 成片 |
| `frames.py` | 抽帧工具：`--last` 取末帧接下一镜头（首尾帧衔接）、`--grid` 挑帧 |
| `<slug>/shots.json` | 该课文的分镜表 |
| `<slug>/storyboard.md` | 人写的分镜脚本 + 生成提示词（喂给可灵/即梦/Veo） |
| `<slug>/shoot-list.md` | 素材生成执行单：平台设置、参考图、逐镜头提示词、额度预算 |
| `<slug>/_build/` | 中间片段，可随时删 |

## shots.json

```jsonc
{
  "delogo": { "x": 566, "y": 1118, "w": 90, "h": 88 },  // 可选：抹掉素材右下角水印
  "shots": [
    { "id": "title", "kind": "title", "dur": 3.0 },

    // 已有视频素材
    { "id": "s1", "kind": "clip", "src": "clips/shot1_raw.mp4",
      "ss": 0.5,            // 从素材第几秒开始取
      "dur": 5.0,
      "audio": "audio/s1.mp3",       // 画外音；不写则用 keep_audio 或静音
      "keep_audio": false,           // true = 用素材自带音轨（对口型镜头必须）
      "subs": [{ "sent": 0 }] },     // 字幕取 sentences[0]

    // 素材缺位时的兜底：静态图慢推
    { "id": "s5", "kind": "kenburns", "src": "still-shopkeeper.png", "dur": 4.0,
      "audio": "audio/s5.mp3", "subs": [{ "sent": 4 }],
      "placeholder": true },         // 只影响构建日志里的提醒

    { "id": "vocab", "kind": "vocab" }   // 自动展开成逐词高亮，配 media/audio/w/ 的单词 TTS
  ]
}
```

一个镜头内多条字幕（一段素材装了两句对白）：

```jsonc
"subs": [
  { "sent": 2, "start": 0.0, "end": 4.0,  "quote": true, "speaker": "girl" },
  { "sent": 3, "start": 4.2, "end": 10.0, "quote": true, "speaker": "man"  }
]
```

- `quote: true` — 课文里的「我说：“…”」只取引号内容。配音为了对口型通常只念
  引号内，字幕不裁就会音画不同步。
- `speaker` — 汉字行换色区分说话人（`girl` 白 / `man` 浅蓝）。

## 两个容易踩的坑

**拼音是逐词对齐的**，不是整句糊一行 —— 靠 `sentences[].t` 里每个 token 的
`[汉字, 拼音, 释义]` 结构。所以课文 JSON 的分词质量直接决定字幕好不好看。

**中文全角标点**（，。？）的 advance 宽度是一个全角，但字形只占左下角。按 advance
排版会在标点后撑出一个洞，必须单独收窄（见 `vlib.NARROW`）。

## 环境

- `ffmpeg` — 本机这份是精简构建，**没有 libass/libfreetype**，所以字幕不走
  `subtitles`/`drawtext` 滤镜，改由 Pillow 渲染 PNG 再 overlay。
- 编码用 `h264_videotoolbox`（Intel Mac 的 Quick Sync 硬件编码）。45 秒成片
  约 13 秒渲完；换成 CPU 软编会慢一个数量级。
- 配音：`edge_tts`（免费，见根目录 `gen_audio.py`）。

## 关于素材水印

`delogo` 用来抹掉生成模型打在右下角的可见标识。注意这只去掉可见部分，
Veo/Imagen 一类仍会嵌 SynthID 隐形水印，且各家服务条款对去标识的规定不同 ——
要正式发布，更稳妥的做法是用付费层直接输出无水印素材。
