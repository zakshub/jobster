from __future__ import annotations

from pathlib import Path

import yaml

from .application_policy import normalize_question
from .models import ApplicationAnswer


def load_answer_bank(path: str | Path) -> list[ApplicationAnswer]:
    path = Path(path)
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = raw.get("answers", raw if isinstance(raw, list) else [])
    return [ApplicationAnswer.model_validate(item) for item in items]


def answer_lookup(answers: list[ApplicationAnswer]) -> dict[str, ApplicationAnswer]:
    lookup: dict[str, ApplicationAnswer] = {}
    for answer in answers:
        keys = [answer.key, *answer.aliases]
        for key in keys:
            lookup[normalize_question(key)] = answer
    return lookup
