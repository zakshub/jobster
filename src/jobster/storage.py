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
CREATE TABLE IF NOT EXISTS company_watchlist (
    company TEXT PRIMARY KEY,
    watching INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS career_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    reaction TEXT NOT NULL,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    company TEXT,
    role TEXT,
    email TEXT,
    linkedin_url TEXT,
    relationship TEXT NOT NULL DEFAULT 'new',
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS interviews (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    scheduled_at TEXT,
    format TEXT,
    status TEXT NOT NULL DEFAULT 'planned',
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS offers (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    monthly_base REAL,
    bonus TEXT,
    equity TEXT,
    status TEXT NOT NULL DEFAULT 'reviewing',
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS automation_authority (
    action TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0,
    requires_approval INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    job_id TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS career_goals (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    horizon TEXT NOT NULL DEFAULT 'now',
    status TEXT NOT NULL DEFAULT 'active',
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS outreach_drafts (
    id TEXT PRIMARY KEY,
    contact_id TEXT,
    job_id TEXT,
    channel TEXT NOT NULL DEFAULT 'email',
    subject TEXT,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    scheduled_for TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(contact_id) REFERENCES contacts(id),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS star_stories (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    situation TEXT,
    task TEXT,
    action TEXT,
    result TEXT,
    skills_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS application_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    path TEXT NOT NULL,
    label TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE TABLE IF NOT EXISTS watch_rules (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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


    def set_company_watch(self, company: str, watching: bool, note: str | None = None) -> dict:
        company = repair_text(company).strip()
        if not company:
            raise ValueError("Company is required")
        with self.connect() as con:
            con.execute(
                """INSERT INTO company_watchlist(company, watching, note)
                VALUES (?, ?, ?)
                ON CONFLICT(company) DO UPDATE SET
                  watching=excluded.watching,
                  note=COALESCE(excluded.note, company_watchlist.note),
                  updated_at=CURRENT_TIMESTAMP""",
                (company, 1 if watching else 0, note),
            )
        return {"company": company, "watching": watching, "note": note}

    def list_company_summaries(self, limit: int = 200) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT
                    j.company,
                    COUNT(*) AS jobs,
                    MAX(COALESCE(CAST(json_extract(e.payload_json, '$.interest_score') AS INTEGER), 0)) AS best_score,
                    MAX(j.updated_at) AS last_seen,
                    SUM(CASE WHEN e.decision IN ('aggressive_pursuit','high_priority','apply') THEN 1 ELSE 0 END) AS strong_jobs,
                    MAX(COALESCE(w.watching, 0)) AS watching,
                    MAX(w.note) AS note
                FROM jobs j
                LEFT JOIN evaluations e ON e.job_id = j.id
                LEFT JOIN company_watchlist w ON lower(w.company) = lower(j.company)
                GROUP BY j.company
                ORDER BY watching DESC, strong_jobs DESC, best_score DESC, last_seen DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "company": repair_text(row["company"]),
                "jobs": row["jobs"],
                "best_score": row["best_score"] or 0,
                "strong_jobs": row["strong_jobs"] or 0,
                "last_seen": row["last_seen"],
                "watching": bool(row["watching"]),
                "note": row["note"],
            }
            for row in rows
        ]

    def save_feedback(self, job_id: str | None, reaction: str, note: str | None = None) -> dict:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO career_feedback(job_id, reaction, note) VALUES (?, ?, ?)",
                (job_id, reaction, note),
            )
            feedback_id = cur.lastrowid
        payload = {"id": feedback_id, "job_id": job_id, "reaction": reaction, "note": note}
        self.audit("career_feedback_added", payload, job_id=job_id)
        return payload

    def list_feedback(self, limit: int = 200) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT f.id, f.job_id, f.reaction, f.note, f.created_at,
                       j.title, j.company
                FROM career_feedback f
                LEFT JOIN jobs j ON j.id = f.job_id
                ORDER BY f.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_contact(self, payload: dict) -> dict:
        with self.connect() as con:
            con.execute(
                """INSERT INTO contacts(id, name, company, role, email, linkedin_url, relationship, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  name=excluded.name,
                  company=excluded.company,
                  role=excluded.role,
                  email=excluded.email,
                  linkedin_url=excluded.linkedin_url,
                  relationship=excluded.relationship,
                  note=excluded.note,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload["name"],
                    payload.get("company"),
                    payload.get("role"),
                    payload.get("email"),
                    payload.get("linkedin_url"),
                    payload.get("relationship", "new"),
                    payload.get("note"),
                ),
            )
        return payload

    def list_contacts(self, limit: int = 300) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, name, company, role, email, linkedin_url, relationship, note,
                          created_at, updated_at
                   FROM contacts
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_interview(self, payload: dict) -> dict:
        with self.connect() as con:
            con.execute(
                """INSERT INTO interviews(id, job_id, company, title, scheduled_at, format, status, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  job_id=excluded.job_id,
                  company=excluded.company,
                  title=excluded.title,
                  scheduled_at=excluded.scheduled_at,
                  format=excluded.format,
                  status=excluded.status,
                  note=excluded.note,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload.get("job_id"),
                    payload["company"],
                    payload["title"],
                    payload.get("scheduled_at"),
                    payload.get("format"),
                    payload.get("status", "planned"),
                    payload.get("note"),
                ),
            )
        return payload

    def list_interviews(self, limit: int = 200) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, job_id, company, title, scheduled_at, format, status, note,
                          created_at, updated_at
                   FROM interviews
                   ORDER BY
                     CASE WHEN scheduled_at IS NULL THEN 1 ELSE 0 END,
                     scheduled_at ASC,
                     updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_offer(self, payload: dict) -> dict:
        with self.connect() as con:
            con.execute(
                """INSERT INTO offers(id, job_id, company, title, currency, monthly_base, bonus, equity, status, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  job_id=excluded.job_id,
                  company=excluded.company,
                  title=excluded.title,
                  currency=excluded.currency,
                  monthly_base=excluded.monthly_base,
                  bonus=excluded.bonus,
                  equity=excluded.equity,
                  status=excluded.status,
                  note=excluded.note,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload.get("job_id"),
                    payload["company"],
                    payload["title"],
                    payload.get("currency", "USD"),
                    payload.get("monthly_base"),
                    payload.get("bonus"),
                    payload.get("equity"),
                    payload.get("status", "reviewing"),
                    payload.get("note"),
                ),
            )
        return payload

    def list_offers(self, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, job_id, company, title, currency, monthly_base, bonus, equity, status, note,
                          created_at, updated_at
                   FROM offers
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_authority(self) -> dict[str, dict]:
        defaults = {
            "search": {"enabled": True, "requires_approval": False},
            "prepare": {"enabled": True, "requires_approval": False},
            "submit": {"enabled": False, "requires_approval": True},
            "contact": {"enabled": False, "requires_approval": True},
            "follow_up": {"enabled": False, "requires_approval": True},
        }
        with self.connect() as con:
            rows = con.execute(
                "SELECT action, enabled, requires_approval, updated_at FROM automation_authority"
            ).fetchall()
        for row in rows:
            defaults[row["action"]] = {
                "enabled": bool(row["enabled"]),
                "requires_approval": bool(row["requires_approval"]),
                "updated_at": row["updated_at"],
            }
        return defaults

    def set_authority(self, action: str, enabled: bool, requires_approval: bool) -> dict:
        allowed = {"search", "prepare", "submit", "contact", "follow_up"}
        if action not in allowed:
            raise ValueError("Unknown authority action")
        with self.connect() as con:
            con.execute(
                """INSERT INTO automation_authority(action, enabled, requires_approval)
                VALUES (?, ?, ?)
                ON CONFLICT(action) DO UPDATE SET
                  enabled=excluded.enabled,
                  requires_approval=excluded.requires_approval,
                  updated_at=CURRENT_TIMESTAMP""",
                (action, 1 if enabled else 0, 1 if requires_approval else 0),
            )
        result = {
            "action": action,
            "enabled": enabled,
            "requires_approval": requires_approval,
        }
        self.audit("automation_authority_updated", result)
        return result

    def add_notification(self, kind: str, title: str, body: str, job_id: str | None = None) -> dict:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO notifications(kind, title, body, job_id) VALUES (?, ?, ?, ?)",
                (kind, title, body, job_id),
            )
            notification_id = cur.lastrowid
        return {
            "id": notification_id,
            "kind": kind,
            "title": title,
            "body": body,
            "job_id": job_id,
            "is_read": False,
        }

    def list_notifications(self, limit: int = 100, unread_only: bool = False) -> list[dict]:
        query = """SELECT id, kind, title, body, job_id, is_read, created_at
                   FROM notifications"""
        params: tuple = ()
        if unread_only:
            query += " WHERE is_read = 0"
        query += " ORDER BY id DESC LIMIT ?"
        params = (limit,)
        with self.connect() as con:
            rows = con.execute(query, params).fetchall()
        return [
            {
                **dict(row),
                "is_read": bool(row["is_read"]),
            }
            for row in rows
        ]

    def mark_notification_read(self, notification_id: int, is_read: bool = True) -> None:
        with self.connect() as con:
            con.execute(
                "UPDATE notifications SET is_read = ? WHERE id = ?",
                (1 if is_read else 0, notification_id),
            )

    def upsert_goal(self, payload: dict) -> dict:
        with self.connect() as con:
            con.execute(
                """INSERT INTO career_goals(id, label, horizon, status, note)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  label=excluded.label,
                  horizon=excluded.horizon,
                  status=excluded.status,
                  note=excluded.note,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload["label"],
                    payload.get("horizon", "now"),
                    payload.get("status", "active"),
                    payload.get("note"),
                ),
            )
        return payload

    def list_goals(self, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, label, horizon, status, note, created_at, updated_at
                   FROM career_goals
                   ORDER BY
                     CASE status WHEN 'active' THEN 0 ELSE 1 END,
                     updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]


    def upsert_outreach(self, payload: dict) -> dict:
        with self.connect() as con:
            con.execute(
                """INSERT INTO outreach_drafts(id, contact_id, job_id, channel, subject, body, status, scheduled_for)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  contact_id=excluded.contact_id,
                  job_id=excluded.job_id,
                  channel=excluded.channel,
                  subject=excluded.subject,
                  body=excluded.body,
                  status=excluded.status,
                  scheduled_for=excluded.scheduled_for,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload.get("contact_id"),
                    payload.get("job_id"),
                    payload.get("channel", "email"),
                    payload.get("subject"),
                    payload["body"],
                    payload.get("status", "draft"),
                    payload.get("scheduled_for"),
                ),
            )
        return payload

    def list_outreach(self, limit: int = 200) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT o.id, o.contact_id, o.job_id, o.channel, o.subject, o.body,
                          o.status, o.scheduled_for, o.created_at, o.updated_at,
                          c.name AS contact_name, c.company AS contact_company,
                          j.title AS job_title, j.company AS job_company
                   FROM outreach_drafts o
                   LEFT JOIN contacts c ON c.id = o.contact_id
                   LEFT JOIN jobs j ON j.id = o.job_id
                   ORDER BY o.updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_star_story(self, payload: dict) -> dict:
        skills = payload.get("skills") or []
        with self.connect() as con:
            con.execute(
                """INSERT INTO star_stories(id, title, situation, task, action, result, skills_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  title=excluded.title,
                  situation=excluded.situation,
                  task=excluded.task,
                  action=excluded.action,
                  result=excluded.result,
                  skills_json=excluded.skills_json,
                  status=excluded.status,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload["title"],
                    payload.get("situation"),
                    payload.get("task"),
                    payload.get("action"),
                    payload.get("result"),
                    json.dumps(skills),
                    payload.get("status", "active"),
                ),
            )
        return payload

    def list_star_stories(self, limit: int = 200) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, title, situation, task, action, result, skills_json, status,
                          created_at, updated_at
                   FROM star_stories
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            {
                **dict(row),
                "skills": json.loads(row["skills_json"] or "[]"),
            }
            for row in rows
        ]

    def save_application_artifact(
        self,
        job_id: str,
        artifact_type: str,
        path: str,
        label: str | None = None,
    ) -> dict:
        with self.connect() as con:
            cur = con.execute(
                """INSERT INTO application_artifacts(job_id, artifact_type, path, label)
                   VALUES (?, ?, ?, ?)""",
                (job_id, artifact_type, path, label),
            )
            artifact_id = cur.lastrowid
        return {
            "id": artifact_id,
            "job_id": job_id,
            "artifact_type": artifact_type,
            "path": path,
            "label": label,
        }

    def list_application_artifacts(self, job_id: str | None = None, limit: int = 300) -> list[dict]:
        query = """SELECT a.id, a.job_id, a.artifact_type, a.path, a.label, a.created_at,
                          j.title, j.company
                   FROM application_artifacts a
                   LEFT JOIN jobs j ON j.id = a.job_id"""
        params: tuple
        if job_id:
            query += " WHERE a.job_id = ?"
            params = (job_id, limit)
        else:
            params = (limit,)
        query += " ORDER BY a.id DESC LIMIT ?"
        with self.connect() as con:
            rows = con.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def upsert_watch_rule(self, payload: dict) -> dict:
        criteria = payload.get("criteria") or {}
        with self.connect() as con:
            con.execute(
                """INSERT INTO watch_rules(id, label, criteria_json, enabled)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  label=excluded.label,
                  criteria_json=excluded.criteria_json,
                  enabled=excluded.enabled,
                  updated_at=CURRENT_TIMESTAMP""",
                (
                    payload["id"],
                    payload["label"],
                    json.dumps(criteria, sort_keys=True),
                    1 if payload.get("enabled", True) else 0,
                ),
            )
        return payload

    def list_watch_rules(self, limit: int = 100) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, label, criteria_json, enabled, created_at, updated_at
                   FROM watch_rules
                   ORDER BY enabled DESC, updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            {
                **dict(row),
                "criteria": json.loads(row["criteria_json"] or "{}"),
                "enabled": bool(row["enabled"]),
            }
            for row in rows
        ]

    def emergency_stop(self) -> dict:
        actions = ("search", "prepare", "submit", "contact", "follow_up")
        with self.connect() as con:
            for action in actions:
                con.execute(
                    """INSERT INTO automation_authority(action, enabled, requires_approval)
                    VALUES (?, 0, 1)
                    ON CONFLICT(action) DO UPDATE SET
                      enabled=0,
                      requires_approval=1,
                      updated_at=CURRENT_TIMESTAMP""",
                    (action,),
                )
        result = {"stopped": True, "actions": list(actions)}
        self.audit("emergency_stop", result)
        return result
