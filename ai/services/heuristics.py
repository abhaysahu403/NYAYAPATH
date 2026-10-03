"""Deterministic (regex/keyword) extraction.

Roles: (1) offline fallback when the LLM fails or returns invalid output, (2) the Mock provider,
(3) authoritative cross-check for identifiers (CNR, state, case age) that an LLM must not hallucinate.
"""
import re
from typing import Dict, List, Optional

from ai.services import glossary
from ai.services.language import detect_language

CNR_RE = re.compile(r"\b([A-Z]{4}\d{12})\b", re.I)
CASE_NO_RE = re.compile(
    r"(?:case\s*(?:no\.?|number)|केस\s*(?:नंबर|संख्या)|वाद\s*संख्या|मुकदमा\s*संख्या|"
    r"\b(?:RCS|CS|CC|SA|FA|WP|CRA|CRR|MCC|MA|CRLA|RSA|OS)\b)\s*[:#\-]?\s*(?:No\.?)?\s*([A-Z]{0,6}\s?\d{1,6}\s*(?:/|of)\s*\d{2,4})",
    re.I)
NUM_WORDS = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "पाच": 5, "छह": 6, "छः": 6, "छै": 6, "सात": 7,
             "आठ": 8, "नौ": 9, "दस": 10, "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5,
             "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
             "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUM = r"(\d+(?:\.\d+)?|" + "|".join(sorted(map(re.escape, NUM_WORDS), key=len, reverse=True)) + r")"
AGE_RE = re.compile(_NUM + r"\s*(?:\+\s*)?(साल|वर्ष|सालों|saal|sal|years?|yrs?|mahine|महीने|months?)", re.I)
SIZE_RE = re.compile(_NUM + r"\s*(एकड़|एकड|acres?|bigha|बीघा|हेक्टेयर|hectares?|sq\.?\s*ft|square\s*feet|वर्ग\s*फुट|decimal|डिसमिल)", re.I)
EXISTING_YES = ["case chal", "केस चल", "मुकदमा चल", "case pending", "केस लंबित", "case filed", "केस दायर", "मुकदमा दायर", "सुनवाई", "hearing",
                "तारीख", "my case", "मेरा केस", "mera case", "court case", "case is pending", "केस पेंडिंग", "case 4", "pending hai", "chal raha"]
EXISTING_NO = ["no case", "not filed", "haven't filed", "have not filed", "want to file", "केस नहीं", "मुकदमा नहीं", "case nahi", "file karna", "दायर करना चाहता", "दायर करना चाहती"]


def _to_number(token: str) -> Optional[float]:
    token = token.strip().lower()
    if token in NUM_WORDS:
        return float(NUM_WORDS[token])
    try:
        return float(token)
    except ValueError:
        return None


def extract_case_age_years(text: str) -> Optional[float]:
    best = None
    for m in AGE_RE.finditer(text):
        n = _to_number(m.group(1))
        if n is None:
            continue
        unit = m.group(2).lower()
        years = n / 12 if unit in {"mahine", "महीने", "month", "months"} else n
        # only treat as case age when near case/pendency words
        window = text[max(0, m.start() - 60): m.end() + 60].lower()
        if any(w in window for w in ["case", "केस", "मुकदमा", "pending", "चल रहा", "चल रहा है", "chal", "लंबित", "court", "कोर्ट"]):
            best = years if best is None else max(best, years)
    return round(best, 2) if best is not None else None


def extract_state(text: str) -> Optional[str]:
    low = f" {text.lower()} "
    for state, aliases in glossary.STATES.items():
        if any((a if a.endswith(" ") else a) in low for a in aliases if len(a) > 3 or a.endswith(" ")):
            return state
    return None


def extract_district(text: str):
    low = text.lower()
    for key, (district, state) in glossary.DISTRICTS.items():
        if re.search(rf"(?<![\w]){re.escape(key)}(?![\w])", low):
            return district, state
    return None, None


def extract_documents(text: str) -> List[str]:
    low = text.lower()
    return [name for name, keys in glossary.DOCUMENT_HINTS.items() if any(k.lower() in low for k in keys)]


def classify_topic(text: str) -> str:
    low = text.lower()
    scores: Dict[str, int] = {}
    for topic, hints in glossary.TOPIC_HINTS:
        scores[topic] = sum(1 for h in hints if h in low)
    land, prop, pend = scores.get("LAND_DISPUTE", 0), scores.get("PROPERTY_DISPUTE", 0), scores.get("CASE_PENDENCY", 0)
    if land or prop:
        return "LAND_DISPUTE" if land >= prop else "PROPERTY_DISPUTE"
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else "OTHER"


def expand_keywords(text: str) -> List[str]:
    low = text.lower()
    out: List[str] = []
    for term in sorted(glossary.TERM_MAP, key=len, reverse=True):
        if term in low:
            for w in glossary.TERM_MAP[term]:
                if w not in out:
                    out.append(w)
    return out[:12]


def analyse(text: str) -> dict:
    """Return a dict compatible with ai.schemas.IntakeResult."""
    text = text or ""
    district, d_state = extract_district(text)
    state = extract_state(text) or d_state
    low = text.lower()
    flags = []
    if any(w in low for w in ["कब्ज", "kabza", "kabja", "possession", "encroach", "अतिक्रमण", "dispossess"]):
        flags.append("POSSESSION_ISSUE")
    age = extract_case_age_years(text)
    if age is not None and age >= 1 or any(w in low for w in ["pending", "लंबित", "आगे नहीं", "तारीख पर तारीख", "date pe date", "delay", "not moving"]):
        flags.append("PENDENCY_ISSUE")
    if any(w in low for w in ["khasra", "खसरा", "khatauni", "खतौनी", "खतोनी", "mutation", "नामांतरण", "revenue record", "jamabandi"]):
        flags.append("REVENUE_RECORD_ISSUE")
    existing = None
    if any(k in low for k in EXISTING_NO):
        existing = False
    elif any(k in low for k in EXISTING_YES) or age is not None:
        existing = True
    cnr = CNR_RE.search(text)
    cn = CASE_NO_RE.search(text)
    size = SIZE_RE.search(text)
    topic = classify_topic(text)
    keywords = expand_keywords(text)
    urgency = "HIGH" if "POSSESSION_ISSUE" in flags or topic in {"BAIL", "CRIMINAL_CASE"} else "MEDIUM"
    return {
        "language": detect_language(text), "legal_topic": topic, "state": state, "district": district,
        "cnr": cnr.group(1).upper() if cnr else None, "case_number": cn.group(1).strip() if cn else None,
        "existing_case": existing, "case_age_years": age, "documents": extract_documents(text),
        "property_size": f"{size.group(1)} {size.group(2)}" if size else None,
        "issue_flags": flags, "search_keywords": keywords, "urgency": urgency,
        "key_issues": [], "problem_summary_en": None, "problem_summary_hi": None,
    }
