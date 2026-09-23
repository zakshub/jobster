from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ApplicationPlan, Job, JobEvaluation
from .text_utils import repair_text


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
CREATE TABLE IF NOT EXISTS job_verifications (
    job_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    status_code INTEGER,
    final_url TEXT,
    detail TEXT NOT NULL,
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS job_preferences (
    job_id TEXT PRIMARY KEY,
    saved INTEGER NOT NULL DEFAULT 0,
    dismissed INTEGER NOT NULL DEFAULT 0,
    note TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
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

    def save_job_verification(self, job_id: str, verification: dict) -> None:
        with self.connect() as con:
            con.execute(
                """INSERT INTO job_verifications(job_id, state, status_code, final_url, detail)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  state=excluded.state,
                  status_code=excluded.status_code,
                  final_url=excluded.final_url,
                  detail=excluded.detail,
                  checked_at=CURRENT_TIMESTAMP""",
                (
                    job_id,
                    str(verification.get("state", "needs_review")),
                    verification.get("status_code"),
                    verification.get("final_url"),
                    str(verification.get("detail", "")),
                ),
            )

    def get_job_verification(self, job_id: str) -> dict | None:
        with self.connect() as con:
            row = con.execute(
                """SELECT state, status_code, final_url, detail, checked_at
                FROM job_verifications WHERE job_id = ?""",
                (job_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def save_job_preference(
        self,
        job_id: str,
        *,
        saved: bool | None = None,
        dismissed: bool | None = None,
        note: str | None = None,
    ) -> dict:
        with self.connect() as con:
            existing = con.execute(
                "SELECT saved, dismissed, note FROM job_preferences WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            current_saved = bool(existing["saved"]) if existing else False
            current_dismissed = bool(existing["dismissed"]) if existing else False
            current_note = existing["note"] if existing else None

            next_saved = current_saved if saved is None else bool(saved)
            next_dismissed = current_dismissed if dismissed is None else bool(dismissed)
            next_note = current_note if note is None else note

            con.execute(
                """INSERT INTO job_preferences(job_id, saved, dismissed, note)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  saved=excluded.saved,
                  dismissed=excluded.dismissed,
                  note=excluded.note,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    job_id,
                    1 if next_saved else 0,
                    1 if next_dismissed else 0,
                    next_note,
                ),
            )
        return {
            "job_id": job_id,
            "saved": next_saved,
            "dismissed": next_dismissed,
            "note": next_note,
        }

    def get_job_preference(self, job_id: str) -> dict:
        with self.connect() as con:
            row = con.execute(
                "SELECT saved, dismissed, note, updated_at FROM job_preferences WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return {
                "job_id": job_id,
                "saved": False,
                "dismissed": False,
                "note": None,
                "updated_at": None,
            }
        return {
            "job_id": job_id,
            "saved": bool(row["saved"]),
            "dismissed": bool(row["dismissed"]),
            "note": row["note"],
            "updated_at": row["updated_at"],
        }

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
            saved = con.execute(
                "SELECT COUNT(*) AS n FROM job_preferences WHERE saved = 1"
            ).fetchone()["n"]

        return {
            "jobs": jobs,
            "evaluated": evaluated,
            "applications": applications,
            "submitted": submitted,
            "ready": ready,
            "blocked": blocked,
            "high_priority": high_priority,
            "saved": saved,
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
                    p.ats,
                    v.state AS verification_state,
                    v.checked_at AS verification_checked_at,
                    COALESCE(pref.saved, 0) AS saved,
                    COALESCE(pref.dismissed, 0) AS dismissed,
                    pref.note AS preference_note
                FROM jobs j
                LEFT JOIN evaluations e ON e.job_id = j.id
                LEFT JOIN application_plans p ON p.job_id = j.id
                LEFT JOIN job_verifications v ON v.job_id = j.id
                LEFT JOIN job_preferences pref ON pref.job_id = j.id
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
                    "title": repair_text(row["title"]),
                    "company": repair_text(row["company"]),
                    "source": row["source"],
                    "url": row["url"],
                    "location": repair_text(job.get("location")) if job.get("location") else None,
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
                    "verification_state": row["verification_state"],
                    "verification_checked_at": row["verification_checked_at"],
                    "saved": bool(row["saved"]),
                    "dismissed": bool(row["dismissed"]),
                    "note": row["preference_note"],
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
                    p.payload_json AS application_json,
                    v.state AS verification_state,
                    v.status_code AS verification_status_code,
                    v.final_url AS verification_final_url,
                    v.detail AS verification_detail,
                    v.checked_at AS verification_checked_at,
                    COALESCE(pref.saved, 0) AS saved,
                    COALESCE(pref.dismissed, 0) AS dismissed,
                    pref.note AS preference_note
                FROM jobs j
                LEFT JOIN evaluations e ON e.job_id = j.id
                LEFT JOIN application_plans p ON p.job_id = j.id
                LEFT JOIN job_verifications v ON v.job_id = j.id
                LEFT JOIN job_preferences pref ON pref.job_id = j.id
                WHERE j.id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        job_payload = json.loads(row["job_json"])
        job_payload["title"] = repair_text(job_payload.get("title"))
        job_payload["company"] = repair_text(job_payload.get("company"))
        if job_payload.get("location"):
            job_payload["location"] = repair_text(job_payload.get("location"))
        verification = None
        if row["verification_state"]:
            verification = {
                "state": row["verification_state"],
                "status_code": row["verification_status_code"],
                "final_url": row["verification_final_url"],
                "detail": row["verification_detail"],
                "checked_at": row["verification_checked_at"],
            }
        return {
            "job": job_payload,
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
            "verification": verification,
            "preference": {
                "job_id": job_id,
                "saved": bool(row["saved"]),
                "dismissed": bool(row["dismissed"]),
                "note": row["preference_note"],
            },
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


    def pipeline_counts(self) -> dict:
        with self.connect() as con:
            rows = con.execute(
                "SELECT state, COUNT(*) AS n FROM application_plans GROUP BY state"
            ).fetchall()
        counts = {row["state"]: row["n"] for row in rows}
        return {
            "preparing": counts.get("preparing", 0),
            "blocked": counts.get("blocked", 0),
            "ready": counts.get("ready", 0),
            "submitted": counts.get("submitted", 0),
            "interviewing": counts.get("interviewing", 0),
            "offer": counts.get("offer", 0),
            "closed": counts.get("closed", 0),
        }

    def list_needs_attention(self, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT
                    p.job_id,
                    p.state,
                    p.payload_json,
                    p.updated_at,
                    j.title,
                    j.company,
                    j.url,
                    v.state AS verification_state,
                    v.detail AS verification_detail
                FROM application_plans p
                JOIN jobs j ON j.id = p.job_id
                LEFT JOIN job_verifications v ON v.job_id = j.id
                WHERE p.state = 'blocked'
                   OR v.state IN ('expired', 'unreachable', 'needs_review')
                ORDER BY p.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        output = []
        for row in rows:
            plan = json.loads(row["payload_json"])
            blocked_questions = [
                item.get("label")
                for item in plan.get("blocked_questions", [])
                if item.get("label")
            ]
            unknown_questions = [
                item.get("label")
                for item in plan.get("unknown_questions", [])
                if item.get("label")
            ]
            reasons = list(plan.get("reasons", []))
            if row["verification_detail"] and row["verification_state"] in {
                "expired",
                "unreachable",
                "needs_review",
            }:
                reasons.append(row["verification_detail"])

            output.append(
                {
                    "job_id": row["job_id"],
                    "title": repair_text(row["title"]),
                    "company": repair_text(row["company"]),
                    "url": row["url"],
                    "state": row["state"],
                    "reasons": reasons,
                    "blocked_questions": blocked_questions,
                    "unknown_questions": unknown_questions,
                    "verification_state": row["verification_state"],
                    "updated_at": row["updated_at"],
                }
            )
        return output
