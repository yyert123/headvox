"""Pluggable TTS backends.

A backend turns a short piece of text into audio bytes plus optional word
boundaries. Register your own with :func:`register_backend` and select it by
name on the command line or through :func:`headvox.synthesize`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Protocol, runtime_checkable


@dataclass
class WordMark:
    """A word and where it falls inside a segment's audio (milliseconds)."""

    text: str
    start_ms: int
    end_ms: int


@dataclass
class SegmentAudio:
    """Result of synthesizing one segment."""

    audio: bytes
    audio_format: str  # "mp3" or "wav"
    duration_ms: int
    words: List[WordMark] = field(default_factory=list)


@runtime_checkable
class TTSBackend(Protocol):
    """Interface every backend implements."""

    name: str

    def synthesize_segment(self, text: str, settings) -> SegmentAudio:  # noqa: D401
        ...


_REGISTRY: Dict[str, Callable[..., TTSBackend]] = {}


def register_backend(name: str, factory: Callable[..., TTSBackend]) -> None:
    _REGISTRY[name.lower()] = factory


def available_backends() -> List[str]:
    return sorted(_REGISTRY)


def get_backend(name: str, **kwargs) -> TTSBackend:
    key = name.lower()
    if key not in _REGISTRY:
        raise ValueError(
            f"unknown backend {name!r}; available: {', '.join(available_backends()) or '(none)'}"
        )
    return _REGISTRY[key](**kwargs)


# Register the backends that ship with HeadVox. Imports are deferred inside the
# factories so a missing optional dependency only fails when that backend is
# actually used.

def _edge_factory(**kw):
    from .edge import EdgeBackend

    return EdgeBackend(**kw)


def _sine_factory(**kw):
    from .sine import SineBackend

    return SineBackend(**kw)


register_backend("edge", _edge_factory)
register_backend("sine", _sine_factory)
