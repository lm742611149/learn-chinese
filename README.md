# Read Mandarin

Free graded Chinese reading practice for HSK 1–6, with pinyin, audio, tap-to-translate
and comprehension quizzes.

**→ [readmandarin.com](https://readmandarin.com)**

Every text is original. No textbook passages, no scraped content — each reading is
written to stay inside the vocabulary of its HSK level, so you can read without
hitting a wall every second sentence.

## What's in it

| | |
|---|---|
| **315 readings** | HSK 1–6, roughly 50 per level |
| **5,024 words** | every word that appears in a reading, [indexed by level](https://readmandarin.com/words) |
| **659 grammar patterns** | pulled from the readings, [indexed by level](https://readmandarin.com/grammar) |
| **1,834 characters** | with stroke-order animations |

## Features

- **Pinyin over every character**, toggleable — lean on it early, switch it off later
- **Tap any word** for its meaning, plus real example sentences from other readings
- **Audio on every sentence and every word**, with a 0.7× slow mode for shadowing
- **Stroke-order animations** for any character in the text
- **Three-question comprehension check** at the end of each reading
- **Grammar notes** explaining the patterns that reading introduces
- **Wordbook + flashcards** — star a word, review it later
- **Reading streak and progress tracking**
- Dark mode, offline support (PWA), works on phones

## Levels

[HSK 1](https://readmandarin.com/hsk1) ·
[HSK 2](https://readmandarin.com/hsk2) ·
[HSK 3](https://readmandarin.com/hsk3) ·
[HSK 4](https://readmandarin.com/hsk4) ·
[HSK 5](https://readmandarin.com/hsk5) ·
[HSK 6](https://readmandarin.com/hsk6)

## How it's built

A dependency-free static site generator in plain Python — no framework, no npm, no
build pipeline beyond one script.

```
content/texts/*.json   one reading per file
build.py               generates docs/ from content/
gen_audio.py           pre-renders sentence + word audio (edge-tts)
get_strokes.py         fetches stroke data for characters actually used
validate_texts.py      schema check: sentence counts, pinyin tones, quiz answers
```

Build it:

```bash
python3 build.py        # content/ -> docs/
```

That's the whole toolchain. `docs/` is served as a static site on Cloudflare Pages.

### Reading format

Each reading is a single JSON file. Tokens carry their own pinyin and gloss, which is
what makes per-word audio and tap-to-translate possible without a runtime dictionary:

```json
{
  "slug": "hsk1-my-day",
  "level": 1,
  "title_zh": "我的一天",
  "title_py": "Wǒ de yì tiān",
  "title_en": "My Day",
  "sentences": [
    { "t": [["我","wǒ","I"],["七点","qī diǎn","seven o'clock"],
            ["起床","qǐchuáng","to get up"],["。"]],
      "en": "I get up at seven o'clock." }
  ],
  "vocab": [["起床","qǐchuáng","to get up"]],
  "quiz":  [{"q":"What time does the narrator get up?","a":["Six","Seven","Eight"],"c":1}],
  "grammar":[{"p":"time before verb","e":"Chinese puts the time word before the verb.",
              "x":"我七点起床。 — I get up at seven."}]
}
```

## Who makes it

Written and maintained by Fei, a Mandarin teacher. The site is free and stays free —
if reading is the part you can do alone, speaking is the part that needs a person, and
that's what the lessons are for.

## License

Code is MIT. The readings themselves are original work — please don't republish them
as your own, but linking to them is always welcome.
