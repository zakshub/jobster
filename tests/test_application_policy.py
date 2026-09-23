from jobster.application_policy import build_application_plan, normalize_question, sensitive_category
from jobster.models import ApplicationAnswer, ApplicationQuestion, ApplicationState, Job


def job():
    return Job(id="j1", title="Designer", company="Acme", description="x", url="https://boards.greenhouse.io/acme/jobs/1")


def test_sensitive_unknown_question_blocks():
    questions = [ApplicationQuestion(key="work_authorization", label="Are you authorized to work in the United States?", required=True)]
    plan = build_application_plan(job(), questions, [], allow_final_submit=True)
    assert plan.state == ApplicationState.BLOCKED
    assert plan.can_submit_automatically is False
    assert plan.blocked_questions


def test_verified_authorized_answer_can_be_used():
    questions = [ApplicationQuestion(key="portfolio", label="Portfolio URL", required=True)]
    answers = [ApplicationAnswer(key="portfolio", value="https://example.com", verified=True, allow_automatic_use=True)]
    plan = build_application_plan(job(), questions, answers, allow_final_submit=True)
    assert plan.state == ApplicationState.READY
    assert plan.can_submit_automatically is True


def test_submit_policy_can_keep_ready_information_in_preparing_state():
    questions = [ApplicationQuestion(key="portfolio", label="Portfolio URL", required=True)]
    answers = [ApplicationAnswer(key="portfolio", value="https://example.com", verified=True, allow_automatic_use=True)]
    plan = build_application_plan(job(), questions, answers, allow_final_submit=False)
    assert plan.can_submit_automatically is False
    assert plan.state == ApplicationState.PREPARING


def test_sensitive_classifier():
    assert sensitive_category("Will you now or in the future require visa sponsorship?") == "sponsorship"
    assert sensitive_category("Portfolio URL") is None
    assert normalize_question("Portfolio URL") == "portfolio_url"
