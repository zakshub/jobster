from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ApplicationPlan, Job, JobEvaluation


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS evaluations (
    job_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS application_plans (
    job_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    ats TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class JobsterStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def init(self) -> None:
        with self.connect() as con:
            con.executescript(SCHEMA)

    def save_job(self, job: Job) -> None:
        payload = job.model_dump_json()
        with self.connect() as con:
            con.execute(
                """INSERT INTO jobs(id, source, title, company, url, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  source=excluded.source,
                  title=excluded.title,
                  company=excluded.company,
                  url=excluded.url,
                  payload_json=excluded.payload_json,
                  updated_at=CURRENT_TIMESTAMP""",
                (job.id, job.source, job.title, job.company, job.url, payload),
            )

    def save_evaluation(self, evaluation: JobEvaluation) -> None:
        with self.connect() as con:
            con.execute(
                """INSERT INTO evaluations(job_id, decision, payload_json)
                VALUES (?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  decision=excluded.decision,
                  payload_json=excluded.payload_json""",
                (evaluation.job_id, evaluation.pursuit_decision.value, evaluation.model_dump_json()),
            )

    def save_application_plan(self, plan: ApplicationPlan) -> None:
        with self.connect() as con:
            con.execute(
                """INSERT INTO application_plans(job_id, state, ats, payload_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  state=excluded.state,
                  ats=excluded.ats,
                  payload_json=excluded.payload_json,
                  updated_at=CURRENT_TIMESTAMP""",
                (plan.job_id, plan.state.value, plan.ats, plan.model_dump_json()),
            )

    def audit(self, event_type: str, payload: dict, job_id: str | None = None) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO audit_events(job_id, event_type, payload_json) VALUES (?, ?, ?)",
                (job_id, event_type, json.dumps(payload, sort_keys=True)),
            )
