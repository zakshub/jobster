from __future__ import annotations

import os

import httpx

from jobster.models import Job
from .base import JobSource


SERPAPI_ENDPOINT = "https://serpapi.com/search"


def parse_google_jobs(payload: dict) -> list[Job]:
    jobs: list[Job] = []
    for item in payload.get("jobs_results", []):
        job_id = item.get("job_id") or item.get("share_link") or f"{item.get('company_name')}:{item.get('title')}"
        detected_extensions = item.get("detected_extensions") or {}
        location = str(item.get("location") or "")
        remote = bool(detected_extensions.get("work_from_home")) or "remote" in location.lower()

        apply_options = item.get("apply_options") or []
        url = None
        if apply_options and isinstance(apply_options[0], dict):
            url = apply_options[0].get("link")
        url = url or item.get("share_link")

        jobs.append(
            Job(
                id=f"google_jobs:{job_id}",
                title=str(item.get("title") or ""),
                company=str(item.get("company_name") or "Unknown company"),
                description=str(item.get("description") or ""),
                location=location or None,
                remote=remote if location or detected_extensions else None,
                source="google_jobs",
                url=url,
            )
        )
    return jobs


class SerpApiGoogleJobsSource(JobSource):
    name = "google_jobs"

    def __init__(self, query: str, location: str | None = None, api_key: str | None = None, timeout: float = 30.0):
        self.query = query
        self.location = location
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        if not self.api_key:
            raise RuntimeError("SERPAPI_API_KEY is required for Google Jobs discovery")
        params = {"engine": "google_jobs", "q": self.query, "api_key": self.api_key}
        if self.location:
            params["location"] = self.location
        response = httpx.get(SERPAPI_ENDPOINT, params=params, timeout=self.timeout)
        response.raise_for_status()
        return parse_google_jobs(response.json())
