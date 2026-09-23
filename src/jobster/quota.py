from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class QuotaStatus:
    allowed: bool
    used_in_window: int
    usable_limit: int
    used_today: int
    daily_limit: int
    window_started_at: str
    window_ends_at: str


class SerpApiQuota:
    """Persistent local quota guard for paid SerpAPI calls."""

    def __init__(
        self,
        path: str | Path,
        monthly_limit: int = 250,
        reserve_queries: int = 25,
        daily_limit: int = 7,
        window_days: int = 30,
    ):
        self.path = Path(path)
        self.monthly_limit = max(1, monthly_limit)
        self.reserve_queries = max(0, min(reserve_queries, self.monthly_limit - 1))
        self.daily_limit = max(1, daily_limit)
        self.window_days = max(1, window_days)

    @property
    def usable_limit(self) -> int:
        return self.monthly_limit - self.reserve_queries

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _fresh_state(self, now: datetime) -> dict:
        return {
            "window_started_at": now.isoformat(),
            "used_in_window": 0,
            "days": {},
        }

    def _load(self, now: datetime) -> dict:
        if not self.path.exists():
            return self._fresh_state(now)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            started = datetime.fromisoformat(data["window_started_at"])
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if now >= started + timedelta(days=self.window_days):
                return self._fresh_state(now)
            if not isinstance(data.get("days"), dict):
                data["days"] = {}
            return data
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return self._fresh_state(now)

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def status(self, now: datetime | None = None) -> QuotaStatus:
        now = now or self._now()
        data = self._load(now)
        started = datetime.fromisoformat(data["window_started_at"])
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        day_key = now.date().isoformat()
        used_today = int(data["days"].get(day_key, 0))
        used_in_window = int(data.get("used_in_window", 0))
        allowed = (
            used_in_window < self.usable_limit
            and used_today < self.daily_limit
        )
        return QuotaStatus(
            allowed=allowed,
            used_in_window=used_in_window,
            usable_limit=self.usable_limit,
            used_today=used_today,
            daily_limit=self.daily_limit,
            window_started_at=started.isoformat(),
            window_ends_at=(started + timedelta(days=self.window_days)).isoformat(),
        )

    def consume(self, amount: int = 1, now: datetime | None = None) -> bool:
        amount = max(1, amount)
        now = now or self._now()
        data = self._load(now)
        day_key = now.date().isoformat()
        used_today = int(data["days"].get(day_key, 0))
        used_in_window = int(data.get("used_in_window", 0))

        if used_today + amount > self.daily_limit:
            return False
        if used_in_window + amount > self.usable_limit:
            return False

        data["days"][day_key] = used_today + amount
        data["used_in_window"] = used_in_window + amount
        self._save(data)
        return True
