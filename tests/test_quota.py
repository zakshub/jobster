from datetime import datetime, timedelta, timezone

from jobster.quota import SerpApiQuota


def test_quota_enforces_daily_limit(tmp_path):
    quota = SerpApiQuota(
        tmp_path / "quota.json",
        monthly_limit=250,
        reserve_queries=25,
        daily_limit=2,
        window_days=30,
    )
    now = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    assert quota.consume(now=now) is True
    assert quota.consume(now=now) is True
    assert quota.consume(now=now) is False


def test_quota_persists_across_instances(tmp_path):
    path = tmp_path / "quota.json"
    now = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)

    first = SerpApiQuota(path, monthly_limit=250, reserve_queries=25, daily_limit=7)
    assert first.consume(now=now) is True

    second = SerpApiQuota(path, monthly_limit=250, reserve_queries=25, daily_limit=7)
    status = second.status(now=now)
    assert status.used_in_window == 1
    assert status.used_today == 1


def test_quota_resets_after_30_day_window(tmp_path):
    path = tmp_path / "quota.json"
    start = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    quota = SerpApiQuota(
        path,
        monthly_limit=250,
        reserve_queries=25,
        daily_limit=7,
        window_days=30,
    )
    assert quota.consume(now=start) is True

    later = start + timedelta(days=30, minutes=1)
    status = quota.status(now=later)
    assert status.used_in_window == 0
    assert status.used_today == 0
