from __future__ import annotations

import re

from .answer_bank import answer_lookup
from .ats import detect_ats
from .field_keys import normalize_question
from .models import ApplicationAnswer, ApplicationPlan, ApplicationQuestion, ApplicationState, Job


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

    # Keep every explicitly approved reusable answer available to the browser
    # executor. Multi-page forms often reveal later questions only after the
    # first page has been completed. This does not weaken sensitive-answer
    # safeguards: only verified answers with automatic-use permission enter
    # this map.
    for answer in answer_bank:
        if not answer.verified or not answer.allow_automatic_use:
            continue
        for raw_key in [answer.key, *answer.aliases]:
            normalized = normalize_question(raw_key)
            if normalized:
                known.setdefault(normalized, answer.value)

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
