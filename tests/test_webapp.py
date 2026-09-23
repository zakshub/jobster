from pathlib import Path

from fastapi.testclient import TestClient

from jobster.models import (
    ApplicationPlan,
    ApplicationState,
    CareerValue,
    Job,
    JobEvaluation,
    PursuitDecision,
)
from jobster.storage import JobsterStore
from jobster.webapp import app


PROFILE = """
profile_id: zak
display_name: Zak
headline: Senior Product Designer
location: Karachi, Pakistan
years_experience: 15
target_titles:
  - Senior Product Designer
remote_only: true
compensation:
  currency: USD
  target_monthly: 6500
"""

SEARCH = """
cycle_minutes: 60
serpapi_budget:
  monthly_limit: 250
  reserve_queries: 25
  daily_limit: 7
  window_days: 30
sources:
  remoteok:
    enabled: false
  remotive:
    enabled: false
  weworkremotely:
    enabled: false
  himalayas:
    enabled: false
  google_jobs:
    enabled: false
  web_search:
    enabled: false
application:
  semantic_reasoning: false
  auto_submit: false
  answer_bank_path: private_data/answer_bank.yaml
  max_submissions_per_cycle: 5
  submission_schedule:
    enabled: true
    timezone: Asia/Karachi
    friday_stop_time: "18:00"
    monday_resume_time: "09:00"
"""


def configure_runtime(tmp_path: Path, monkeypatch):
    private = tmp_path / "private_data"
    config = tmp_path / "config"
    data = tmp_path / "data"
    private.mkdir()
    config.mkdir()
    data.mkdir()
    (private / "profile.yaml").write_text(PROFILE, encoding="utf-8")
    (private / "answer_bank.yaml").write_text("answers: []\n", encoding="utf-8")
    (config / "search.yaml").write_text(SEARCH, encoding="utf-8")

    monkeypatch.setenv("JOBSTER_PROFILE", str(private / "profile.yaml"))
    monkeypatch.setenv("JOBSTER_SEARCH", str(config / "search.yaml"))
    monkeypatch.setenv("JOBSTER_DB", str(data / "jobster.db"))
    monkeypatch.chdir(tmp_path)
    return data / "jobster.db"


def seed(db_path: Path):
    store = JobsterStore(db_path)
    store.init()
    job = Job(
        id="job-1",
        title="Senior Product Designer",
        company="Acme Health",
        description="Healthcare SaaS product design",
        location="Remote",
        remote=True,
        source="manual",
        url="https://example.com/job-1",
        salary_min_monthly=6000,
        salary_max_monthly=8000,
        currency="USD",
    )
    store.save_job(job)
    store.save_evaluation(
        JobEvaluation(
            job_id=job.id,
            summary="Strong healthcare product-design alignment.",
            eligible=True,
            role_interpretation="Senior product-design role",
            strong_matches=["Healthcare SaaS", "Design systems"],
            interest_score=94,
            career_value=CareerValue(
                compensation="good",
                growth="high",
                interesting_work="high",
                global_exposure="high",
                future_positioning="high",
            ),
            pursuit_decision=PursuitDecision.HIGH_PRIORITY,
            confidence=0.95,
            next_action="Prepare application",
        )
    )
    store.save_application_plan(
        ApplicationPlan(
            job_id=job.id,
            ats="unknown",
            state=ApplicationState.PREPARING,
            reasons=["Final submission is disabled by policy"],
        )
    )
    store.save_job(
        Job(
            id="job-noise",
            title="Payroll Assistant",
            company="Noise Co",
            description="Payroll operations",
            location="Remote",
            remote=True,
            source="remoteok",
            url="https://example.com/noise",
        )
    )


def test_web_console_status_and_jobs(tmp_path, monkeypatch):
    db_path = configure_runtime(tmp_path, monkeypatch)
    seed(db_path)

    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "JOBSTER" in root.text

    status = client.get("/api/status")
    assert status.status_code == 200
    payload = status.json()
    assert payload["profile"]["display_name"] == "Zak"
    assert payload["metrics"]["jobs"] == 1
    assert payload["metrics"]["hidden_irrelevant"] == 1
    assert payload["metrics"]["high_priority"] == 1
    assert payload["submission"]["auto_submit"] is False

    jobs = client.get("/api/jobs")
    assert jobs.status_code == 200
    assert len(jobs.json()) == 1
    assert jobs.json()[0]["interest_score"] == 94
    assert jobs.json()[0]["decision"] == "high_priority"


