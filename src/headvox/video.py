"""Put the voiceover onto a talking-head (or b-roll) video with ffmpeg."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Union

from .synth import _need, probe_duration_ms


def _has_filter(name: str) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    p = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True, text=True)
    return any(line.split()[1:2] == [name] for line in p.stdout.splitlines() if line.strip())


def _escape_filter_path(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    return s.replace(":", r"\:").replace("'", r"\'")


def mux(
    video: Union[str, Path],
    voiceover: Union[str, Path],
    out: Union[str, Path],
    *,
    subtitles: Optional[Union[str, Path]] = None,
    burn: bool = False,
    music: Optional[Union[str, Path]] = None,
    music_volume: float = 0.12,
    fit: str = "loop",
) -> Path:
    """Combine ``video`` with ``voiceover``.

    fit:
      * ``loop``  — loop the video until the voiceover ends (good for short
        avatar clips or b-roll).
      * ``audio`` — cut at whichever ends first.
    subtitles + burn=False embeds a soft subtitle track (toggle in players);
    burn=True renders them into the picture (needs ffmpeg built with libass).
    music is looped under the voice and ducked with sidechain compression.
    """
    ffmpeg = _need("ffmpeg")
    video, voiceover, out = Path(video), Path(voiceover), Path(out)
    dur_s = probe_duration_ms(voiceover) / 1000.0

    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    if fit == "loop":
        cmd += ["-stream_loop", "-1"]
    cmd += ["-i", str(video), "-i", str(voiceover)]
    n_inputs = 2
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        n_inputs += 1
    sub_input = None
    if subtitles and not burn:
        cmd += ["-i", str(subtitles)]
        sub_input = n_inputs
        n_inputs += 1

    filters = []
    vmap = "0:v:0"
    if subtitles and burn:
        if not _has_filter("subtitles"):
            raise RuntimeError("burning subtitles needs ffmpeg built with libass; use soft subtitles instead")
        filters.append(f"[0:v]subtitles='{_escape_filter_path(Path(subtitles))}'[v]")
        vmap = "[v]"
    amap = "1:a:0"
    if music:
        filters.append(f"[2:a]volume={music_volume}[bg]")
        filters.append("[bg][1:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck]")
        filters.append("[1:a][duck]amix=inputs=2:duration=first:dropout_transition=0[a]")
        amap = "[a]"
    if filters:
        cmd += ["-filter_complex", ";".join(filters)]
    cmd += ["-map", vmap, "-map", amap]
    if sub_input is not None:
        cmd += ["-map", f"{sub_input}:s:0"]
    vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
    cmd += vcodec + ["-c:a", "aac", "-b:a", "160k"]
    if sub_input is not None:
        cmd += ["-c:s", "mov_text" if out.suffix.lower() in (".mp4", ".mov", ".m4v") else "srt"]
    cmd += ["-t", f"{dur_s:.3f}"] if fit == "loop" else ["-shortest"]
    cmd += ["-movflags", "+faststart", str(out)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg mux failed:\n{p.stderr}")
    return out
