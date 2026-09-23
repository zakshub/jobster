from __future__ import annotations

from urllib.parse import urlparse


def detect_ats(url: str | None) -> str:
    if not url:
        return "unknown"
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    if "greenhouse.io" in host or "boards.greenhouse" in host:
        return "greenhouse"
    if "lever.co" in host or "jobs.lever" in host:
        return "lever"
    if "ashbyhq.com" in host or "jobs.ashby" in host:
        return "ashby"
    if "myworkdayjobs.com" in host or "workday" in host:
        return "workday"
    if "linkedin.com" in host:
        return "linkedin"
    if any(token in path for token in ("/careers", "/career", "/jobs", "/job/")):
        return "generic_careers"
    return "unknown"
