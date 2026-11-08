"""Reproducible HeadVox benchmark: wall time, cache speed-up and caption stats.

Usage:  python scripts/bench.py examples/demo-en.md examples/demo-zh.md [--backend edge]
"""
import argparse, json, shutil, tempfile, time
from pathlib import Path
from headvox import synthesize, Script
from headvox.script import _visual_len

def run(path, backend, voice):
    out = Path(tempfile.mkdtemp(prefix="hvbench-"))
    cache = out / "cache"
    kw = dict(backend=backend, cache_dir=str(cache))
    if voice:
        from headvox import VoiceSettings
        kw["settings"] = VoiceSettings(voice=voice)
    t0 = time.perf_counter(); res = synthesize(Script.from_file(path), out / "a", **kw); cold = time.perf_counter() - t0
    t0 = time.perf_counter(); synthesize(Script.from_file(path), out / "b", **kw); warm = time.perf_counter() - t0
    widths = [_visual_len(c.text) for c in res.cues]
    gaps = [b.start_ms - a.end_ms for a, b in zip(res.cues, res.cues[1:])]
    shutil.rmtree(out, ignore_errors=True)
    return {
        "script": Path(path).name, "backend": backend,
        "audio_s": round(res.duration_ms / 1000, 2), "cues": len(res.cues),
        "max_cue_width": max(widths), "overlapping_cues": sum(g < 0 for g in gaps),
        "cold_s": round(cold, 2), "cached_s": round(warm, 2),
        "rtf_cold": round(cold / (res.duration_ms / 1000), 3),
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", nargs="+")
    ap.add_argument("--backend", default="edge")
    ap.add_argument("--voice", default=None)
    a = ap.parse_args()
    for p in a.scripts:
        print(json.dumps(run(p, a.backend, a.voice), ensure_ascii=False))
