import pytest

from jobster.executors.browser_form import BrowserExecutionError, GenericCareersExecutor, WorkdayExecutor, classify_form_action
from jobster.executors.registry import get_executor
from jobster.models import ApplicationPlan, ApplicationState, Job


def test_registry_routes_supported_ats():
    greenhouse = Job(id="1", title="x", company="x", description="x", url="https://boards.greenhouse.io/acme/jobs/1")
    lever = Job(id="2", title="x", company="x", description="x", url="https://jobs.lever.co/acme/1")
    ashby = Job(id="3", title="x", company="x", description="x", url="https://jobs.ashbyhq.com/acme/1")
    assert get_executor(greenhouse).capability.ats == "greenhouse"
    assert get_executor(lever).capability.ats == "lever"
    assert get_executor(ashby).capability.ats == "ashby"


def test_workday_is_inspection_only():
    job = Job(id="4", title="x", company="x", description="x", url="https://acme.wd5.myworkdayjobs.com/jobs/job/1")
    executor = get_executor(job)
    assert isinstance(executor, WorkdayExecutor)
    assert executor.capability.can_submit is False
    plan = ApplicationPlan(job_id="4", ats="workday", state=ApplicationState.READY, can_submit_automatically=True)
    with pytest.raises(BrowserExecutionError):
        executor.execute(job, plan)


def test_generic_company_careers_form_is_supervised():
    job = Job(
        id="5",
        title="x",
        company="x",
        description="x",
        url="https://example.com/careers/jobs/designer",
    )
    executor = get_executor(job)
    assert isinstance(executor, GenericCareersExecutor)
    assert executor.capability.can_inspect is True
    assert executor.capability.can_fill is True
    assert executor.capability.can_submit is False


def test_form_action_classifier_separates_next_from_final_submit():
    assert classify_form_action("Continue") == "next"
    assert classify_form_action("Review application") == "next"
    assert classify_form_action("Submit application") == "final"
    assert classify_form_action("Apply now") == "final"
    assert classify_form_action("Cancel") == "other"
