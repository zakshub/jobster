from jobster.intelligence import (
    build_daily_missions,
    build_insights,
    build_salary_intelligence,
)
from jobster.models import (
    CareerProfile,
    CareerValue,
    Job,
    JobEvaluation,
    PursuitDecision,
)
from jobster.storage import JobsterStore


def seed(tmp_path):
    store = JobsterStore(tmp_path / "jobster.db")
    store.init()
    profile = CareerProfile(
        profile_id="p",
        display_name="Candidate",
        target_titles=["Senior Product Designer"],
    )
    profile.compensation.currency = "USD"
    profile.compensation.target_monthly = 6500

    jobs = [
        Job(
            id="j1",
            title="Senior Product Designer",
            company="Acme",
            description="Healthcare design systems",
            remote=True,
            source="source_a",
            salary_min_monthly=6000,
            salary_max_monthly=8000,
            currency="USD",
        ),
        Job(
            id="j2",
            title="Product Designer",
            company="Beta",
            description="Product design",
            remote=True,
            source="source_b",
            salary_min_monthly=5000,
            salary_max_monthly=7000,
            currency="USD",
        ),
    ]
    for job in jobs:
        store.save_job(job)

    store.save_evaluation(
        JobEvaluation(
            job_id="j1",
            summary="Strong fit",
            eligible=True,
            role_interpretation="Senior product design",
            learnable_gaps=["AI prototyping"],
            interest_score=94,
            career_value=CareerValue(growth="high", interesting_work="high"),
            pursuit_decision=PursuitDecision.HIGH_PRIORITY,
            confidence=0.9,
            next_action="Prepare",
        )
    )
    store.save_evaluation(
        JobEvaluation(
            job_id="j2",
            summary="Good fit",
            eligible=True,
            role_interpretation="Product design",
            interest_score=82,
            career_value=CareerValue(growth="medium", interesting_work="high"),
            pursuit_decision=PursuitDecision.APPLY,
            confidence=0.8,
            next_action="Review",
        )
    )
    return profile, store


def test_salary_intelligence_uses_same_currency(tmp_path):
    profile, store = seed(tmp_path)
    result = build_salary_intelligence(profile, store)
    assert result["currency"] == "USD"
    assert result["strong_jobs"]["count"] == 2
    assert result["strong_jobs"]["median"] == 6500


def test_insights_include_sources_roles_and_gaps(tmp_path):
    profile, store = seed(tmp_path)
    result = build_insights(profile, store)
    assert result["sources"][0]["strong"] >= 1
    assert any(item["family"] == "Product Design" for item in result["roles"])
    assert result["gaps"][0]["gap"] == "AI prototyping"


def test_daily_missions_surface_strong_opportunity(tmp_path):
    profile, store = seed(tmp_path)
    missions = build_daily_missions(profile, store)
    assert missions
    assert missions[0]["kind"] == "opportunity"
    assert missions[0]["job_id"] == "j1"
