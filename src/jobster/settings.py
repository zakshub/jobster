from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .sources.source_registry import WEB_SEARCH_DOMAINS


DEFAULT_ROLE_QUERIES = [
    "Senior Product Designer",
    "UX Architect",
    "Product Designer",
    "UX Engineer",
    "AI Product Designer",
]

DEFAULT_WEB_QUERY = (
    '"Senior Product Designer" OR "UX Architect" OR "Product Designer" '
    'OR "UX Engineer" OR "AI Product Designer" remote'
)


class SourceToggle(BaseModel):
    enabled: bool = True


class GoogleJobsConfig(SourceToggle):
    query: str = "remote product designer"
    location: str | None = None


class HimalayasConfig(SourceToggle):
    queries: list[str] = Field(default_factory=lambda: list(DEFAULT_ROLE_QUERIES))
    country: str | None = None
    worldwide: bool | None = None
    cache_hours: float = Field(default=24, ge=1, le=168)


class WebSearchConfig(SourceToggle):
    query: str = DEFAULT_WEB_QUERY
    sites: list[str] = Field(default_factory=lambda: list(WEB_SEARCH_DOMAINS))
    group_size: int = Field(default=6, ge=1, le=10)
    results_per_group: int = Field(default=10, ge=1, le=20)
    cache_hours: float = Field(default=6, ge=1, le=168)


class SourcesConfig(BaseModel):
    remoteok: SourceToggle = Field(default_factory=SourceToggle)
    remotive: SourceToggle = Field(default_factory=SourceToggle)
    weworkremotely: SourceToggle = Field(default_factory=SourceToggle)
    himalayas: HimalayasConfig = Field(default_factory=HimalayasConfig)
    google_jobs: GoogleJobsConfig = Field(
        default_factory=lambda: GoogleJobsConfig(enabled=False)
    )
    web_search: WebSearchConfig = Field(
        default_factory=lambda: WebSearchConfig(enabled=False)
    )


class ApplicationConfig(BaseModel):
    auto_submit: bool = False
    semantic_reasoning: bool = True
    answer_bank_path: str = "private_data/answer_bank.yaml"
    max_submissions_per_cycle: int = Field(default=5, ge=0, le=25)


class SearchConfig(BaseModel):
    cycle_minutes: int = Field(default=60, ge=15)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)


def load_search_config(path: str | Path) -> SearchConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return SearchConfig.model_validate(data)
