# HeadVox

**Turn a script into a talking‑head voiceover — with word‑aligned captions — in one command.**

[![PyPI](https://img.shields.io/pypi/v/headvox.svg)](https://pypi.org/project/headvox/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Demo](https://img.shields.io/badge/%F0%9F%A4%97-Live%20samples-yellow)](https://huggingface.co/spaces/headvox/headvox)

**中文简介：** HeadVox 是开源 Python 命令行工具，把文字稿 / Markdown 一条命令变成口播配音，自动生成与声音逐字对齐的 SRT / VTT 字幕和 JSON 逐词时间轴，可直接合成到视频。支持中文、英文、日语。▶ [试听样例](https://huggingface.co/spaces/headvox/headvox)

HeadVox reads a plain‑text or Markdown script, speaks it with a neural TTS voice,
stitches the clips into a single track with natural pauses, and writes
**SRT + WebVTT captions that line up with the audio**, plus a JSON timing manifest
you can feed to a talking‑head avatar or a video editor. Point it at a video clip
and it muxes the voiceover on, loops the clip to length, and attaches the subtitles.

Chinese, English and Japanese work out of the box (mixed CJK/Latin scripts
segment correctly). The voices come from the free [`edge-tts`](https://github.com/rany2/edge-tts)
service; HeadVox does **not** bundle or re‑host any model.

```bash
pip install "headvox[edge]"
headvox script.md -o out/ --voice zh-female --video avatar.mp4
# -> out/voiceover.mp3  out/voiceover.srt  out/voiceover.vtt
#    out/voiceover.json out/voiceover.mp4
```

---

## Why

Making a short explainer or a "talking head" clip usually means three fiddly
steps: generate the audio, hand‑time the subtitles, and mux it onto video.
HeadVox does all three from one script and keeps them in sync, so the captions
actually match the voice instead of drifting a few hundred milliseconds off.

## Features

- **One command, three outputs** — audio, captions (SRT **and** VTT), and a timing manifest.
- **Word‑aligned captions.** With the `edge` backend HeadVox uses real word
  boundaries, then breaks lines at punctuation and a character budget
  (a CJK character counts as two columns) so no caption runs off screen.
- **Pacing you control.** Sentence and paragraph pauses are automatic; drop
  `[pause]`, `[pause 1.5s]` or `[pause 400ms]` anywhere for a beat.
- **Markdown‑aware.** Headings, emphasis, links, code fences and lists are
  reduced to the words a narrator would actually say.
- **Pluggable backends.** `edge` (online neural voices) and `sine` (offline,
  no network, used by the tests and for dry runs). Register your own in a few lines.
- **Caches** every clip, so re‑rendering after a tiny script edit is nearly free.
- **Video muxing** with optional looped, ducked background music, and either
  soft subtitles (toggleable) or burned‑in captions.
- **Pure‑Python, tiny deps.** Only `ffmpeg`/`ffprobe` on your PATH, and
  `edge-tts` if you use the online voices.

## Install

```bash
pip install "headvox[edge]"   # online neural voices
pip install headvox           # library + offline 'sine' backend only
```

You also need **ffmpeg** (with `ffprobe`) on your PATH — <https://ffmpeg.org/download.html>.

## Usage

```bash
# Simplest: script in, files out
headvox talk.md -o out/

# Pick a voice and tweak the delivery
headvox talk.md -o out/ --voice en-female --rate +6 --pitch +1

# Put it on a clip, loop the clip to the voiceover length, duck some music under it
headvox talk.md -o out/ --video avatar.mp4 --music bed.mp3

# Burn captions into the picture instead of a soft track
headvox talk.md -o out/ --video avatar.mp4 --burn-subs

# See how the script will be segmented without calling any TTS
headvox talk.md --dry-run
```

Voice presets: `zh-female`, `zh-male`, `en-female`, `en-male`, `ja-female`, `ja-male`
— or pass any `edge-tts` voice id directly (e.g. `--voice zh-CN-YunxiNeural`).
Run `edge-tts --list-voices` to see them all. Behind a proxy? Use `--proxy`
or set `HEADVOX_PROXY`.

### As a library

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
    print(cue.start_ms, cue.text)
```

`synthesize()` returns paths to the audio, SRT, VTT and manifest, the total
duration, and the per‑segment word timings.

## Timing manifest

`voiceover.json` holds everything downstream tools need to drive an avatar or
re‑style captions:

```json
{
  "tool": "headvox",
  "backend": "edge",
  "duration_ms": 19600,
  "segments": [
    {"index": 0, "text": "Hi everyone, and welcome back.",
     "start_ms": 2398, "end_ms": 4049,
     "words": [{"text": "Hi", "start_ms": 2398, "end_ms": 2560}, ...]}
  ],
  "cues": [{"index": 1, "start_ms": 262, "end_ms": 1573, "text": "HeadVox demo"}]
}
```

## Write your own backend

```python
from headvox.backends import SegmentAudio, WordMark, register_backend

class MyBackend:
    name = "mine"
    def synthesize_segment(self, text, settings):
        audio, fmt, dur = my_tts(text, settings.voice)   # bytes, "wav"/"mp3", ms
        return SegmentAudio(audio, fmt, dur, [WordMark("hi", 0, 200)])

register_backend("mine", lambda **kw: MyBackend())
```

Then `headvox script.md -b mine`.

## How it works

1. **Parse** the script to speech segments, stripping Markdown and honouring pause directives.
2. **Synthesize** each segment through the chosen backend (cached by text + voice settings).
3. **Assemble** one 24 kHz track, trimming the padding some engines add so your pauses are exact.
4. **Caption** from the word boundaries, breaking lines at punctuation within a width budget.
5. **Mux** (optional) onto video with ffmpeg, with ducked music and soft or burned‑in subtitles.

## Development

```bash
git clone https://github.com/yyert123/headvox.git
cd headvox
pip install -e ".[dev]"
pytest          # the suite runs fully offline via the 'sine' backend
```

## License

MIT — see [LICENSE](LICENSE). HeadVox is original work and is not affiliated
with Microsoft or the `edge-tts` project; it simply uses `edge-tts` as one
optional backend.
