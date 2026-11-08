import json
import shutil
import subprocess
import sys

import pytest

from headvox import synthesize, Script, VoiceSettings
from headvox.captions import to_srt
from headvox.cli import main
from headvox.synth import probe_duration_ms

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg required")

SCRIPT = """# Demo

Welcome to HeadVox. This line is the second sentence.

第二段：中文也可以，标点会被保留。[pause 0.5s] Last one!
"""


def test_end_to_end_offline(tmp_path):
    res = synthesize(Script.from_text(SCRIPT), tmp_path, backend="sine", name="demo")
    for p in (res.audio_path, res.srt_path, res.vtt_path, res.manifest_path):
        assert p.exists() and p.stat().st_size > 0
    real = probe_duration_ms(res.audio_path)
    assert abs(real - res.duration_ms) < 150  # mp3 frame padding
    # captions are ordered, non-overlapping and inside the audio
    prev_end = 0
    for c in res.cues:
        assert c.start_ms >= prev_end - 1
        assert c.end_ms > c.start_ms
        assert c.end_ms <= res.duration_ms
        prev_end = c.end_ms
    srt = res.srt_path.read_text("utf-8")
    assert "Welcome to HeadVox." in srt
    assert "标点会被保留" in srt
    assert res.vtt_path.read_text("utf-8").startswith("WEBVTT")
    m = json.loads(res.manifest_path.read_text("utf-8"))
    assert m["backend"] == "sine" and len(m["segments"]) == len(res.segments)


def test_cache_reuses_audio(tmp_path):
    calls = []

    from headvox.backends.sine import SineBackend

    class Counting(SineBackend):
        def synthesize_segment(self, text, settings):
            calls.append(text)
            return super().synthesize_segment(text, settings)

    kw = dict(backend=Counting(), cache_dir=tmp_path / "cache")
    synthesize("One. Two.", tmp_path / "a", **kw)
    n = len(calls)
    synthesize("One. Two.", tmp_path / "b", **kw)
    assert n == 2 and len(calls) == 2
    synthesize("One. Two.", tmp_path / "c", settings=VoiceSettings(rate_pct=10), **kw)
    assert len(calls) == 4  # settings are part of the cache key


def test_cli_and_video(tmp_path):
    script = tmp_path / "s.md"
    script.write_text(SCRIPT, "utf-8")
    clip = tmp_path / "face.mp4"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25",
         "-t", "1", "-pix_fmt", "yuv420p", str(clip)], check=True,
    )
    out = tmp_path / "out"
    rc = main([str(script), "-o", str(out), "-b", "sine", "--video", str(clip), "-q"])
    assert rc == 0
    video = out / "voiceover.mp4"
    assert video.exists()
    v = probe_duration_ms(video)
    a = probe_duration_ms(out / "voiceover.mp3")
    assert abs(v - a) < 250  # 1 s clip was looped to the voiceover length
    streams = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert streams.count("video") == 1 and streams.count("audio") == 1 and "subtitle" in streams


def test_dry_run(capsys, tmp_path):
    s = tmp_path / "s.txt"
    s.write_text("A. B.", "utf-8")
    assert main([str(s), "--dry-run"]) == 0
    assert "A." in capsys.readouterr().out


def test_srt_format():
    from headvox.captions import Cue
    assert to_srt([Cue(1, 0, 1234, "hi")]).startswith("1\n00:00:00,000 --> 00:00:01,234\nhi")


def test_module_entrypoint():
    r = subprocess.run([sys.executable, "-m", "headvox", "--version"], capture_output=True, text=True)
    assert r.returncode == 0 and "headvox" in r.stdout
