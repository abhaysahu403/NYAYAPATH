"""Text cleaning and structure-preserving chunking (Hindi + English)."""
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

_WS = re.compile(r"[ \t\u00a0]+")
_BLANKS = re.compile(r"\n{3,}")
_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*[.)]\s+\S.*|[IVXLC]+\.\s+\S.*|[A-Z][A-Z0-9 ,&/\-()]{3,80}|(?:अध्याय|धारा|खंड|भाग)\s*\S.*)$")
_SENT_SPLIT = re.compile(r"(?<=[.!?।])\s+")


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"-\n(?=[a-z])", "", text)  # de-hyphenate line breaks
    text = "\n".join(_WS.sub(" ", ln).strip() for ln in text.split("\n"))
    return _BLANKS.sub("\n\n", text).strip()


def is_heading(line: str) -> bool:
    line = line.strip()
    if not (3 <= len(line) <= 100):
        return False
    return bool(_HEADING.match(line)) or (len(line.split()) <= 8 and not line.endswith((".", ",", ";", "।", ":")) and line[0].isupper())


@dataclass
class TextChunk:
    text: str
    page_number: Optional[int]
    section_title: Optional[str]
    char_start: int = 0
    char_end: int = 0


def _split_long(paragraph: str, max_chars: int) -> List[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    out, cur = [], ""
    for sent in _SENT_SPLIT.split(paragraph):
        while len(sent) > max_chars:  # unbroken run: hard split
            out.append(sent[:max_chars])
            sent = sent[max_chars:]
        if cur and len(cur) + len(sent) + 1 > max_chars:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_pages(pages: Iterable[Tuple[Optional[int], str]], max_chars: int = 1200, min_chars: int = 200) -> List[TextChunk]:
    """Split (page_number, text) pairs into paragraph-aware chunks.

    Keeps page number and the most recent heading with every chunk so answers can cite page/section.
    Chunks never span pages (citations stay exact).
    """
    chunks: List[TextChunk] = []
    offset = 0
    for page_no, raw in pages:
        text = clean_text(raw)
        if not text:
            continue
        section: Optional[str] = None
        buf: List[str] = []
        buf_len = 0
        buf_section = None

        def flush():
            nonlocal buf, buf_len, offset
            if buf:
                body = "\n\n".join(buf).strip()
                if body:
                    chunks.append(TextChunk(body, page_no, buf_section, offset, offset + len(body)))
                    offset += len(body)
            buf, buf_len = [], 0

        for para in re.split(r"\n\s*\n", text):
            para = para.strip()
            if not para:
                continue
            first = para.split("\n", 1)[0]
            if "\n" not in para and is_heading(para) and len(para) < 100:
                flush()
                section = para
                continue
            if "\n" in para and is_heading(first) and len(first) < 100 and not first.endswith("."):
                section = first
            for piece in _split_long(para.replace("\n", " "), max_chars):
                if buf and buf_len + len(piece) > max_chars:
                    flush()
                if not buf:
                    buf_section = section
                buf.append(piece)
                buf_len += len(piece) + 2
        flush()
    # merge tiny trailing chunks on the same page/section
    merged: List[TextChunk] = []
    for ch in chunks:
        prev = merged[-1] if merged else None
        if prev and len(ch.text) < min_chars and prev.page_number == ch.page_number and len(prev.text) + len(ch.text) <= max_chars:
            prev.text += "\n\n" + ch.text
            prev.char_end = ch.char_end
        else:
            merged.append(ch)
    return merged
