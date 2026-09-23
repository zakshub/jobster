from __future__ import annotations

from .brain import CareerBrain
from .models import CareerProfile, Job, PursuitDecision
from .storage import JobsterStore


QUEUE_DECISIONS = {
    PursuitDecision.APPLY,
    PursuitDecision.HIGH_PRIORITY,
    PursuitDecision.AGGRESSIVE_PURSUIT,
}


def evaluate_and_store(profile: CareerProfile, jobs: list[Job], store: JobsterStore):
    brain = CareerBrain()
    results = []
    for job in jobs:
        store.save_job(job)
        evaluation = brain.evaluate(profile, job)
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
        results.append(evaluation)
    return results
