from __future__ import annotations

from jobster.ats import detect_ats
from jobster.models import Job
from .browser_form import AshbyExecutor, GreenhouseExecutor, LeverExecutor, WorkdayExecutor


EXECUTORS = {
    "greenhouse": GreenhouseExecutor,
    "lever": LeverExecutor,
    "ashby": AshbyExecutor,
    "workday": WorkdayExecutor,
}


def get_executor(job: Job):
    ats = detect_ats(job.url)
    cls = EXECUTORS.get(ats)
    return cls() if cls else None
