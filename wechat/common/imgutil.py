from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

try:
    import imghdr as _imghdr
except ModuleNotFoundError:  # Python 3.13+
    _imghdr = None


def what(file: str | Path | None = None, h: bytes | None = None) -> str | None:
    """
    Compatibility wrapper for the removed stdlib `imghdr` module (Python 3.13+).

    Behaves like `imghdr.what(file, h)` and returns a lowercase format string
    like "jpeg", "png", "gif", or None if unknown.
    """
    if _imghdr is not None:
        return _imghdr.what(file, h)
    if h is not None:
        return _what_from_bytes(h)
    if file is None:
        return None
    try:
        with Image.open(str(file)) as im:
            fmt = im.format
    except Exception:
        return None
    return fmt.lower() if fmt else None


def _what_from_bytes(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith(b"II*\x00") or data.startswith(b"MM\x00*"):
        return "tiff"
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt = im.format
    except Exception:
        return None
    return fmt.lower() if fmt else None

