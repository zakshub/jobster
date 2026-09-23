from __future__ import annotations

from .dedupe import dedupe_jobs
from .models import Job
from .sources.base import JobSource


def discover(sources: list[JobSource]) -> list[Job]:
    jobs: list[Job] = []
    for source in sources:
        jobs.extend(source.fetch())
    return dedupe_jobs(jobs)
