from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from .settings import SubmissionScheduleConfig


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))


def is_submission_allowed(
    config: SubmissionScheduleConfig,
    now: datetime | None = None,
) -> bool:
    if not config.enabled:
        return True

    tz = ZoneInfo(config.timezone)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    current = local_now.time().replace(tzinfo=None)

    # Python weekday: Monday=0 ... Friday=4, Saturday=5, Sunday=6.
    weekday = local_now.weekday()

    if weekday == 4 and current >= _parse_hhmm(config.friday_stop_time):
        return False
    if weekday in {5, 6}:
        return False
    if weekday == 0 and current < _parse_hhmm(config.monday_resume_time):
        return False
    return True
