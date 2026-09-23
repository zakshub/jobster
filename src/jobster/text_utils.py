from __future__ import annotations


_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ð", "Ø", "Ù")


def repair_text(value: object) -> str:
    text = str(value or "")
    if not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
        return repaired if repaired else text
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
