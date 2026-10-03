"""Script-based language detection for Hindi / English / Hinglish (no LLM call needed)."""
import re

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_LATIN = re.compile(r"[A-Za-z]")
_WORD = re.compile(r"[a-zA-Z]+")

# Common romanised-Hindi words that rarely occur in English legal text.
HINGLISH_MARKERS = {
    "mera", "meri", "mere", "hai", "hain", "hu", "hoon", "tha", "thi", "nahi", "nahin", "kya", "kaise", "kyun", "kab",
    "saal", "sal", "mahine", "din", "zameen", "jameen", "zamin", "jagah", "kabza", "kabja", "padosi", "pados", "case",
    "chal", "raha", "rahi", "rahe", "karna", "kare", "karo", "kar", "diya", "liya", "gaya", "gayi", "ka", "ki", "ke",
    "ko", "se", "par", "pe", "mein", "me", "aur", "ya", "lekin", "abhi", "ab", "mujhe", "humein", "hamara", "uska",
    "unka", "wala", "wali", "samajh", "madad", "batao", "bataye", "kisan", "khet", "vakil", "adalat", "tareekh",
    "tarikh", "pending", "aage", "badh", "bhai", "sarkar", "dhokha", "paisa", "paise", "fir", "thana", "khasra",
    "khatauni", "patwari", "tehsildar", "bijli", "makaan", "makan", "dukan",
}


def detect_language(text: str) -> str:
    """Return 'hi' (Devanagari), 'hinglish' (romanised Hindi / mixed), or 'en'."""
    text = text or ""
    dev = len(_DEVANAGARI.findall(text))
    lat = len(_LATIN.findall(text))
    total = dev + lat
    if total == 0:
        return "en"
    if dev / total >= 0.5:
        return "hi"
    words = [w.lower() for w in _WORD.findall(text)]
    if dev > 0 and lat > 0:
        return "hinglish"
    if not words:
        return "en"
    hits = sum(1 for w in words if w in HINGLISH_MARKERS)
    strong = {"mera", "meri", "mere", "hai", "hain", "nahi", "saal", "zameen", "jameen", "kabza", "kabja", "padosi", "mujhe", "kya", "raha", "rahi"}
    if hits / len(words) >= 0.2 or any(w in strong for w in words) and hits >= 2:
        return "hinglish"
    return "en"


def response_language(requested, detected, preferred=None) -> str:
    """Pick output language: explicit request > detected Hindi/Hinglish > user preference > English."""
    if requested in {"hi", "en"}:
        return requested
    if detected in {"hi", "hinglish"}:
        return "hi"
    return preferred if preferred in {"hi", "en"} else "en"
