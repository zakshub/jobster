from jobster.answer_bank import answer_lookup
from jobster.application_policy import build_application_plan
from jobster.models import ApplicationAnswer, ApplicationQuestion, Job


def test_alias_maps_to_verified_answer():
    answers = [
        ApplicationAnswer(
            key="portfolio_url",
            value="https://example.com",
            aliases=["Portfolio Website"],
            verified=True,
            allow_automatic_use=True,
        )
    ]
    lookup = answer_lookup(answers)
    assert "portfolio_website" in lookup

    job = Job(id="j", title="Designer", company="Acme", description="x")
    question = ApplicationQuestion(key="portfolio_website", label="Portfolio Website", required=True)
    plan = build_application_plan(job, [question], answers, allow_final_submit=True)
    assert plan.can_submit_automatically is True