def test_web_console_job_detail(tmp_path, monkeypatch):
    db_path = configure_runtime(tmp_path, monkeypatch)
    seed(db_path)

    client = TestClient(app)
    response = client.get("/api/jobs/job-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["job"]["company"] == "Acme Health"
    assert payload["evaluation"]["pursuit_decision"] == "high_priority"
    assert payload["application"]["state"] == "preparing"


def test_enterprise_endpoints_and_saved_job(tmp_path, monkeypatch):
    db_path = configure_runtime(tmp_path, monkeypatch)
    seed(db_path)

    client = TestClient(app)

    saved = client.post(
        "/api/jobs/job-1/preference",
        json={"saved": True, "note": "Strong healthcare fit"},
    )
    assert saved.status_code == 200
    assert saved.json()["saved"] is True
    assert saved.json()["note"] == "Strong healthcare fit"

    jobs = client.get("/api/jobs")
    assert jobs.status_code == 200
    assert jobs.json()[0]["saved"] is True
    assert jobs.json()[0]["note"] == "Strong healthcare fit"

    detail = client.get("/api/jobs/job-1")
    assert detail.status_code == 200
    assert detail.json()["preference"]["saved"] is True

    readiness = client.get("/api/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["total"] >= 4
    assert "application_sites" in readiness.json()

    settings = client.get("/api/settings")
    assert settings.status_code == 200
    assert settings.json()["job_search"]["target_titles"] == ["Senior Product Designer"]
    assert settings.json()["applications"]["auto_apply"] is False

    pipeline = client.get("/api/pipeline")
    assert pipeline.status_code == 200
    assert pipeline.json()["preparing"] == 1


def test_attention_queue_lists_blocked_application(tmp_path, monkeypatch):
    db_path = configure_runtime(tmp_path, monkeypatch)
    seed(db_path)
    store = JobsterStore(db_path)
    store.save_application_plan(
        ApplicationPlan(
            job_id="job-1",
            ats="greenhouse",
            state=ApplicationState.BLOCKED,
            reasons=["Required question has no approved answer: Notice period"],
        )
    )

    client = TestClient(app)
    response = client.get("/api/attention")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["job_id"] == "job-1"
    assert "Notice period" in payload[0]["reasons"][0]

    status = client.get("/api/status").json()
    assert status["metrics"]["needs_you"] == 1


def test_omni_career_endpoints(tmp_path, monkeypatch):
    db_path = configure_runtime(tmp_path, monkeypatch)
    seed(db_path)
    client = TestClient(app)

    missions = client.get("/api/missions")
    assert missions.status_code == 200
    assert missions.json()

    insights = client.get("/api/insights")
    assert insights.status_code == 200
    assert "funnel" in insights.json()
    assert "sources" in insights.json()
    assert "salary" in insights.json()

    companies = client.get("/api/companies")
    assert companies.status_code == 200
    assert any(item["company"] == "Acme Health" for item in companies.json())

    watched = client.post("/api/companies/watch", json={"company": "Acme Health", "watching": True})
    assert watched.status_code == 200
    assert watched.json()["watching"] is True

    feedback = client.post(
        "/api/feedback",
        json={"job_id": "job-1", "reaction": "interesting"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["reaction"] == "interesting"

    contact = client.post(
        "/api/contacts",
        json={"name": "Jane Recruiter", "company": "Acme Health", "role": "Recruiter"},
    )
    assert contact.status_code == 200
    assert contact.json()["name"] == "Jane Recruiter"
    assert len(client.get("/api/contacts").json()) == 1

    interview = client.post(
        "/api/interviews",
        json={"company": "Acme Health", "title": "Senior Product Designer", "status": "planned"},
    )
    assert interview.status_code == 200
    assert len(client.get("/api/interviews").json()) == 1

    offer = client.post(
        "/api/offers",
        json={
            "company": "Acme Health",
            "title": "Senior Product Designer",
            "currency": "USD",
            "monthly_base": 6000,
        },
    )
    assert offer.status_code == 200
    offer_id = offer.json()["id"]
    advice = client.post(f"/api/offers/{offer_id}/advice", json={})
    assert advice.status_code == 200
    assert "leverage" in advice.json()

    goal = client.post(
        "/api/goals",
        json={"label": "Move into a stronger global product role", "horizon": "3_months"},
    )
    assert goal.status_code == 200
    assert len(client.get("/api/goals").json()) == 1

    authority = client.get("/api/authority")
    assert authority.status_code == 200
    assert authority.json()["submit"]["enabled"] is False

    update = client.post(
        "/api/authority/prepare",
        json={"enabled": False, "requires_approval": True},
    )
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    export = client.get("/api/export")
    assert export.status_code == 200
    payload = export.json()
    assert "jobs" in payload
    assert "contacts" in payload
    assert "offers" in payload


def test_recruiter_message_advice_endpoint(tmp_path, monkeypatch):
    configure_runtime(tmp_path, monkeypatch)
    client = TestClient(app)
    response = client.post(
        "/api/recruiter/advice",
        json={"message": "We would like to invite you to an interview with the hiring manager."},
    )
    assert response.status_code == 200
    assert response.json()["stage"] == "interview"


def test_pwa_files_are_served(tmp_path, monkeypatch):
    configure_runtime(tmp_path, monkeypatch)
    client = TestClient(app)
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    service_worker = client.get("/service-worker.js")
    assert service_worker.status_code == 200
