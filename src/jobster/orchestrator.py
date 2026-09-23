from __future__ import annotations

from .answer_bank import load_answer_bank
from .application_policy import build_application_plan
from .executors.browser_form import BrowserExecutionError
from .executors.registry import get_executor
from .models import ApplicationPlan, ApplicationState, Job, JobEvaluation, PursuitDecision
from .settings import SearchConfig
from .storage import JobsterStore
from .submission_schedule import is_submission_allowed


PURSUIT = {
    PursuitDecision.APPLY,
    PursuitDecision.HIGH_PRIORITY,
    PursuitDecision.AGGRESSIVE_PURSUIT,
}


def process_applications(
    jobs: list[Job],
    evaluations: list[JobEvaluation],
    config: SearchConfig,
    store: JobsterStore,
) -> dict:
    by_job = {job.id: job for job in jobs}
    answer_bank = load_answer_bank(config.application.answer_bank_path)
    authority = store.get_authority()
    prepare_authorized = authority.get("prepare", {}).get("enabled", True)
    submit_rule = authority.get("submit", {})
    submit_authorized = bool(
        submit_rule.get("enabled", False)
        and not submit_rule.get("requires_approval", True)
    )
    submission_window_open = is_submission_allowed(
        config.application.submission_schedule
    )
    summary = {
        "considered": 0,
        "blocked": 0,
        "ready": 0,
        "submitted_confirmed": 0,
        "needs_verification": 0,
        "unsupported": 0,
        "errors": 0,
        "submission_window_open": submission_window_open,
        "prepare_authorized": prepare_authorized,
        "submit_authorized": submit_authorized,
    }
    submitted_this_cycle = 0

    for evaluation in evaluations:
        if not evaluation.eligible or evaluation.pursuit_decision not in PURSUIT:
            continue

        summary["considered"] += 1
        job = by_job[evaluation.job_id]

        if not prepare_authorized:
            plan = ApplicationPlan(
                job_id=job.id,
                ats="unknown",
                state=ApplicationState.SHORTLISTED,
                reasons=["Automatic application preparation is turned off in the Authority Center"],
            )
            store.save_application_plan(plan)
            store.audit(
                "application_preparation_paused",
                {"reason": "prepare_authority_off"},
                job_id=job.id,
            )
            summary["ready"] += 1
            continue

        executor = get_executor(job)

        if executor is None:
            plan = ApplicationPlan(
                job_id=job.id,
                ats="unknown",
                state=ApplicationState.BLOCKED,
                reasons=["No supported ATS executor for this application URL"],
            )
            store.save_application_plan(plan)
            store.audit("application_unsupported", {"url": job.url}, job_id=job.id)
            summary["unsupported"] += 1
            continue

        try:
            questions = executor.inspect_questions(job)
            allow_submit = (
                config.application.auto_submit
                and submit_authorized
                and submission_window_open
                and executor.capability.can_submit
                and submitted_this_cycle < config.application.max_submissions_per_cycle
            )
            plan = build_application_plan(
                job,
                questions,
                answer_bank,
                allow_final_submit=allow_submit,
            )

            if config.application.auto_submit and not submit_authorized:
                plan.reasons.append(
                    "Final submission is not authorized in the Authority Center"
                )
                store.audit(
                    "application_submission_not_authorized",
                    {"authority": submit_rule},
                    job_id=job.id,
                )

            if config.application.auto_submit and not submission_window_open:
                plan.reasons.append(
                    "Submission paused by schedule: Friday evening through Monday morning"
                )
                store.audit(
                    "application_submission_window_closed",
                    {
                        "timezone": config.application.submission_schedule.timezone,
                        "friday_stop_time": config.application.submission_schedule.friday_stop_time,
                        "monday_resume_time": config.application.submission_schedule.monday_resume_time,
                    },
                    job_id=job.id,
                )

            store.save_application_plan(plan)

            if plan.state == ApplicationState.BLOCKED:
                summary["blocked"] += 1
                store.audit(
                    "application_blocked",
                    {
                        "blocked_questions": [q.label for q in plan.blocked_questions],
                        "unknown_questions": [q.label for q in plan.unknown_questions],
                    },
                    job_id=job.id,
                )
                continue

            if not plan.can_submit_automatically:
                summary["ready"] += 1
                store.audit("application_prepared", {"ats": plan.ats}, job_id=job.id)
                continue

            receipt = executor.execute(job, plan)
            store.save_receipt(job.id, receipt)
            submitted_this_cycle += 1

            if receipt.get("status") == "submitted_confirmed":
                plan.state = ApplicationState.SUBMITTED
                summary["submitted_confirmed"] += 1
            else:
                plan.state = ApplicationState.BLOCKED
                plan.reasons.append(
                    "Submit action occurred but success confirmation was not detected"
                )
                summary["needs_verification"] += 1
            store.save_application_plan(plan)
            store.audit("application_execution", receipt, job_id=job.id)

        except BrowserExecutionError as exc:
            plan = ApplicationPlan(
                job_id=job.id,
                ats=getattr(executor.capability, "ats", "unknown"),
                state=ApplicationState.BLOCKED,
                reasons=[str(exc)],
            )
            store.save_application_plan(plan)
            store.audit(
                "application_browser_error",
                {"error": str(exc)},
                job_id=job.id,
            )
            summary["errors"] += 1

    return summary
