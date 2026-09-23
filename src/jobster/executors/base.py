from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from jobster.models import ApplicationPlan, ApplicationQuestion, Job


@dataclass(frozen=True)
class ExecutorCapability:
    ats: str
    can_inspect: bool
    can_fill: bool
    can_upload: bool
    can_submit: bool


class ApplicationExecutor(ABC):
    capability: ExecutorCapability

    @abstractmethod
    def supports(self, job: Job) -> bool:
        raise NotImplementedError

    @abstractmethod
    def inspect_questions(self, job: Job) -> list[ApplicationQuestion]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, job: Job, plan: ApplicationPlan) -> dict:
        raise NotImplementedError
