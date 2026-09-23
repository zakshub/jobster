from __future__ import annotations

import re


def normalize_question(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
