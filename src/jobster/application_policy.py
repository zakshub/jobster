from __future__ import annotations

import re

from .answer_bank import answer_lookup
from .models import ApplicationAnswer, ApplicationPlan, ApplicationQuestion, ApplicationState, Job
from .ats import detect_ats


SENSITIVE_PATTERNS = {
    "work_authorization": [r"work authori[sz]ation", r"authorized to work", r"right to work"],
    "sponsorship": [r"sponsor", r"visa"],
    "salary_history": [r"current salary", r"salary history", r"previous salary"],
    "legal": [r"certify", r"legal", r"under penalty", r"attest"],
    "disability": [r"disability", r"disabled", r"medical condition"],
    "security_clearance": [r"security clearance", r"clearance level"],
    "criminal_history": [r"convicted", r"criminal", r"felony"],
    "relocation": [r"relocat"],
}


def normalize_question(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def sensitive_category(label: str) -> str | None:
    low = label.lower()
    for category, patterns in SENSITIVE_PATTERNS.items():
        if any(re.search(pattern, low) for pattern in patterns):
            return category
    return None


def build_application_plan(
    job: Job,
    questions: list[ApplicationQuestion],
    answer_bank: list[ApplicationAnswer],
    allow_final_submit: bool = False,
) -> ApplicationPlan:
    answers_by_key = answer_lookup(answer_bank)
    known: dict[str, str] = {}
    blocked: list[ApplicationQuestion] = []
    unknown: list[ApplicationQuestion] = []
    reasons: list[str] = []

    for question in questions:
        key = normalize_question(question.key or question.label)
        category = sensitive_category(question.label)
        answer = answers_by_key.get(key)

        if category:
            if not answer or not answer.verified or not answer.allow_automatic_use:
                blocked.append(question)
                reasons.append(f"Sensitive question requires explicit verified authority: {question.label}")
                continue

        if answer and answer.verified and answer.allow_automatic_use:
            known[question.key] = answer.value
        elif question.required:
            unknown.append(question)
            reasons.append(f"Required question has no approved answer: {question.label}")

    can_submit = allow_final_submit and not blocked and not unknown
    state = ApplicationState.READY if can_submit else ApplicationState.BLOCKED if blocked or unknown else ApplicationState.PREPARING

    if not allow_final_submit:
        reasons.append("Final submission is disabled by policy")

    return ApplicationPlan(
        job_id=job.id,
        ats=detect_ats(job.url),
        state=state,
        known_answers=known,
        blocked_questions=blocked,
        unknown_questions=unknown,
        can_submit_automatically=can_submit,
        reasons=reasons,
    )
