"""HeadVox — turn a script into a talking-head voiceover with aligned captions.

HeadVox reads a plain-text or Markdown script, synthesizes it segment by
segment through a pluggable TTS backend, stitches the audio into a single
track, and emits word-aligned subtitles plus a timing manifest you can use
to drive a talking-head avatar or a video editor.

Public API:
    from headvox import synthesize, Script, get_backend

Everything here is original work, released under the MIT License.
"""
from __future__ import annotations

from .script import Script, Segment, split_script
from .backends import TTSBackend, SegmentAudio, WordMark, get_backend, register_backend
from .synth import synthesize, SynthResult, VoiceSettings

__all__ = [
    "Script",
    "Segment",
    "split_script",
    "TTSBackend",
    "SegmentAudio",
    "WordMark",
    "get_backend",
    "register_backend",
    "synthesize",
    "SynthResult",
    "VoiceSettings",
]

__version__ = "0.1.0"
