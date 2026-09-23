from __future__ import annotations

from abc import ABC, abstractmethod

from jobster.models import Job


class JobSource(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> list[Job]:
        raise NotImplementedError
