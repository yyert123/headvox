"""Caption building: word timings -> readable SRT / WebVTT cues.

Cues never cross a segment boundary, prefer to break after punctuation, and
respect a character budget where a CJK character counts as two columns. The
cue text is sliced from the original script, so punctuation and casing survive
even when the TTS engine reports bare words.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .script import _is_wide, _visual_len

_BREAK_AFTER = set("。！？!?…，,；;：:、.")


@dataclass
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str


def _locate(text: str, words) -> List[Optional[Tuple[int, int]]]:
    """Find each word's span in ``text``, scanning left to right."""
    spans: List[Optional[Tuple[int, int]]] = []
    cursor = 0
    low = text.lower()
    for w in words:
        needle = w.text.strip().lower()
        if not needle:
            spans.append(None)
            continue
        idx = low.find(needle, cursor)
        if idx == -1 or idx - cursor > 40:
            spans.append(None)
            continue
        spans.append((idx, idx + len(needle)))
        cursor = idx + len(needle)
    return spans


def _extend_punct(text: str, end: int) -> int:
    while end < len(text) and (text[end] in _BREAK_AFTER or text[end] in "\"'”’」』）)】]"):
        end += 1
    return end


def _join_words(tokens: Sequence[str]) -> str:
    out = ""
    for t in tokens:
        if out and not (_is_wide(out[-1]) or _is_wide(t[0])):
            out += " "
        out += t
    return out


def build_cues(timed_segments, *, max_chars: int = 42, max_ms: int = 5000) -> List[Cue]:
    cues: List[Cue] = []
    budget = max_chars
    for seg in timed_segments:
        words = seg.words
        if not words:
            cues.append(Cue(len(cues) + 1, seg.start_ms, seg.end_ms, seg.text))
            continue
        spans = _locate(seg.text, words)
        group: List[int] = []

        def flush(group_idx: List[int], last_in_segment: bool) -> None:
            first, last = group_idx[0], group_idx[-1]
            s_span, e_span = spans[first], spans[last]
            if s_span and e_span:
                start_char = 0 if first == 0 else s_span[0]
                end_char = len(seg.text) if last_in_segment else _extend_punct(seg.text, e_span[1])
                text = seg.text[start_char:end_char].strip()
            else:
                text = _join_words([words[k].text for k in group_idx])
            start = words[first].start_ms
            end = seg.end_ms if last_in_segment else words[last].end_ms
            cues.append(Cue(len(cues) + 1, start, max(end, start + 200), text))

        def breaks_after(k: int) -> bool:
            sp = spans[k]
            return bool(sp) and sp[1] < len(seg.text) and seg.text[sp[1]] in _BREAK_AFTER

        for i, w in enumerate(words):
            group.append(i)
            if i + 1 >= len(words):
                break
            cur_len = _visual_len(_join_words([words[k].text for k in group]))
            nxt_len = _visual_len(_join_words([words[k].text for k in group] + [words[i + 1].text]))
            dur = w.end_ms - words[group[0]].start_ms
            if cur_len >= budget * 0.6 and breaks_after(i):
                flush(group, False)
                group = []
            elif nxt_len > budget or dur >= max_ms:
                # back up to the last punctuation in this cue when there is one,
                # so lines end on a natural phrase instead of mid-word
                cut = next((j for j in range(len(group) - 1, 0, -1) if breaks_after(group[j - 1])), None)
                if cut is not None and cut < len(group):
                    flush(group[:cut], False)
                    group = group[cut:]
                else:
                    flush(group, False)
                    group = []
        if group:
            flush(group, True)

    # make cues contiguous enough to read, without overlapping
    for a, b in zip(cues, cues[1:]):
        if b.start_ms - a.end_ms < 120:
            a.end_ms = max(a.start_ms + 200, b.start_ms - 1)
    return cues


def _ts(ms: int, sep: str) -> str:
    h, rem = divmod(max(0, ms), 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_srt(cues: Sequence[Cue]) -> str:
    return "\n".join(
        f"{c.index}\n{_ts(c.start_ms, ',')} --> {_ts(c.end_ms, ',')}\n{c.text}\n" for c in cues
    )


def to_vtt(cues: Sequence[Cue]) -> str:
    body = "\n".join(f"{_ts(c.start_ms, '.')} --> {_ts(c.end_ms, '.')}\n{c.text}\n" for c in cues)
    return "WEBVTT\n\n" + body


def write_srt(cues: Sequence[Cue], path: Path) -> None:
    Path(path).write_text(to_srt(cues), "utf-8")


def write_vtt(cues: Sequence[Cue], path: Path) -> None:
    Path(path).write_text(to_vtt(cues), "utf-8")
