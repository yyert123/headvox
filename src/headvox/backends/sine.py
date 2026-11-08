"""Offline "sine" backend.

Produces a soft tone per word instead of speech. It needs no network and no
extra packages, so it's what the test suite uses, and it's handy for checking
pacing, caption layout, and video muxing before spending real TTS calls.
"""
from __future__ import annotations

import io
import math
import struct
import wave

from . import SegmentAudio, WordMark
from ..script import iter_words

SAMPLE_RATE = 24_000


class SineBackend:
    name = "sine"

    def __init__(self, ms_per_word: int = 260, ms_per_cjk: int = 210, gap_ms: int = 40) -> None:
        self.ms_per_word = ms_per_word
        self.ms_per_cjk = ms_per_cjk
        self.gap_ms = gap_ms

    def synthesize_segment(self, text: str, settings) -> SegmentAudio:
        speed = max(0.25, 1.0 + settings.rate_pct / 100.0)
        freq = 220.0 * (2 ** (settings.pitch_hz / 1200.0)) if settings.pitch_hz else 220.0
        frames = bytearray()
        words = []
        t = 0
        for tok in iter_words(text):
            if not any(ch.isalnum() for ch in tok):
                continue  # punctuation is silent
            base = self.ms_per_cjk if len(tok) == 1 and ord(tok) > 0x2E80 else self.ms_per_word
            dur = int(base / speed)
            frames += _tone(freq, dur)
            frames += _silence(self.gap_ms)
            words.append(WordMark(tok, t, t + dur))
            t += dur + self.gap_ms
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(bytes(frames))
        return SegmentAudio(buf.getvalue(), "wav", t, words)


def _tone(freq: float, ms: int) -> bytes:
    n = int(SAMPLE_RATE * ms / 1000)
    fade = max(1, int(SAMPLE_RATE * 0.01))
    out = bytearray()
    for i in range(n):
        env = min(1.0, i / fade, (n - i) / fade)
        out += struct.pack("<h", int(6000 * env * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)))
    return bytes(out)


def _silence(ms: int) -> bytes:
    return b"\x00\x00" * int(SAMPLE_RATE * ms / 1000)
