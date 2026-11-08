"""Edge TTS backend.

Wraps the `edge-tts` project (Microsoft Edge's online neural voices, free to
use) behind HeadVox's backend interface. It returns MP3 audio and real
word-boundary marks, which is what makes tight caption alignment possible.

Install the optional dependency::

    pip install "headvox[edge]"

HeadVox does not bundle or re-host any voice model; it calls the same public
service the `edge-tts` CLI uses.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional

from . import SegmentAudio, WordMark


def _fmt_pct(v: float, unit: str = "%") -> str:
    sign = "+" if v >= 0 else "-"
    return f"{sign}{abs(int(round(v)))}{unit}"


class EdgeBackend:
    """TTS backend backed by edge-tts neural voices."""

    name = "edge"

    def __init__(self, proxy: Optional[str] = None) -> None:
        try:
            import edge_tts  # noqa: F401
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "the 'edge' backend needs edge-tts; install with "
                "pip install \"headvox[edge]\""
            ) from exc
        self.proxy = proxy

    def synthesize_segment(self, text: str, settings) -> SegmentAudio:
        return asyncio.run(self._run(text, settings))

    async def _run(self, text: str, settings) -> SegmentAudio:
        import edge_tts

        comm = edge_tts.Communicate(
            text,
            voice=settings.voice or "en-US-EmmaMultilingualNeural",
            rate=_fmt_pct(settings.rate_pct),
            volume=_fmt_pct(settings.volume_pct),
            pitch=_fmt_pct(settings.pitch_hz, "Hz"),
            boundary="WordBoundary",
            proxy=self.proxy,
        )
        audio = bytearray()
        words: List[WordMark] = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                start = int(chunk["offset"] / 10_000)  # 100-ns ticks -> ms
                dur = int(chunk["duration"] / 10_000)
                words.append(WordMark(chunk["text"], start, start + dur))
        duration_ms = words[-1].end_ms if words else 0
        return SegmentAudio(
            audio=bytes(audio),
            audio_format="mp3",
            duration_ms=duration_ms,
            words=words,
        )

