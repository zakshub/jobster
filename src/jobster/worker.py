from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .profile import load_profile
from .runner import run_cycle
from .settings import load_search_config
from .storage import JobsterStore


def main():
    profile_path = Path(os.getenv("JOBSTER_PROFILE", "config/profile.yaml"))
    search_path = Path(os.getenv("JOBSTER_SEARCH", "config/search.yaml"))
    db_path = Path(os.getenv("JOBSTER_DB", "data/jobster.db"))

    profile = load_profile(profile_path)
    config = load_search_config(search_path)
    store = JobsterStore(db_path)
    store.init()

    while True:
        try:
            summary = run_cycle(profile, config, store)
            print(json.dumps({"event": "cycle_completed", **summary}, sort_keys=True), flush=True)
        except Exception as exc:
            store.audit("cycle_failed", {"error": str(exc)})
            print(json.dumps({"event": "cycle_failed", "error": str(exc)}), flush=True)
        time.sleep(config.cycle_minutes * 60)


if __name__ == "__main__":
    main()
