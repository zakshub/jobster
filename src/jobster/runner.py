from __future__ import annotations

from .brain import CareerBrain
from .discovery import discover
from .models import CareerProfile, PursuitDecision
from .orchestrator import process_applications
from .semantic import SemanticCareerBrain
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
    jobs = discover(build_sources(config))
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
        "decisions": counts,
        "applications": applications,
    }
    store.audit("discovery_cycle_completed", summary)
    return summary
