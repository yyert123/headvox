<div align="center">

# HeadVox

**Script → voiceover + word‑aligned SRT/VTT captions, in one command.**
Open‑source Python CLI & library for talking‑head videos, explainers and Shorts. Chinese · English · Japanese.

[![PyPI](https://img.shields.io/pypi/v/headvox.svg)](https://pypi.org/project/headvox/)
[![Python](https://img.shields.io/pypi/pyversions/headvox.svg)](https://pypi.org/project/headvox/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yyert123/headvox/blob/main/LICENSE)
[![Live samples](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-live%20samples-yellow)](https://huggingface.co/spaces/headvox/headvox)

**English** · [简体中文](https://github.com/yyert123/headvox/blob/main/README.zh-CN.md) · [日本語](https://github.com/yyert123/headvox/blob/main/README.ja.md)

</div>

---

**HeadVox** is a free, MIT‑licensed command‑line tool and Python library that turns a plain‑text or Markdown script into a natural‑sounding neural text‑to‑speech voiceover, and writes **SRT and WebVTT captions timed to the actual spoken words** plus a **JSON manifest with per‑word timestamps**. It can then put the voiceover and captions onto a video clip with ffmpeg — looping the clip to length and ducking background music under the voice. It is built for people who make talking‑head videos, explainers, course lessons, product demos and YouTube Shorts / TikTok / Bilibili / Douyin clips, and who are tired of hand‑timing subtitles.

```bash
pip install "headvox[edge]"
headvox script.md -o out/ --voice en-female --video avatar.mp4
# out/voiceover.mp3  voiceover.srt  voiceover.vtt  voiceover.json  voiceover.mp4
```

▶ **Hear real, unedited output** (Chinese and English, captions scrolling from the generated VTT): <https://huggingface.co/spaces/headvox/headvox>

## Contents

- [Why HeadVox](#why-headvox) · [Features](#features) · [How it compares](#how-it-compares)
- [Install](#install) · [Quick start](#quick-start) · [Writing a script](#writing-a-script-that-sounds-good)
- [Recipes](#recipes) · [Python API](#python-api) · [Timing manifest](#timing-manifest)
- [Voices](#voices) · [Troubleshooting](#troubleshooting) · [FAQ](#faq) · [How it works](#how-it-works)

## Why HeadVox

A short narrated video normally takes three separate, fiddly jobs: generate the audio, time the subtitles by hand, and mux both onto the picture. Change one sentence and you redo all three. Generic TTS tools give you an MP3 and, at best, one caption per sentence — fine for an audiobook, too long and too late for a vertical video, and awkward for Chinese or Japanese where lines must break by width, not by spaces.

HeadVox treats **audio, captions and timing as one artifact**, generated from one script, so they cannot drift apart.

## Features

| | |
|---|---|
| 🎯 **Word‑aligned captions** | Cues come from the TTS engine's real word‑boundary timestamps, not from estimating by character count — so the 40th caption is as tight as the first. |
| 🀄 **CJK‑aware line breaking** | Chinese/Japanese characters count as two columns; lines break at punctuation inside a width budget (`--caption-chars`), so mixed 中文 + English never runs off a 9:16 screen. |
| ⏸️ **Pacing you control** | Automatic sentence (250 ms) and paragraph (700 ms) pauses, plus `[pause]`, `[pause 1.5s]`, `[pause 400ms]` anywhere in the script. |
| 📝 **Markdown‑aware** | Headings, emphasis, links, code fences and list markers are reduced to the words a narrator would actually say. |
| 🧭 **Per‑word JSON manifest** | Start/end milliseconds for every segment and word — ready for lip‑sync / avatar tools, kinetic typography, or your own caption styling. |
| 🎬 **One‑step video** | Loop a talking‑head clip to the voiceover length, duck a music bed with sidechain compression, attach soft subtitles or burn them in. |
| ⚡ **Clip cache** | Every segment is cached by text + voice settings; re‑rendering after a one‑word edit only re‑synthesizes that sentence. |
| 🧩 **Pluggable backends** | `edge` (free online neural voices, no API key) and `sine` (offline, for tests and dry runs). Add your own engine in ~10 lines. |
| 🪶 **Tiny footprint** | Pure Python, zero required dependencies; needs `ffmpeg`. No model weights are bundled or downloaded. |

## How it compares

Honest positioning — pick the tool that fits the job:

| You want… | Good fit |
|---|---|
| One‑liner TTS of a short string to MP3 | the `edge-tts` CLI itself |
| A full "topic → AI script → stock footage → video" generator | an end‑to‑end short‑video pipeline |
| Subtitles for a video that **already has speech** | a Whisper‑based transcription tool |
| **Your own script** → voiceover + captions that match it word‑for‑word, CJK‑friendly, with pause control, a reusable timing file, and optional mux onto your own clip | **HeadVox** |

HeadVox is deliberately the focused, composable piece: it does one job well and hands clean files (MP3/SRT/VTT/JSON/MP4) to whatever editor or pipeline you already use.

## Install

```bash
pip install "headvox[edge]"   # with free online neural voices (recommended)
pip install headvox           # library + offline 'sine' backend only
```

Requirements: Python 3.9+, and **ffmpeg** with `ffprobe` on your PATH (<https://ffmpeg.org/download.html>; macOS `brew install ffmpeg`, Ubuntu `sudo apt install ffmpeg`, Windows `winget install ffmpeg`).

## Quick start

```bash
headvox talk.md -o out/                                  # script in, files out
headvox talk.md -o out/ --voice zh-male --rate +8        # different voice, a bit faster
headvox talk.md --dry-run                                # preview segmentation, no TTS call
echo "Hello from HeadVox." | headvox - -o out/ --voice en-female
```

Main options (`headvox --help` for all):

| Option | Default | What it does |
|---|---|---|
| `-v, --voice` | `zh-female` | preset (`zh-female`, `zh-male`, `en-female`, `en-male`, `ja-female`, `ja-male`) or any edge‑tts voice id |
| `--rate` / `--pitch` / `--volume` | `0` | speed %, pitch Hz, volume % (e.g. `+8`, `-5`) |
| `--format` | `mp3` | `mp3`, `wav`, `m4a` |
| `--sentence-pause` / `--paragraph-pause` | `250` / `700` | silence in ms |
| `--caption-chars` | `42` | caption width budget (CJK char = 2) |
| `--video` | – | clip to put the voiceover on |
| `--fit` | `loop` | `loop` the clip to the audio length, or cut to `audio` |
| `--music` / `--music-volume` | – / `0.12` | background bed, looped and ducked |
| `--burn-subs` / `--no-subs` | off | burn captions into the picture / attach none |
| `--proxy` | – | HTTP proxy for the online backend (or `HEADVOX_PROXY`) |

## Writing a script that sounds good

- **One idea per sentence.** Shorter sentences give shorter, punchier captions and more natural breathing.
- **Use blank lines between paragraphs** — they become longer pauses (`--paragraph-pause`).
- **Add beats deliberately:** `That's it. [pause 0.8s] Now the fun part.`
- **Spell out what should be said:** write "two thousand twenty‑six" or "v zero point one" if the engine mispronounces a token.
- **Markdown is fine** — `# Headings` are spoken as plain sentences, `**bold**` loses its asterisks, code fences are skipped.
- For vertical video (9:16) try `--caption-chars 28`; for 16:9 the default 42 works well.

## Recipes

**YouTube Shorts / TikTok / Douyin (9:16, burned‑in captions)**
```bash
headvox short.md -o out/ --voice en-male --rate +6 --caption-chars 28 \
        --video portrait_avatar.mp4 --burn-subs --music bed.mp3
```

**Course lesson with toggleable subtitles (16:9)**
```bash
headvox lesson-03.md -o lesson-03/ --voice zh-female --video slides.mp4 --fit audio
```

**Bilingual versions from two scripts**
```bash
headvox intro.zh.md -o out/zh --voice zh-female
headvox intro.en.md -o out/en --voice en-female
```

**Import into an editor** — drop `voiceover.mp3` + `voiceover.srt` into Premiere Pro, DaVinci Resolve, Final Cut (via SRT import) or CapCut/剪映; the captions land on the right frames.

**Batch a folder**
```bash
for f in scripts/*.md; do headvox "$f" -o "out/$(basename "$f" .md)"; done
```
Unchanged sentences come from the cache, so re‑runs are fast.

## Python API

```python
from headvox import synthesize, Script, VoiceSettings

res = synthesize(
    Script.from_file("talk.md"),
    "out/",
    backend="edge",
    settings=VoiceSettings(voice="zh-CN-XiaoxiaoNeural", rate_pct=5),
)
print(res.duration_ms, "ms,", len(res.cues), "captions")
for cue in res.cues:
    print(cue.start_ms, cue.end_ms, cue.text)
```

`synthesize()` returns the paths of the audio, SRT, VTT and manifest, the total duration, the caption cues and per‑segment word timings.

### Custom backend

```python
from headvox.backends import SegmentAudio, WordMark, register_backend

class MyBackend:
    name = "mine"
    def synthesize_segment(self, text, settings):
        audio, fmt, dur = my_tts(text, settings.voice)   # bytes, "wav"/"mp3", ms
        return SegmentAudio(audio, fmt, dur, [WordMark("hi", 0, 200)])

register_backend("mine", lambda **kw: MyBackend())
```
Then `headvox script.md -b mine`. Any engine that can report word timings (or that you align afterwards) gets HeadVox's captioning, pacing, caching and muxing for free.

## Timing manifest

`voiceover.json` holds everything downstream tools need:

```json
{
  "tool": "headvox",
  "backend": "edge",
  "duration_ms": 19600,
  "segments": [
    {"index": 0, "text": "Hi everyone, and welcome back.",
     "start_ms": 250, "end_ms": 2232,
     "words": [{"text": "Hi", "start_ms": 250, "end_ms": 412}]}
  ],
  "cues": [{"index": 1, "start_ms": 250, "end_ms": 2232, "text": "Hi everyone, and welcome back."}]
}
```

Use it to drive mouth shapes on an avatar, highlight the active word (karaoke‑style captions), cut B‑roll on sentence boundaries, or generate chapter markers.

## Voices

| Preset | edge‑tts voice |
|---|---|
| `zh-female` | `zh-CN-XiaoxiaoNeural` |
| `zh-male` | `zh-CN-YunxiNeural` |
| `en-female` | `en-US-AvaMultilingualNeural` |
| `en-male` | `en-US-AndrewMultilingualNeural` |
| `ja-female` | `ja-JP-NanamiNeural` |
| `ja-male` | `ja-JP-KeitaNeural` |

Any other edge‑tts voice id works too (`edge-tts --list-voices`), which opens up many more languages and accents; caption line‑breaking is tuned for CJK and Latin scripts.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ffmpeg not found` | install ffmpeg and make sure `ffmpeg` and `ffprobe` are on PATH |
| `NoAudioReceived` from edge | the voice id is wrong or temporarily unavailable — try another voice, or retry |
| Network blocked / corporate proxy | `--proxy http://host:port` or `export HEADVOX_PROXY=...` |
| `--burn-subs` fails | your ffmpeg lacks libass; use soft subtitles (default) or install a full ffmpeg build |
| Captions too long on vertical video | lower `--caption-chars` (e.g. 24–28) |

## FAQ

**Is HeadVox free?** Yes. HeadVox is MIT‑licensed. The default `edge` backend uses the free online service behind Microsoft Edge's read‑aloud via the `edge-tts` package; it needs internet but no API key or account.

**Does it work offline?** Parsing, stitching, captioning and video muxing are fully local. Speech synthesis with `edge` needs internet; plug in a local engine through the backend API for a fully offline setup.

**Why are the captions more accurate than splitting by sentence?** HeadVox uses the word‑boundary events the engine emits while speaking, trims the leading/trailing silence some engines add, and then places line breaks — so each cue starts when its first word is actually heard.

**Can it generate a talking‑head avatar?** No — HeadVox doesn't render faces. It produces the voiceover, captions and per‑word timings that an avatar or lip‑sync tool consumes, and it can put the result on an avatar clip you already have.

**Can I use the output commercially?** HeadVox's code is MIT. Rights to synthesized speech depend on the TTS service you use — check its terms for your use case.

**Is this affiliated with Microsoft or edge‑tts?** No. HeadVox is an independent, original project that uses `edge-tts` as one optional backend.

## How it works

1. **Parse** — split the script into speakable segments, strip Markdown, honour `[pause]` directives.
2. **Synthesize** — call the backend per segment, cached by text + voice settings.
3. **Assemble** — build one 24 kHz track, trimming engine padding so pauses are exact.
4. **Caption** — build cues from word boundaries, breaking at punctuation within a CJK‑aware width budget.
5. **Mux** *(optional)* — ffmpeg puts it on video, loops the clip, ducks music, adds soft or burned‑in subtitles.

## Development

```bash
git clone https://github.com/yyert123/headvox.git
cd headvox
pip install -e ".[dev]"
pytest            # runs fully offline via the 'sine' backend
```

Issues and pull requests are welcome — especially new backends, more languages' line‑breaking rules, and caption styles.

## Citation

If HeadVox helps your research or course, see [`CITATION.cff`](https://github.com/yyert123/headvox/blob/main/CITATION.cff).

## License

[MIT](https://github.com/yyert123/headvox/blob/main/LICENSE). HeadVox is original work and is not affiliated with Microsoft or the `edge-tts` project.

<!-- keywords: text to speech, TTS, voiceover generator, AI voiceover, subtitle generator, SRT generator, WebVTT, word-level timestamps, talking head video, faceless video, YouTube Shorts, TikTok, Bilibili, Douyin, edge-tts, Chinese TTS, Japanese TTS, 文字转语音, 配音, 口播, 字幕生成, 音声合成, 字幕 -->
