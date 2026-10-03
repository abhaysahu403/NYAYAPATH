"""LegalSafetyService: last gate before any AI-written text reaches a citizen.

Removes outcome promises, absolute instructions and individualised legal conclusions, redacts specifics
(fees, deadlines, section numbers) that no retrieved source supports, and guarantees a disclaimer.
Deterministic by design (no LLM): a safety layer must be predictable and testable.
"""
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

DISCLAIMER = {
    "en": "This is legal information, not legal advice. Please verify with a qualified legal professional before taking any action or filing anything.",
    "hi": "यह कानूनी जानकारी है, कानूनी सलाह नहीं। कोई भी कदम उठाने या कुछ दाखिल करने से पहले किसी योग्य वकील से सत्यापित करें।",
}
DISCLAIMER_MARKERS = re.compile(r"qualified\s+(?:legal\s+professional|lawyer)|योग्य\s+(?:वकील|कानूनी)|कानूनी\s+पेशेवर|legal\s+professional", re.I)
EMPTY_FALLBACK = {
    "en": "The available information does not allow a safe, source-backed statement on this point.",
    "hi": "उपलब्ध जानकारी के आधार पर इस बिंदु पर सुरक्षित, स्रोत-समर्थित कथन संभव नहीं है।",
}

_RULES = {
    "OUTCOME_PROMISE": [
        r"\byou\s+(?:will|are\s+going\s+to|shall)\s+(?:definitely\s+|certainly\s+|surely\s+|easily\s+)?(?:win|succeed|get\s+(?:the\s+|your\s+)?(?:land|possession|compensation|bail|justice|relief))",
        r"\bguarantee[sd]?\b", r"\b100\s*%", r"\b(?:sure|certain)\s+to\s+(?:win|succeed)", r"\bcertain(?:ly)?\s+(?:win|succeed)",
        r"\b(?:the\s+)?(?:judge|court)\s+will\s+(?:definitely\s+|certainly\s+|surely\s+)?(?:grant|rule|decide|order|release|punish|favou?r|allow|accept)",
        r"\bno\s+chance\s+of\s+losing", r"\bwithout\s+(?:any\s+)?doubt\b", r"\b(?:aap|tum)\s+(?:zaroor\s+|pakka\s+)?jeet", r"\bpakka\s+(?:jeet|milega|milegi)",
        r"गारंटी", r"जीत\s+(?:जाएंगे|जायेंगे|जाओगे|जाएँगे|पक्की|निश्चित)", r"निश्चित\s+रूप\s+से\s+(?:जीत|मिलेगी|मिलेगा|सफल)",
        r"पक्का\s+(?:जीत|मिलेगा|मिलेगी)", r"न्यायाधीश\s+(?:ज़रूर|जरूर|अवश्य)", r"आप\s+(?:ज़रूर|जरूर)\s+जीत",
    ],
    "ABSOLUTE_INSTRUCTION": [
        r"\byou\s+must\s+(?:definitely|certainly|immediately|absolutely)\b", r"\byou\s+should\s+(?:definitely|certainly)\b",
        r"\bthere\s+is\s+no\s+other\s+(?:option|way)\b", r"आपको\s+(?:निश्चित\s+रूप\s+से|ज़रूर|जरूर|अवश्य)\s+(?:दाखिल|फाइल|केस)",
    ],
    "INDIVIDUAL_CONCLUSION": [
        r"\byou\s+(?:are|'re)\s+the\s+(?:rightful\s+|legal\s+|real\s+)?owner", r"\b(?:the\s+)?(?:land|property|plot)\s+(?:legally\s+)?belongs\s+to\s+you",
        r"\byou\s+have\s+a\s+(?:very\s+)?strong\s+case", r"\byour\s+case\s+is\s+(?:very\s+)?strong", r"\byou\s+(?:will|would)\s+(?:certainly\s+)?lose",
        r"\b(?:your\s+)?(?:neighbou?r|opposite\s+party|respondent)\s+(?:is|has)\s+(?:clearly|definitely|illegally)\b",
        r"आप\s+(?:ही\s+)?(?:असली\s+|वैध\s+)?(?:मालिक|स्वामी)\s+हैं", r"(?:ज़मीन|जमीन)\s+आपकी\s+ही\s+है", r"आपका\s+केस\s+(?:बहुत\s+)?मजबूत",
    ],
}
_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in _RULES.items()}
_NEG_BEFORE = re.compile(r"\b(?:cannot|can't|can\s+not|no\s+one|nobody|not|never|neither|nor|without|no)\b[^.!?।]{0,40}$", re.I)
_NEG_HI_AFTER = re.compile(r"^[^.!?।]{0,30}(?:नहीं|नही|ना\s+दे)")
_NEG_HI_BEFORE = re.compile(r"(?:कोई|किसी)[^.!?।]{0,25}$")
SPECIFIC = re.compile(
    r"(?:(?:Rs\.?|₹|INR)\s?\d[\d,]*(?:\.\d+)?)|(?:\bwithin\s+\d+\s+(?:working\s+)?(?:days?|months?|years?|weeks?))|"
    r"(?:\d+\s*(?:दिन|दिनों|महीने|वर्ष|सप्ताह)\s*(?:के\s+(?:भीतर|अंदर)|में))|(?:\b(?:section|sec\.?|s\.)\s*\d+[A-Za-z]?(?:\(\d+\))?)|"
    r"(?:धारा\s*\d+[A-Za-z]?)|(?:\bArticle\s+\d+[A-Za-z]?)|(?:\bOrder\s+[IVXLC]+(?:\s+Rule\s+\d+)?)", re.I)
