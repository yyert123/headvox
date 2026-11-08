"""Core pipeline: script -> per-segment TTS -> one audio track + captions."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Union

from .backends import SegmentAudio, TTSBackend, WordMark, get_backend
from .captions import Cue, build_cues, write_srt, write_vtt
from .script import Script, Segment

SAMPLE_RATE = 24_000
BYTES_PER_MS = SAMPLE_RATE * 2 // 1000  # mono s16le


@dataclass
class VoiceSettings:
    voice: Optional[str] = None
    rate_pct: float = 0.0  # +10 -> 10% faster
    pitch_hz: float = 0.0
    volume_pct: float = 0.0

    def key(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


@dataclass
class TimedSegment:
    index: int
    text: str
    start_ms: int
    end_ms: int
    pause_after_ms: int
    words: List[WordMark] = field(default_factory=list)


@dataclass
class SynthResult:
    audio_path: Path
    srt_path: Path
    vtt_path: Path
    manifest_path: Path
    duration_ms: int
    segments: List[TimedSegment]
    cues: List[Cue]
    video_path: Optional[Path] = None


# ---------------------------------------------------------------- ffmpeg

def _need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise RuntimeError(
            f"{tool} not found on PATH. HeadVox uses ffmpeg/ffprobe for audio; "
            "install it from https://ffmpeg.org or your package manager."
        )
    return path


def _decode_to_pcm(data: bytes, fmt: str) -> bytes:
    """Decode any audio blob to mono 24 kHz s16le PCM."""
    ffmpeg = _need("ffmpeg")
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", fmt, "-i", "pipe:0",
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "pipe:1"],
        input=data, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg could not decode {fmt} audio: {proc.stderr.decode(errors='ignore')}")
    return proc.stdout


def _trim_silence_tail(pcm: bytes, threshold: int = 300, keep_ms: int = 60) -> bytes:
    """Drop trailing near-silence some TTS engines pad onto each clip, so the
    pauses HeadVox inserts are the pauses the listener actually hears."""
    import array

    a = array.array("h")
    a.frombytes(pcm[: len(pcm) // 2 * 2])
    end = len(a)
    while end > 0 and abs(a[end - 1]) < threshold:
        end -= 1
    end = min(len(a), end + SAMPLE_RATE * keep_ms // 1000)
    return a[:end].tobytes()


def _encode(pcm: bytes, out: Path) -> None:
    ffmpeg = _need("ffmpeg")
    codec = ["-c:a", "libmp3lame", "-b:a", "128k"] if out.suffix.lower() == ".mp3" else []
    if out.suffix.lower() == ".m4a":
        codec = ["-c:a", "aac", "-b:a", "160k"]
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SAMPLE_RATE),
         "-ac", "1", "-i", "pipe:0", *codec, str(out)],
        input=pcm, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg encode failed: {proc.stderr.decode(errors='ignore')}")


# ---------------------------------------------------------------- cache

class _Cache:
    def __init__(self, root: Optional[Path]) -> None:
        self.root = root
        if root:
            root.mkdir(parents=True, exist_ok=True)

    def _key(self, backend: str, text: str, settings: VoiceSettings) -> str:
        h = hashlib.sha256(f"{backend}\x00{settings.key()}\x00{text}".encode()).hexdigest()
        return h[:32]

    def get(self, backend, text, settings) -> Optional[SegmentAudio]:
        if not self.root:
            return None
        k = self._key(backend, text, settings)
        meta, blob = self.root / f"{k}.json", self.root / f"{k}.bin"
        if not (meta.exists() and blob.exists()):
            return None
        m = json.loads(meta.read_text("utf-8"))
        return SegmentAudio(
            blob.read_bytes(), m["format"], m["duration_ms"], [WordMark(**w) for w in m["words"]]
        )

    def put(self, backend, text, settings, seg: SegmentAudio) -> None:
        if not self.root:
            return
        k = self._key(backend, text, settings)
        (self.root / f"{k}.bin").write_bytes(seg.audio)
        (self.root / f"{k}.json").write_text(
            json.dumps({"format": seg.audio_format, "duration_ms": seg.duration_ms,
                        "words": [asdict(w) for w in seg.words]}, ensure_ascii=False),
            "utf-8",
        )


# ---------------------------------------------------------------- main API

def synthesize(
    script: Union[Script, str],
    out_dir: Union[str, Path],
    *,
    backend: Union[str, TTSBackend] = "edge",
    settings: Optional[VoiceSettings] = None,
    name: str = "voiceover",
    audio_format: str = "mp3",
    cache_dir: Optional[Union[str, Path]] = None,
    caption_max_chars: int = 42,
    caption_max_ms: int = 5000,
    lead_in_ms: int = 150,
    trim_tts_padding: bool = True,
    backend_options: Optional[dict] = None,
    progress: Optional[Callable[[int, int, Segment], None]] = None,
) -> SynthResult:
    """Render a script into ``<out_dir>/<name>.{mp3,srt,vtt,json}``."""
    if isinstance(script, str):
        script = Script.from_text(script)
    if not script.segments:
        raise ValueError("script is empty: nothing to say")
    settings = settings or VoiceSettings()
    tts = get_backend(backend, **(backend_options or {})) if isinstance(backend, str) else backend
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cache = _Cache(Path(cache_dir) if cache_dir else None)

    pcm = bytearray(b"\x00\x00" * (SAMPLE_RATE * lead_in_ms // 1000))
    timed: List[TimedSegment] = []
    total = len(script.segments)
    for i, seg in enumerate(script.segments):
        if progress:
            progress(i, total, seg)
        clip = cache.get(tts.name, seg.text, settings)
        if clip is None:
            clip = tts.synthesize_segment(seg.text, settings)
            if not clip.audio:
                raise RuntimeError(f"backend {tts.name!r} returned no audio for: {seg.text!r}")
            cache.put(tts.name, seg.text, settings, clip)
        clip_pcm = _decode_to_pcm(clip.audio, clip.audio_format)
        if trim_tts_padding:
            last_word = clip.words[-1].end_ms if clip.words else 0
            trimmed = _trim_silence_tail(clip_pcm)
            # never cut into the last spoken word
            min_len = (last_word + 40) * BYTES_PER_MS
            clip_pcm = trimmed if len(trimmed) >= min_len else clip_pcm[: max(len(trimmed), min_len)]
        start_ms = len(pcm) // BYTES_PER_MS
        pcm += clip_pcm
        end_ms = len(pcm) // BYTES_PER_MS
        words = [WordMark(w.text, start_ms + w.start_ms, min(end_ms, start_ms + w.end_ms)) for w in clip.words]
        timed.append(TimedSegment(i, seg.text, start_ms, end_ms, seg.pause_after_ms, words))
        pcm += b"\x00\x00" * (SAMPLE_RATE * seg.pause_after_ms // 1000)
    pcm += b"\x00\x00" * (SAMPLE_RATE * 300 // 1000)  # gentle tail
    if progress:
        progress(total, total, script.segments[-1])

    audio_path = out / f"{name}.{audio_format}"
    _encode(bytes(pcm), audio_path)
    duration_ms = len(pcm) // BYTES_PER_MS

    cues = build_cues(timed, max_chars=caption_max_chars, max_ms=caption_max_ms)
    srt_path, vtt_path = out / f"{name}.srt", out / f"{name}.vtt"
    write_srt(cues, srt_path)
    write_vtt(cues, vtt_path)

    manifest_path = out / f"{name}.json"
    manifest = {
        "tool": "headvox",
        "backend": tts.name,
        "settings": asdict(settings),
        "audio": audio_path.name,
        "duration_ms": duration_ms,
        "segments": [
            {"index": t.index, "text": t.text, "start_ms": t.start_ms, "end_ms": t.end_ms,
             "words": [asdict(w) for w in t.words]}
            for t in timed
        ],
        "cues": [asdict(c) for c in cues],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
    return SynthResult(audio_path, srt_path, vtt_path, manifest_path, duration_ms, timed, cues)


def probe_duration_ms(path: Union[str, Path]) -> int:
    ffprobe = _need("ffprobe")
    p = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return int(round(float(p.stdout.strip()) * 1000))


def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(Path.home(), ".cache")
    return Path(base) / "headvox"

