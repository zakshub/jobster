from __future__ import annotations

import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

from .models import Job


def canonical_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def fingerprint(job: Job) -> str:
    url = canonical_url(job.url)
    if url:
        raw = f"url:{url}"
    else:
        norm = lambda value: re.sub(r"\s+", " ", value.lower()).strip()
        raw = f"job:{norm(job.company)}|{norm(job.title)}|{norm(job.location or '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dedupe_jobs(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    result: list[Job] = []
    for job in jobs:
        key = fingerprint(job)
        if key in seen:
            continue
        seen.add(key)
        result.append(job)
    return result
