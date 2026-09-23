from __future__ import annotations

import hashlib
import os
import time
from urllib.parse import urlparse

import httpx

from jobster.models import Job
from .base import JobSource
from .source_registry import SOURCE_REGISTRY


SERPAPI_ENDPOINT = "https://serpapi.com/search"

_DOMAIN_TO_SOURCE = {
    item.domain.split("/", 1)[0].lower(): item.key
    for item in SOURCE_REGISTRY
    if item.method in {"web_search", "ats_web_search"}
}


def _source_for_url(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for domain, key in _DOMAIN_TO_SOURCE.items():
        if host == domain or host.endswith("." + domain):
            return key
    return "web_search"


def _title_and_company(raw_title: str, source: str) -> tuple[str, str]:
    title = raw_title.strip()
    for suffix in (
        " | LinkedIn",
        " - LinkedIn",
        " | Wellfound",
        " | Glassdoor",
        " | Indeed",
    ):
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()

    parts = [part.strip() for part in title.split(" - ") if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]

    parts = [part.strip() for part in title.split(" at ") if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]

    return title, source.replace("_", " ").title()


def parse_serpapi_web(payload: dict) -> list[Job]:
    jobs: list[Job] = []
    for item in payload.get("organic_results", []):
        if not isinstance(item, dict):
            continue
        link = str(item.get("link") or "").strip()
        raw_title = str(item.get("title") or "").strip()
        if not link or not raw_title:
            continue

        source = _source_for_url(link)
        title, company = _title_and_company(raw_title, source)
        snippet = str(item.get("snippet") or "")
        haystack = f"{raw_title} {snippet}".lower()
        remote = True if "remote" in haystack or "worldwide" in haystack else None
        stable = hashlib.sha1(link.encode("utf-8")).hexdigest()[:20]

        jobs.append(
            Job(
                id=f"{source}:{stable}",
                title=title,
                company=company,
                description=snippet,
                location="Remote" if remote else None,
                remote=remote,
                source=source,
                url=link,
            )
        )
    return jobs


class SerpApiWebSearchSource(JobSource):
    name = "web_search"

    def __init__(
        self,
        query: str,
        sites: list[str],
        api_key: str | None = None,
        group_size: int = 6,
        results_per_group: int = 10,
        cache_hours: float = 6,
        timeout: float = 30.0,
    ):
        self.query = query
        self.sites = sites
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.group_size = max(1, group_size)
        self.results_per_group = max(1, min(results_per_group, 20))
        self.cache_seconds = max(cache_hours, 0) * 3600
        self.timeout = timeout
        self._cached_at = 0.0
        self._cached_jobs: list[Job] = []

    def fetch(self) -> list[Job]:
        if not self.api_key:
            raise RuntimeError(
                "SERPAPI_API_KEY is required for expanded web-source discovery"
            )

        now = time.monotonic()
        if (
            self._cached_jobs
            and self.cache_seconds
            and now - self._cached_at < self.cache_seconds
        ):
            return list(self._cached_jobs)

        jobs: list[Job] = []
        seen: set[str] = set()

        for start in range(0, len(self.sites), self.group_size):
            group = self.sites[start : start + self.group_size]
            site_filter = " OR ".join(f"site:{site}" for site in group)
            q = f"({self.query}) ({site_filter})"

            response = httpx.get(
                SERPAPI_ENDPOINT,
                params={
                    "engine": "google",
                    "q": q,
                    "num": self.results_per_group,
                    "api_key": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            for job in parse_serpapi_web(response.json()):
                key = job.url or job.id
                if key not in seen:
                    seen.add(key)
                    jobs.append(job)

        self._cached_jobs = jobs
        self._cached_at = now
        return list(jobs)
