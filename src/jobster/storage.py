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
CREATE TABLE IF NOT EXISTS automation_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
                (
                    evaluation.job_id,
                    evaluation.pursuit_decision.value,
                    evaluation.model_dump_json(),
                ),
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

    def save_receipt(self, job_id: str, receipt: dict) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO automation_receipts(job_id, status, payload_json) VALUES (?, ?, ?)",
                (
                    job_id,
                    str(receipt.get("status", "unknown")),
                    json.dumps(receipt, sort_keys=True),
                ),
            )

    def audit(self, event_type: str, payload: dict, job_id: str | None = None) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO audit_events(job_id, event_type, payload_json) VALUES (?, ?, ?)",
                (job_id, event_type, json.dumps(payload, sort_keys=True)),
            )

    def dashboard_metrics(self) -> dict:
        with self.connect() as con:
            jobs = con.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"]
            evaluated = con.execute(
                "SELECT COUNT(*) AS n FROM evaluations"
            ).fetchone()["n"]
            applications = con.execute(
                "SELECT COUNT(*) AS n FROM application_plans"
            ).fetchone()["n"]
            submitted = con.execute(
                "SELECT COUNT(*) AS n FROM application_plans WHERE state = 'submitted'"
            ).fetchone()["n"]
            ready = con.execute(
                "SELECT COUNT(*) AS n FROM application_plans WHERE state IN ('ready', 'preparing')"
            ).fetchone()["n"]
            blocked = con.execute(
                "SELECT COUNT(*) AS n FROM application_plans WHERE state = 'blocked'"
            ).fetchone()["n"]
            high_priority = con.execute(
                "SELECT COUNT(*) AS n FROM evaluations WHERE decision IN ('high_priority', 'aggressive_pursuit')"
            ).fetchone()["n"]

        return {
            "jobs": jobs,
            "evaluated": evaluated,
            "applications": applications,
            "submitted": submitted,
            "ready": ready,
            "blocked": blocked,
            "high_priority": high_priority,
        }

    def list_job_summaries(self, limit: int = 100, offset: int = 0) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT
                    j.id,
                    j.source,
                    j.title,
                    j.company,
                    j.url,
                    j.payload_json,
                    j.updated_at,
                    e.decision,
                    e.payload_json AS evaluation_json,
                    p.state AS application_state,
                    p.ats
                FROM jobs j
                LEFT JOIN evaluations e ON e.job_id = j.id
                LEFT JOIN application_plans p ON p.job_id = j.id
                ORDER BY
                    CASE e.decision
                        WHEN 'aggressive_pursuit' THEN 0
                        WHEN 'high_priority' THEN 1
                        WHEN 'apply' THEN 2
                        WHEN 'watch' THEN 3
                        WHEN 'low_priority' THEN 4
                        WHEN 'ignore' THEN 5
                        ELSE 6
                    END,
                    j.updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        output: list[dict] = []
        for row in rows:
            job = json.loads(row["payload_json"])
            evaluation = (
                json.loads(row["evaluation_json"])
                if row["evaluation_json"]
                else None
            )
            output.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "company": row["company"],
                    "source": row["source"],
                    "url": row["url"],
                    "location": job.get("location"),
                    "remote": job.get("remote"),
                    "salary_min_monthly": job.get("salary_min_monthly"),
                    "salary_max_monthly": job.get("salary_max_monthly"),
                    "currency": job.get("currency"),
                    "decision": row["decision"],
                    "interest_score": (
                        evaluation.get("interest_score") if evaluation else None
                    ),
                    "confidence": evaluation.get("confidence") if evaluation else None,
                    "eligible": evaluation.get("eligible") if evaluation else None,
                    "application_state": row["application_state"],
                    "ats": row["ats"],
                    "updated_at": row["updated_at"],
                }
            )
        return output

    def get_job_bundle(self, job_id: str) -> dict | None:
        with self.connect() as con:
            row = con.execute(
                """
                SELECT
                    j.payload_json AS job_json,
                    e.payload_json AS evaluation_json,
                    p.payload_json AS application_json
                FROM jobs j
                LEFT JOIN evaluations e ON e.job_id = j.id
                LEFT JOIN application_plans p ON p.job_id = j.id
                WHERE j.id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "job": json.loads(row["job_json"]),
            "evaluation": (
                json.loads(row["evaluation_json"])
                if row["evaluation_json"]
                else None
            ),
            "application": (
                json.loads(row["application_json"])
                if row["application_json"]
                else None
            ),
        }

    def list_application_summaries(self, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT
                    p.job_id,
                    p.state,
                    p.ats,
                    p.payload_json,
                    p.updated_at,
                    j.title,
                    j.company,
                    j.url
                FROM application_plans p
                JOIN jobs j ON j.id = p.job_id
                ORDER BY p.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "job_id": row["job_id"],
                "title": row["title"],
                "company": row["company"],
                "url": row["url"],
                "state": row["state"],
                "ats": row["ats"],
                "plan": json.loads(row["payload_json"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def list_activity(self, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT id, job_id, event_type, payload_json, created_at
                FROM audit_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "job_id": row["job_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
