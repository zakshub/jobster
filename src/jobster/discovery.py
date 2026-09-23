from __future__ import annotations

from collections.abc import Callable

from .dedupe import dedupe_jobs
from .models import Job
from .sources.base import JobSource


SourceErrorHandler = Callable[[str, Exception], None]
DiscoveryEventHandler = Callable[[str, dict], None]


def discover(
    sources: list[JobSource],
    on_error: SourceErrorHandler | None = None,
    on_event: DiscoveryEventHandler | None = None,
) -> list[Job]:
    jobs: list[Job] = []
    for source in sources:
        if on_event is not None:
            on_event("source_started", {"source": source.name})
        try:
            fetched = source.fetch()
            jobs.extend(fetched)
            if on_event is not None:
                on_event(
                    "source_completed",
                    {"source": source.name, "fetched": len(fetched)},
                )
        except Exception as exc:
            if on_error is not None:
                on_error(source.name, exc)
            if on_event is not None:
                on_event(
                    "source_failed",
                    {"source": source.name, "error": str(exc)},
                )
    deduped = dedupe_jobs(jobs)
    if on_event is not None:
        on_event(
            "discovery_completed",
            {"raw": len(jobs), "deduped": len(deduped)},
        )
    return deduped
