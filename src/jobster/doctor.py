from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .settings import load_search_config


def doctor(
    profile_path: str | Path = "config/profile.yaml",
    search_path: str | Path = "config/search.yaml",
    db_path: str | Path = "data/jobster.db",
) -> list[dict]:
    checks = []

    profile = Path(profile_path)
    search = Path(search_path)
    db = Path(db_path)

    checks.append({"name": "profile", "ok": profile.exists(), "detail": str(profile)})
    checks.append({"name": "search_config", "ok": search.exists(), "detail": str(search)})
    checks.append(
        {
            "name": "db_directory",
            "ok": db.parent.exists() or db.parent == Path("."),
            "detail": str(db.parent),
        }
    )
    checks.append(
        {
            "name": "playwright_python",
            "ok": importlib.util.find_spec("playwright") is not None,
            "detail": "Python package",
        }
    )
    checks.append(
        {
            "name": "openai_semantic_key",
            "ok": bool(os.getenv("OPENAI_API_KEY")),
            "detail": "Optional but required for semantic CareerBrain",
        }
    )

    if search.exists():
        config = load_search_config(search)
        if config.sources.google_jobs.enabled or config.sources.web_search.enabled:
            checks.append(
                {
                    "name": "serpapi_key",
                    "ok": bool(os.getenv("SERPAPI_API_KEY")),
                    "detail": (
                        "Required because Google Jobs or expanded web search is enabled"
                    ),
                }
            )

    return checks
