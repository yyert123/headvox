# Changelog

## 0.1.2
- README v2 in all three languages: real demo GIF/MP4, measured performance table, pipeline diagram, roadmap, risks & limitations.
- Added `scripts/bench.py` (reproducible benchmark) and `scripts/render_demo.py` (karaoke preview renderer).
- No changes to the library code.

## 0.1.1
- Documentation: full English README, plus Simplified Chinese and Japanese READMEs.
- Project links (GitHub, live samples, docs) and expanded keywords/classifiers on PyPI.
- Added `llms.txt` and `CITATION.cff`.
- No changes to the library code.

## 0.1.0
- First release.
- Script -> voiceover pipeline with Markdown parsing and pause directives.
- `edge` (online neural) and `sine` (offline) TTS backends, with a backend registry.
- Word-aligned SRT and WebVTT captions, line-broken by punctuation and a CJK-aware width budget.
- JSON timing manifest (per-segment and per-word).
- Per-clip caching keyed by text + voice settings.
- Video muxing with looped clip, ducked background music, and soft or burned-in subtitles.
- CLI (`headvox`) and Python API; test suite runs fully offline.
