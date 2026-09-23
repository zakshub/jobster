from __future__ import annotations

import html

import httpx

from jobster.models import Job
from .base import JobSource


REMOTE_OK_API = "https://remoteok.com/api"


def parse_remoteok(payload: list[dict]) -> list[Job]:
    jobs: list[Job] = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("id") or not item.get("position"):
            continue
        description = html.unescape(str(item.get("description") or ""))
        location = str(item.get("location") or "Remote")
        jobs.append(
            Job(
                id=f"remoteok:{item['id']}",
                title=str(item.get("position") or ""),
                company=str(item.get("company") or "Unknown company"),
                description=description,
                location=location,
                remote=True,
                source="remoteok",
                url=item.get("url") or item.get("apply_url"),
            )
        )
    return jobs


class RemoteOkSource(JobSource):
    name = "remoteok"

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        headers = {"User-Agent": "JobsterPersonalCareerAgent/0.1"}
        response = httpx.get(REMOTE_OK_API, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return parse_remoteok(response.json())
