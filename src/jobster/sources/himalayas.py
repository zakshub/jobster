from __future__ import annotations

import html
import re
import time

import httpx

from jobster.models import Job
from .base import JobSource


HIMALAYAS_SEARCH_API = "https://himalayas.app/jobs/api/search"


def _clean_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(value or "")).replace("  ", " ").strip()


def _monthly_salary(value: object, period: str | None) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    normalized = (period or "annual").lower()
    if normalized == "monthly":
        return float(value)
    if normalized == "annual":
        return float(value) / 12
    if normalized == "weekly":
        return float(value) * 52 / 12
    if normalized == "fortnightly":
        return float(value) * 26 / 12
    return None


def parse_himalayas(payload: dict) -> list[Job]:
    jobs: list[Job] = []
    for item in payload.get("jobs", []):
        if not isinstance(item, dict) or not item.get("title"):
            continue
        guid = str(
            item.get("guid")
            or item.get("applicationLink")
            or f"{item.get('companyName')}:{item.get('title')}"
        )
        restrictions = item.get("locationRestrictions") or []
        names = [
            str(x.get("name"))
            for x in restrictions
            if isinstance(x, dict) and x.get("name")
        ]
        location = ", ".join(names) if names else "Worldwide"
        period = str(item.get("salaryPeriod") or "annual")
        description = _clean_html(
            str(item.get("description") or item.get("excerpt") or "")
        )
        jobs.append(
            Job(
                id=f"himalayas:{guid}",
                title=str(item.get("title") or ""),
                company=str(item.get("companyName") or "Unknown company"),
                description=description,
                location=location,
                remote=True,
                source="himalayas",
                url=item.get("applicationLink"),
                salary_min_monthly=_monthly_salary(item.get("minSalary"), period),
                salary_max_monthly=_monthly_salary(item.get("maxSalary"), period),
                currency=item.get("currency"),
            )
        )
    return jobs


class HimalayasSource(JobSource):
    name = "himalayas"

    def __init__(
        self,
        queries: list[str],
        country: str | None = None,
        worldwide: bool | None = None,
        cache_hours: float = 24,
        timeout: float = 30.0,
    ):
        self.queries = queries
        self.country = country
        self.worldwide = worldwide
        self.cache_seconds = max(cache_hours, 0) * 3600
        self.timeout = timeout
        self._cached_at = 0.0
        self._cached_jobs: list[Job] = []

    def fetch(self) -> list[Job]:
        now = time.monotonic()
        if (
            self._cached_jobs
            and self.cache_seconds
            and now - self._cached_at < self.cache_seconds
        ):
            return list(self._cached_jobs)

        jobs: list[Job] = []
        seen: set[str] = set()
        for query in self.queries:
            params: dict[str, object] = {"q": query, "sort": "recent", "page": 1}
            if self.country:
                params["country"] = self.country
            if self.worldwide is not None:
                params["worldwide"] = str(self.worldwide).lower()

            response = httpx.get(
                HIMALAYAS_SEARCH_API,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

            for job in parse_himalayas(response.json()):
                key = job.url or job.id
                if key not in seen:
                    seen.add(key)
                    jobs.append(job)

        self._cached_jobs = jobs
        self._cached_at = now
        return list(jobs)
