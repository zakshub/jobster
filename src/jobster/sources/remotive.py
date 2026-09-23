from __future__ import annotations

import html

import httpx

from jobster.models import Job
from .base import JobSource


REMOTIVE_API = "https://remotive.com/api/remote-jobs"


def parse_remotive(payload: dict) -> list[Job]:
    jobs: list[Job] = []
    for item in payload.get("jobs", []):
        if not item.get("id") or not item.get("title"):
            continue
        jobs.append(
            Job(
                id=f"remotive:{item['id']}",
                title=str(item.get("title") or ""),
                company=str(item.get("company_name") or "Unknown company"),
                description=html.unescape(str(item.get("description") or "")),
                location=str(item.get("candidate_required_location") or "Remote"),
                remote=True,
                source="remotive",
                url=item.get("url"),
            )
        )
    return jobs


class RemotiveSource(JobSource):
    name = "remotive"

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        response = httpx.get(REMOTIVE_API, timeout=self.timeout)
        response.raise_for_status()
        return parse_remotive(response.json())
