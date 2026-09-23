from __future__ import annotations

from collections import Counter
from collections.abc import Callable

from .brain import CareerBrain
from .discovery import discover
from .models import CareerProfile, PursuitDecision
from .orchestrator import process_applications
from .quota import SerpApiQuota
from .relevance import select_relevant_jobs
from .semantic import SemanticCareerBrain, friendly_semantic_error
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


RunEventHandler = Callable[[str, dict], None]


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

    quota = None
    if config.sources.google_jobs.enabled or config.sources.web_search.enabled:
        budget = config.serpapi_budget
        quota = SerpApiQuota(
            path=budget.state_path,
            monthly_limit=budget.monthly_limit,
            reserve_queries=budget.reserve_queries,
            daily_limit=budget.daily_limit,
            window_days=budget.window_days,
        )

    if config.sources.google_jobs.enabled:
        sources.append(
            SerpApiGoogleJobsSource(
                query=config.sources.google_jobs.query,
                location=config.sources.google_jobs.location,
                quota=quota,
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
                quota=quota,
            )
        )

    return sources


def run_cycle(
    profile: CareerProfile,
    config: SearchConfig,
    store: JobsterStore,
    sources: list[JobSource] | None = None,
    on_event: RunEventHandler | None = None,
) -> dict:
    active_sources = sources if sources is not None else build_sources(config)

    def emit(event: str, payload: dict) -> None:
        if on_event is not None:
            on_event(event, payload)

    def record_source_error(source_name: str, exc: Exception) -> None:
        store.audit(
            "source_failed",
            {"source": source_name, "error": str(exc)},
        )

    emit(
        "cycle_started",
        {
            "sources": [source.name for source in active_sources],
            "target_titles": profile.target_titles,
        },
    )

    discovered = discover(
        active_sources,
        on_error=record_source_error,
        on_event=emit,
    )
    raw_by_source = dict(Counter(job.source for job in discovered))

    if config.intake.enabled:
        jobs, rejected = select_relevant_jobs(
            profile,
            discovered,
            min_score=config.intake.min_title_score,
            max_per_source=config.intake.max_per_source,
            max_total=config.intake.max_total,
        )
    else:
        jobs, rejected = discovered, []

    admitted_by_source = dict(Counter(job.source for job in jobs))
    rejection_reasons = Counter(result.reason for _, result in rejected)
    emit(
        "intake_completed",
        {
            "raw": len(discovered),
            "admitted": len(jobs),
            "rejected": len(rejected),
            "raw_by_source": raw_by_source,
            "admitted_by_source": admitted_by_source,
            "top_rejection_reasons": dict(rejection_reasons.most_common(6)),
        },
    )

    baseline_brain = CareerBrain()
    semantic_brain = SemanticCareerBrain()

    evaluations = []
    total = len(jobs)
    semantic_enabled = bool(config.application.semantic_reasoning and semantic_brain.available)
    semantic_pause: dict | None = None
    for index, job in enumerate(jobs, start=1):
        emit(
            "evaluation_started",
            {
                "index": index,
                "total": total,
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "source": job.source,
            },
        )
        store.save_job(job)
        baseline = baseline_brain.evaluate(profile, job)
        review_mode = "basic"
        evaluation = baseline
        if semantic_enabled and baseline.eligible:
            try:
                evaluation = semantic_brain.evaluate(profile, job, baseline)
                review_mode = "ai"
            except Exception as exc:
                semantic_pause = friendly_semantic_error(exc)
                semantic_enabled = False
                store.audit(
                    "ai_review_paused",
                    {
                        "reason": semantic_pause["message"],
                        "kind": semantic_pause["kind"],
                        "code": semantic_pause.get("code"),
                    },
                    job_id=job.id,
                )
                emit(
                    "ai_review_paused",
                    {
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "reason": semantic_pause["message"],
                        "kind": semantic_pause["kind"],
                    },
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
        emit(
            "evaluation_completed",
            {
                "index": index,
                "total": total,
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "decision": evaluation.pursuit_decision.value,
                "interest_score": evaluation.interest_score,
                "review_mode": review_mode,
            },
        )

    counts = {decision.value: 0 for decision in PursuitDecision}
    for evaluation in evaluations:
        counts[evaluation.pursuit_decision.value] += 1

    emit(
        "application_preflight_started",
        {"candidates": sum(counts[key] for key in ("apply", "high_priority", "aggressive_pursuit"))},
    )
    applications = process_applications(jobs, evaluations, config, store)

    summary = {
        "raw_discovered": len(discovered),
        "discovered": len(jobs),
        "rejected_irrelevant": len(rejected),
        "evaluated": len(evaluations),
        "sources": [source.name for source in active_sources],
        "raw_by_source": raw_by_source,
        "admitted_by_source": admitted_by_source,
        "decisions": counts,
        "applications": applications,
        "ai_review_paused": semantic_pause is not None,
        "ai_review_reason": semantic_pause["message"] if semantic_pause else None,
    }
    store.audit("discovery_cycle_completed", summary)

    strong_count = (
        counts.get("apply", 0)
        + counts.get("high_priority", 0)
        + counts.get("aggressive_pursuit", 0)
    )
    if strong_count:
        store.add_notification(
            "success",
            "New strong job matches",
            f"Jobster found {strong_count} job{'s' if strong_count != 1 else ''} worth a closer look.",
        )
    if summary.get("ai_review_paused"):
        store.add_notification(
            "warning",
            "Advanced job review paused",
            summary.get("ai_review_reason")
            or "Jobster continued with its built-in basic review.",
        )
    if applications.get("blocked", 0):
        store.add_notification(
            "warning",
            "Applications need your input",
            f"{applications['blocked']} application{'s' if applications['blocked'] != 1 else ''} stopped instead of guessing an answer.",
        )
    if applications.get("submitted_confirmed", 0):
        store.add_notification(
            "success",
            "Application submitted",
            f"{applications['submitted_confirmed']} application{'s were' if applications['submitted_confirmed'] != 1 else ' was'} confirmed as submitted.",
        )

    emit("cycle_completed", summary)
    return summary
