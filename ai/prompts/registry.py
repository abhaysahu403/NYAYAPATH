"""Versioned prompt files: ai/prompts/<category>/<name>_v<N>.txt (string.Template, $vars)."""
import re
from functools import lru_cache
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parent
_VER = re.compile(r"^(?P<name>.+)_v(?P<ver>\d+)$")


@lru_cache(maxsize=None)
def _latest(category: str, name: str) -> str:
    best, best_v = None, -1
    for f in (PROMPT_DIR / category).glob(f"{name}_v*.txt"):
        m = _VER.match(f.stem)
        if m and m.group("name") == name and int(m.group("ver")) > best_v:
            best, best_v = f.stem, int(m.group("ver"))
    if best is None:
        raise FileNotFoundError(f"No prompt '{category}/{name}'")
    return best


@lru_cache(maxsize=None)
def _read(category: str, stem: str) -> str:
    return (PROMPT_DIR / category / f"{stem}.txt").read_text(encoding="utf-8")


def render(ref: str, **variables):
    """ref = 'category/name' (latest version) or 'category/name_v2' (pinned). Returns (text, version_id)."""
    category, name = ref.split("/", 1)
    stem = name if _VER.match(name) else _latest(category, name)
    variables.setdefault("legal_rules", _read("safety", _latest("safety", "legal_rules")))
    return Template(_read(category, stem)).safe_substitute(**variables), f"{category}/{stem}"
