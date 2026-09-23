from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SourceToggle(BaseModel):
    enabled: bool = True


class GoogleJobsConfig(SourceToggle):
    query: str = "remote product designer"
    location: str | None = None


class SourcesConfig(BaseModel):
    remoteok: SourceToggle = Field(default_factory=SourceToggle)
    remotive: SourceToggle = Field(default_factory=SourceToggle)
    weworkremotely: SourceToggle = Field(default_factory=SourceToggle)
    google_jobs: GoogleJobsConfig = Field(default_factory=lambda: GoogleJobsConfig(enabled=False))


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
