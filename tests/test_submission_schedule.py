from datetime import datetime
from zoneinfo import ZoneInfo

from jobster.settings import SubmissionScheduleConfig
from jobster.submission_schedule import is_submission_allowed


KARACHI = ZoneInfo("Asia/Karachi")


def test_friday_before_evening_is_allowed():
    config = SubmissionScheduleConfig()
    now = datetime(2026, 9, 25, 17, 59, tzinfo=KARACHI)
    assert is_submission_allowed(config, now) is True


def test_friday_evening_is_blocked():
    config = SubmissionScheduleConfig()
    now = datetime(2026, 9, 25, 18, 0, tzinfo=KARACHI)
    assert is_submission_allowed(config, now) is False


def test_weekend_is_blocked():
    config = SubmissionScheduleConfig()
    saturday = datetime(2026, 9, 26, 12, 0, tzinfo=KARACHI)
    sunday = datetime(2026, 9, 27, 12, 0, tzinfo=KARACHI)
    assert is_submission_allowed(config, saturday) is False
    assert is_submission_allowed(config, sunday) is False


def test_monday_morning_resumes_at_nine():
    config = SubmissionScheduleConfig()
    before = datetime(2026, 9, 28, 8, 59, tzinfo=KARACHI)
    after = datetime(2026, 9, 28, 9, 0, tzinfo=KARACHI)
    assert is_submission_allowed(config, before) is False
    assert is_submission_allowed(config, after) is True
