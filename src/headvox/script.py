"""Script parsing: Markdown/plain text -> speakable segments.

Rules
-----
* Markdown formatting (headings, emphasis, links, code fences, list bullets,
  block quotes, images, HTML tags) is stripped down to the words a narrator
  would actually say.
* Blank lines separate paragraphs. A paragraph break inserts a longer pause
  than a sentence break.
* Inline directives let the writer control pacing:
      [pause]          -> default extra pause (600 ms)
      [pause 1.5s]     -> 1.5 s pause
      [pause 400ms]    -> 400 ms pause
* Long sentences are split at the nearest clause punctuation so no single
  TTS request (or caption) grows unwieldy. CJK and Latin punctuation are both
  understood, so mixed Chinese/English scripts segment naturally.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List

# Sentence-ending punctuation (Latin + CJK). Closing quotes/brackets that
# follow the terminator stay attached to the sentence.
_SENT_END = r"[。！？!?…]+|(?<![0-9A-Z])\.(?=\s|$)"
_CLOSERS = "\"'”’」』）)】]"
_CLAUSE = "，,；;：:、—"

_PAUSE_RE = re.compile(r"\[pause(?:\s+([0-9]*\.?[0-9]+)\s*(ms|s)?)?\]", re.IGNORECASE)

DEFAULT_PAUSE_MS = 600


@dataclass
class Segment:
    """One unit of speech sent to the TTS backend."""

    text: str
    pause_after_ms: int = 0
    paragraph: int = 0

    def __post_init__(self) -> None:
        self.text = self.text.strip()


@dataclass
class Script:
    segments: List[Segment] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str, **kw) -> "Script":
        return cls(split_script(text, **kw))

    @classmethod
    def from_file(cls, path: str, **kw) -> "Script":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_text(fh.read(), **kw)

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.segments)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.segments)

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self.segments)


# ---------------------------------------------------------------- markdown

def strip_markdown(text: str) -> str:
    """Reduce Markdown to narratable prose while keeping paragraph breaks."""
    # fenced code blocks are not narrated
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.S)
    # HTML comments are author notes
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # front matter
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    out_lines = []
    for line in text.splitlines():
        s = line.strip()
        s = re.sub(r"^#{1,6}\s+", "", s)  # headings
        s = re.sub(r"^>\s?", "", s)  # quotes
        s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)  # list bullets
        s = re.sub(r"^\|.*\|$", "", s) if re.match(r"^\|[\s:-|]+\|$", s) else s  # table rules
        s = s.replace("|", " ") if s.startswith("|") else s
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)  # images
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)  # links -> label
        s = re.sub(r"`([^`]*)`", r"\1", s)  # inline code
        s = re.sub(r"(\*\*|__)(.+?)\1", r"\2", s)  # bold
        s = re.sub(r"(?<![\w*])([*_])(?!\s)(.+?)(?<!\s)\1(?![\w*])", r"\2", s)  # italics
        s = re.sub(r"~~(.+?)~~", r"\1", s)
        s = re.sub(r"<[^>]+>", "", s)  # html tags
        if re.fullmatch(r"[-*_]{3,}", s):  # horizontal rule
            s = ""
        out_lines.append(s)
    return "\n".join(out_lines)


# ---------------------------------------------------------------- splitting

def _parse_pause(m: re.Match) -> int:
    num, unit = m.group(1), (m.group(2) or "").lower()
    if num is None:
        return DEFAULT_PAUSE_MS
    val = float(num)
    if unit == "ms":
        return int(round(val))
    # bare numbers and "s" are seconds
    return int(round(val * 1000))


def _sentences(par: str) -> List[str]:
    parts: List[str] = []
    buf = ""
    i = 0
    pattern = re.compile(_SENT_END)
    while i < len(par):
        m = pattern.search(par, i)
        if not m:
            buf += par[i:]
            break
        end = m.end()
        while end < len(par) and par[end] in _CLOSERS:
            end += 1
        buf += par[i:end]
        parts.append(buf)
        buf = ""
        i = end
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def _visual_len(s: str) -> int:
    """Approximate spoken length: CJK chars count double (≈ a Latin word)."""
    n = 0
    for ch in s:
        n += 2 if _is_wide(ch) else 1
    return n


def _is_wide(ch: str) -> bool:
    o = ord(ch)
    return (
        0x1100 <= o <= 0x115F
        or 0x2E80 <= o <= 0xA4CF
        or 0xAC00 <= o <= 0xD7A3
        or 0xF900 <= o <= 0xFAFF
        or 0xFE30 <= o <= 0xFE4F
        or 0xFF00 <= o <= 0xFF60
        or 0xFFE0 <= o <= 0xFFE6
    )


def _split_long(sentence: str, max_len: int) -> List[str]:
    if _visual_len(sentence) <= max_len:
        return [sentence]
    # break at the clause punctuation closest to the middle
    best = None
    mid = len(sentence) / 2
    for idx, ch in enumerate(sentence[:-1]):
        if ch in _CLAUSE:
            if best is None or abs(idx - mid) < abs(best - mid):
                best = idx
    if best is None:
        # fall back to the space closest to the middle
        for idx, ch in enumerate(sentence):
            if ch == " " and (best is None or abs(idx - mid) < abs(best - mid)):
                best = idx
    if best is None:
        # hard split (e.g. one huge CJK run with no punctuation)
        cut = max(1, int(mid))
        return _split_long(sentence[:cut], max_len) + _split_long(sentence[cut:], max_len)
    left, right = sentence[: best + 1].strip(), sentence[best + 1 :].strip()
    return [p for p in _split_long(left, max_len) + _split_long(right, max_len) if p]


def split_script(
    text: str,
    *,
    markdown: bool = True,
    max_len: int = 120,
    sentence_pause_ms: int = 250,
    paragraph_pause_ms: int = 700,
) -> List[Segment]:
    """Split a script into :class:`Segment` objects ready for synthesis."""
    if markdown:
        text = strip_markdown(text)
    text = text.replace("\r\n", "\n")
    paragraphs = re.split(r"\n\s*\n", text)
    segments: List[Segment] = []
    for p_idx, par in enumerate(paragraphs):
        par = " ".join(l.strip() for l in par.splitlines() if l.strip())
        if not par:
            continue
        # walk through pause directives inside the paragraph
        pos = 0
        chunks: List[tuple] = []  # (text, extra_pause)
        for m in _PAUSE_RE.finditer(par):
            chunks.append((par[pos : m.start()], _parse_pause(m)))
            pos = m.end()
        chunks.append((par[pos:], 0))
        par_segments: List[Segment] = []
        for chunk_text, extra in chunks:
            pieces: List[str] = []
            for sent in _sentences(chunk_text):
                pieces.extend(_split_long(sent, max_len))
            for piece in pieces:
                par_segments.append(Segment(piece, sentence_pause_ms, p_idx))
            if extra:
                if par_segments:
                    par_segments[-1].pause_after_ms += extra
                elif segments:
                    segments[-1].pause_after_ms += extra
        if par_segments:
            par_segments[-1].pause_after_ms = max(
                par_segments[-1].pause_after_ms, paragraph_pause_ms
            )
            segments.extend(par_segments)
    if segments:
        segments[-1].pause_after_ms = 0
    return [s for s in segments if s.text]


def iter_words(text: str) -> Iterable[str]:
    """Tokenize for captioning: Latin words stay whole, CJK splits per char."""
    for tok in re.findall(r"[A-Za-z0-9'’\-]+[.,!?;:]*|[^\sA-Za-z0-9]", text):
        yield tok
