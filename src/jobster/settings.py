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
    cache_hours: float = Field(default=24, ge=1, le=168)


class IntakeConfig(BaseModel):
    enabled: bool = True
    min_title_score: int = Field(default=70, ge=0, le=100)
    max_per_source: int = Field(default=12, ge=1, le=100)
    max_total: int = Field(default=60, ge=1, le=500)


class SerpApiBudgetConfig(BaseModel):
    monthly_limit: int = Field(default=250, ge=1)
    reserve_queries: int = Field(default=25, ge=0)
    daily_limit: int = Field(default=7, ge=1)
    window_days: int = Field(default=30, ge=1)
    state_path: str = "data/serpapi_quota.json"


class SubmissionScheduleConfig(BaseModel):
    enabled: bool = True
    timezone: str = "Asia/Karachi"
    friday_stop_time: str = Field(default="18:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    monday_resume_time: str = Field(default="09:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")


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
    resume_path: str | None = None
    browser_profile_path: str = "private_data/browser_profile"
    gmail_client_secret_path: str = "private_data/gmail_client_secret.json"
    gmail_token_path: str = "private_data/gmail_token.json"
    max_submissions_per_cycle: int = Field(default=5, ge=0, le=25)
    submission_schedule: SubmissionScheduleConfig = Field(
        default_factory=SubmissionScheduleConfig
    )


class SearchConfig(BaseModel):
    cycle_minutes: int = Field(default=60, ge=15)
    intake: IntakeConfig = Field(default_factory=IntakeConfig)
    serpapi_budget: SerpApiBudgetConfig = Field(default_factory=SerpApiBudgetConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)


def load_search_config(path: str | Path) -> SearchConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return SearchConfig.model_validate(data)