_ABBR = "".join(f"(?<!\\b{a}\\.)" for a in ("Rs", "No", "v", "vs", "Sec", "Art", "Dr", "Mr", "Mrs", "Sh", "Smt", "S", "Nos", "Ors", "Anr"))
_SENT = re.compile(r"(?<=[.!?।])" + _ABBR + r"\s+|\n+")


@dataclass
class SafetyFlag:
    code: str
    severity: str = "WARNING"
    detail: str = ""

    def as_dict(self):
        return {"code": self.code, "severity": self.severity, "detail": self.detail}


@dataclass
class SafetyResult:
    text: str
    flags: List[SafetyFlag] = field(default_factory=list)
    disclaimer: str = ""
    modified: bool = False

    @property
    def flag_codes(self) -> List[str]:
        return sorted({f.code for f in self.flags})


def _negated(sentence: str, m: "re.Match") -> bool:
    return bool(_NEG_BEFORE.search(sentence[: m.start()]) or _NEG_HI_AFTER.search(sentence[m.end():])
                or _NEG_HI_BEFORE.search(sentence[: m.start()]))


def _norm_spec(s: str) -> str:
    return re.sub(r"[\s.,]", "", s.lower())


class LegalSafetyService:
    def inspect(self, text: str, lang: str = "en", source_text: Optional[str] = None, add_disclaimer: bool = True) -> SafetyResult:
        """Return cleaned text + flags. `source_text` = concatenated retrieved passages (enables the unsupported-specifics check)."""
        l = "hi" if lang == "hi" else "en"
        flags: List[SafetyFlag] = []
        kept: List[str] = []
        src_norm = _norm_spec(source_text) if source_text is not None else None
        for sent in [s for s in _SENT.split(text or "") if s and s.strip()]:
            bad = self._violation(sent)
            if bad:
                flags.append(SafetyFlag(bad, "HIGH", "Sentence removed"))
                continue
            if src_norm is not None:
                unsupported = [m.group(0) for m in SPECIFIC.finditer(sent) if _norm_spec(m.group(0)) not in src_norm]
                if unsupported:
                    flags.append(SafetyFlag("UNSUPPORTED_SPECIFIC", "HIGH", f"Removed claim with unsourced specifics: {unsupported[0][:40]}"))
                    continue
            kept.append(sent.strip())
        out = "\n".join(kept) if "\n" in (text or "") else " ".join(kept)
        modified = bool(flags)
        if not out.strip():
            out = EMPTY_FALLBACK[l]
            modified = True
        disc = DISCLAIMER[l]
        if add_disclaimer and not DISCLAIMER_MARKERS.search(out):
            flags.append(SafetyFlag("DISCLAIMER_ADDED", "INFO"))
            out = f"{out}\n\n{disc}"
            modified = True
        return SafetyResult(text=out, flags=flags, disclaimer=disc, modified=modified)

    def inspect_items(self, items: Iterable[str], lang: str = "en", source_text: Optional[str] = None):
        """Clean short strings (steps, warnings). Returns list of (cleaned_or_None, flags)."""
        out = []
        for it in items:
            r = self.inspect(it, lang, source_text, add_disclaimer=False)
            blocked = any(f.severity == "HIGH" for f in r.flags) and r.text == EMPTY_FALLBACK["hi" if lang == "hi" else "en"]
            out.append((None if blocked else r.text, r.flags))
        return out

    @staticmethod
    def _violation(sentence: str) -> Optional[str]:
        for code, pats in _COMPILED.items():
            for p in pats:
                m = p.search(sentence)
                if m and not _negated(sentence, m):
                    return code
        return None
