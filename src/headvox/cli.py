"""Command line interface: ``headvox script.md -o out/ --voice ...``"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .backends import available_backends
from .script import Script
from .synth import VoiceSettings, default_cache_dir, synthesize

PRESET_VOICES = {
    "zh-female": "zh-CN-XiaoxiaoNeural",
    "zh-male": "zh-CN-YunxiNeural",
    "en-female": "en-US-AvaMultilingualNeural",
    "en-male": "en-US-AndrewMultilingualNeural",
    "ja-female": "ja-JP-NanamiNeural",
    "ja-male": "ja-JP-KeitaNeural",
}


def _signed(v: str) -> float:
    return float(v.rstrip("%").rstrip("Hz").rstrip("hz"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="headvox",
        description="Turn a script into a talking-head voiceover with aligned SRT/VTT captions.",
    )
    p.add_argument("script", help="script file (.md or .txt), or '-' for stdin")
    p.add_argument("-o", "--out", default="headvox-out", help="output directory (default: headvox-out)")
    p.add_argument("-n", "--name", default="voiceover", help="base name for output files")
    p.add_argument("-b", "--backend", default="edge", choices=available_backends())
    p.add_argument("-v", "--voice", default="zh-female",
                   help=f"voice id or preset ({', '.join(PRESET_VOICES)})")
    p.add_argument("--rate", type=_signed, default=0, help="speed change in percent, e.g. +8 or -5")
    p.add_argument("--pitch", type=_signed, default=0, help="pitch change in Hz, e.g. +2")
    p.add_argument("--volume", type=_signed, default=0, help="volume change in percent")
    p.add_argument("--format", default="mp3", choices=["mp3", "wav", "m4a"])
    p.add_argument("--plain", action="store_true", help="treat input as plain text, not Markdown")
    p.add_argument("--max-len", type=int, default=120, help="longest segment sent to TTS")
    p.add_argument("--sentence-pause", type=int, default=250, help="ms between sentences")
    p.add_argument("--paragraph-pause", type=int, default=700, help="ms between paragraphs")
    p.add_argument("--caption-chars", type=int, default=42, help="caption width (CJK char = 2)")
    p.add_argument("--no-cache", action="store_true", help="always call the TTS backend")
    p.add_argument("--proxy", default=None, help="HTTP proxy for online backends")
    p.add_argument("--video", help="video to put the voiceover on")
    p.add_argument("--burn-subs", action="store_true", help="render captions into the picture")
    p.add_argument("--no-subs", action="store_true", help="don't attach captions to the video")
    p.add_argument("--music", help="background music, looped and ducked under the voice")
    p.add_argument("--music-volume", type=float, default=0.12)
    p.add_argument("--fit", choices=["loop", "audio"], default="loop",
                   help="loop the video to the voiceover length, or cut at the shorter one")
    p.add_argument("--dry-run", action="store_true", help="only print how the script will be segmented")
    p.add_argument("-q", "--quiet", action="store_true")
    p.add_argument("--version", action="version", version=f"headvox {__version__}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    raw = sys.stdin.read() if args.script == "-" else Path(args.script).read_text("utf-8")
    script = Script.from_text(
        raw,
        markdown=not args.plain,
        max_len=args.max_len,
        sentence_pause_ms=args.sentence_pause,
        paragraph_pause_ms=args.paragraph_pause,
    )
    if not script.segments:
        print("headvox: the script has nothing to say", file=sys.stderr)
        return 2

    if args.dry_run:
        for i, s in enumerate(script.segments, 1):
            print(f"{i:>3}. [{s.pause_after_ms:>4} ms] {s.text}")
        return 0

    settings = VoiceSettings(
        voice=PRESET_VOICES.get(args.voice, args.voice),
        rate_pct=args.rate, pitch_hz=args.pitch, volume_pct=args.volume,
    )
    backend_opts = {}
    if args.backend == "edge":
        backend_opts["proxy"] = args.proxy or os.environ.get("HEADVOX_PROXY")

    def progress(i, total, seg):
        if args.quiet:
            return
        bar = "#" * int(20 * i / total)
        print(f"\r[{bar:<20}] {i}/{total}", end="" if i < total else "\n", file=sys.stderr, flush=True)

    try:
        res = synthesize(
            script, args.out,
            backend=args.backend, settings=settings, name=args.name,
            audio_format=args.format,
            cache_dir=None if args.no_cache else default_cache_dir(),
            caption_max_chars=args.caption_chars,
            backend_options=backend_opts, progress=progress,
        )
    except Exception as exc:  # surface a clean message on the CLI
        print(f"\nheadvox: {exc}", file=sys.stderr)
        return 1

    outputs = [res.audio_path, res.srt_path, res.vtt_path, res.manifest_path]
    if args.video:
        from .video import mux

        out_video = Path(args.out) / f"{args.name}.mp4"
        try:
            mux(args.video, res.audio_path, out_video,
                subtitles=None if args.no_subs else res.srt_path,
                burn=args.burn_subs, music=args.music,
                music_volume=args.music_volume, fit=args.fit)
        except Exception as exc:
            print(f"headvox: {exc}", file=sys.stderr)
            return 1
        outputs.append(out_video)

    if not args.quiet:
        print(f"duration {res.duration_ms / 1000:.2f}s, {len(res.segments)} segments, {len(res.cues)} captions")
        for o in outputs:
            print(f"  {o}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
