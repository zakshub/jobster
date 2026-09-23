from jobster.models import CareerProfile, Job, JobEvaluation, CareerValue, PursuitDecision
from jobster.orchestrator import process_applications
from jobster.settings import SearchConfig
from jobster.storage import JobsterStore


def test_unknown_executor_is_blocked(tmp_path, monkeypatch):
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


def test_prepare_authority_can_pause_application_inspection(tmp_path):
    store = JobsterStore(tmp_path / "db.sqlite")
    store.init()
    store.set_authority("prepare", False, True)

    job = Job(
        id="j2",
        title="Senior Product Designer",
        company="Acme",
        description="x",
        remote=True,
        url="https://boards.greenhouse.io/acme/jobs/123",
    )
    store.save_job(job)
    evaluation = JobEvaluation(
        job_id="j2",
        summary="apply",
        eligible=True,
        role_interpretation="role",
        interest_score=90,
        career_value=CareerValue(),
        pursuit_decision=PursuitDecision.HIGH_PRIORITY,
        confidence=0.9,
        next_action="apply",
    )
    config = SearchConfig()

    result = process_applications([job], [evaluation], config, store)
    assert result["prepare_authorized"] is False

    bundle = store.get_job_bundle("j2")
    assert bundle["application"]["state"] == "shortlisted"
    assert "Authority Center" in bundle["application"]["reasons"][0]
