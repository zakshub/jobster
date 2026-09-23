from __future__ import annotations

from .brain import CareerBrain
from .discovery import discover
from .models import CareerProfile, PursuitDecision
from .orchestrator import process_applications
from .semantic import SemanticCareerBrain
from .settings import SearchConfig
from .sources import (
    HimalayasSource,
    JobSource,
    RemoteOkSource,
    RemotiveSource,
    SerpApiGoogleJobsSource,
    SerpApiWebSearchSource,
    WeWorkRemotelySource,
)
from .storage import JobsterStore


def build_sources(config: SearchConfig) -> list[JobSource]:
    sources: list[JobSource] = []

    if config.sources.remoteok.enabled:
        sources.append(RemoteOkSource())

    if config.sources.remotive.enabled:
        sources.append(RemotiveSource())

    if config.sources.weworkremotely.enabled:
        sources.append(WeWorkRemotelySource())

    if config.sources.himalayas.enabled:
        sources.append(
            HimalayasSource(
                queries=config.sources.himalayas.queries,
                country=config.sources.himalayas.country,
                worldwide=config.sources.himalayas.worldwide,
                cache_hours=config.sources.himalayas.cache_hours,
            )
        )

    if config.sources.google_jobs.enabled:
        sources.append(
            SerpApiGoogleJobsSource(
                query=config.sources.google_jobs.query,
                location=config.sources.google_jobs.location,
            )
        )

    if config.sources.web_search.enabled:
        sources.append(
            SerpApiWebSearchSource(
                query=config.sources.web_search.query,
                sites=config.sources.web_search.sites,
                group_size=config.sources.web_search.group_size,
                results_per_group=config.sources.web_search.results_per_group,
                cache_hours=config.sources.web_search.cache_hours,
            )
        )

    return sources


def run_cycle(
    profile: CareerProfile,
    config: SearchConfig,
    store: JobsterStore,
    sources: list[JobSource] | None = None,
) -> dict:
    active_sources = sources if sources is not None else build_sources(config)

    def record_source_error(source_name: str, exc: Exception) -> None:
        store.audit(
            "source_failed",
            {"source": source_name, "error": str(exc)},
        )

    jobs = discover(active_sources, on_error=record_source_error)
    baseline_brain = CareerBrain()
    semantic_brain = SemanticCareerBrain()

    evaluations = []
    for job in jobs:
        store.save_job(job)
        baseline = baseline_brain.evaluate(profile, job)
        evaluation = (
            semantic_brain.evaluate(profile, job, baseline)
            if config.application.semantic_reasoning and baseline.eligible
            else baseline
        )
        store.save_evaluation(evaluation)
        store.audit(
            "job_evaluated",
            {
                "decision": evaluation.pursuit_decision.value,
                "confidence": evaluation.confidence,
                "eligible": evaluation.eligible,
                "source": job.source,
            },
            job_id=job.id,
        )
        evaluations.append(evaluation)

    counts = {decision.value: 0 for decision in PursuitDecision}
    for evaluation in evaluations:
        counts[evaluation.pursuit_decision.value] += 1

    applications = process_applications(jobs, evaluations, config, store)

    summary = {
        "discovered": len(jobs),
        "evaluated": len(evaluations),
        "sources": [source.name for source in active_sources],
        "decisions": counts,
        "applications": applications,
    }
    store.audit("discovery_cycle_completed", summary)
    return summary
