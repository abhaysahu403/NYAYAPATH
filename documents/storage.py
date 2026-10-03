"""Private file storage. Files live under PRIVATE_MEDIA_ROOT (never served by Django static/media).

They are reachable only through ownership-checked API views or short-lived signed download links.
`Document.file_path` stores a path RELATIVE to PRIVATE_MEDIA_ROOT, so the store can be moved or swapped for
S3-compatible storage without touching database rows.
"""
import os
import uuid
from pathlib import Path
from typing import Tuple

from django.conf import settings


def _root() -> Path:
    root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def absolute_path(relative_path: str) -> Path:
    """Resolve a stored relative path, refusing anything that escapes the private root."""
    root = _root()
    p = (root / relative_path).resolve()
    if root not in p.parents and p != root:
        raise ValueError("Invalid storage path")
    return p


def save_upload(file, owner_id: str) -> Tuple[str, str]:
    """Save an uploaded file. Returns (stored_filename, relative_path). Original filename is never used on disk."""
    ext = Path(file.name).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    rel = f"documents/{owner_id}/{stored_name}"
    dest = absolute_path(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as fh:
        for chunk in file.chunks():
            fh.write(chunk)
    os.chmod(dest, 0o600)
    return stored_name, rel


def delete_file(relative_path: str) -> None:
    try:
        if relative_path:
            p = absolute_path(relative_path)
            if p.exists():
                p.unlink()
    except (OSError, ValueError):
        pass


def file_exists(relative_path: str) -> bool:
    try:
        return bool(relative_path) and absolute_path(relative_path).exists()
    except ValueError:
        return False
