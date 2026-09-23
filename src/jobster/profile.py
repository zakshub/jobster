from pathlib import Path

import yaml

from .models import CareerProfile


def load_profile(path: str | Path) -> CareerProfile:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return CareerProfile.model_validate(data)
