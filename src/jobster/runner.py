from __future__ import annotations

from .discovery import discover
from .models import CareerProfile, PursuitDecision
from .pipeline import evaluate_and_store
from .settings import SearchConfig
from .sources import RemoteOkSource, RemotiveSource, SerpApiGoogleJobsSource, WeWorkRemotelySource
from .storage import JobsterStore


def build_sources(config: SearchConfig):
    sources = []
    if config.sources.remoteok.enabled:
        sources.append(RemoteOkSource())
    if config.sources.remotive.enabled:
        sources.append(RemotiveSource())
    if config.sources.weworkremotely.enabled:
        sources.append(WeWorkRemotelySource())
    if config.sources.google_jobs.enabled:
        sources.append(
            SerpApiGoogleJobsSource(
                query=config.sources.google_jobs.query,
                location=config.sources.google_jobs.location,
            )
        )
    return sources


def run_cycle(profile: CareerProfile, config: SearchConfig, store: JobsterStore) -> dict:
    sources = build_sources(config)
    jobs = discover(sources)
    evaluations = evaluate_and_store(profile, jobs, store)

    counts = {decision.value: 0 for decision in PursuitDecision}
    for evaluation in evaluations:
        counts[evaluation.pursuit_decision.value] += 1

    summary = {
        "discovered": len(jobs),
        "evaluated": len(evaluations),
        "decisions": counts,
    }
    store.audit("discovery_cycle_completed", summary)
    return summary
