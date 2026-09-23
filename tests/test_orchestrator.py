from jobster.models import CareerProfile, Job, JobEvaluation, CareerValue, PursuitDecision
from jobster.orchestrator import process_applications
from jobster.settings import SearchConfig
from jobster.storage import JobsterStore


def test_unknown_executor_is_blocked(tmp_path):
    store = JobsterStore(tmp_path / "db.sqlite")
    store.init()
    job = Job(id="j", title="Designer", company="Acme", description="x", remote=True, url="https://example.com/opening")
    store.save_job(job)
    evaluation = JobEvaluation(
        job_id="j",
        summary="apply",
        eligible=True,
        role_interpretation="role",
        interest_score=80,
        career_value=CareerValue(),
        pursuit_decision=PursuitDecision.APPLY,
        confidence=0.8,
        next_action="apply",
    )
    config = SearchConfig()
    result = process_applications([job], [evaluation], config, store)
    assert result["unsupported"] == 1
