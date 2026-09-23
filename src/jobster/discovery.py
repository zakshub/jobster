from __future__ import annotations

from collections.abc import Callable

from .dedupe import dedupe_jobs
from .models import Job
from .sources.base import JobSource


SourceErrorHandler = Callable[[str, Exception], None]


def discover(
    sources: list[JobSource],
    on_error: SourceErrorHandler | None = None,
) -> list[Job]:
    jobs: list[Job] = []
    for source in sources:
        try:
            jobs.extend(source.fetch())
        except Exception as exc:
            if on_error is not None:
                on_error(source.name, exc)
    return dedupe_jobs(jobs)
