from __future__ import annotations

import asyncio
import os
import uuid
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .answer_bank import load_answer_bank
from .application_packet import build_application_packet
from .intelligence import build_daily_missions, build_evidence_snapshot, build_insights
from .models import Job, JobEvaluation, NegotiationContext
from .negotiation import negotiation_advice
from .recruiter import advise_recruiter_message
from .profile import load_profile
from .quota import SerpApiQuota
from .relevance import score_job_relevance
from .runner import build_sources, run_cycle
from .settings import load_search_config
from .storage import JobsterStore
from .submission_schedule import is_submission_allowed
from .verification import verify_job_url


class CycleController:
    def __init__(self) -> None:
        self._lock = Lock()
        self.running = False
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.last_summary: dict | None = None
        self.last_error: str | None = None
        self.stage = "idle"
        self._sequence = 0
        self._events: deque[dict] = deque(maxlen=600)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "running": self.running,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "last_summary": self.last_summary,
                "last_error": self.last_error,
                "stage": self.stage,
                "last_event_sequence": self._sequence,
            }

    def start(self) -> bool:
        with self._lock:
            if self.running:
                return False
            self.running = True
            self.started_at = datetime.now(timezone.utc).isoformat()
            self.finished_at = None
            self.last_error = None
            self.last_summary = None
            self.stage = "starting"
            self._append_locked(
                "cycle_requested",
                "Research cycle requested from the web console",
                {},
                "info",
            )
            return True

    def _append_locked(
        self,
        event: str,
        message: str,
        payload: dict,
        level: str,
    ) -> dict:
        self._sequence += 1
        item = {
            "sequence": self._sequence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "message": message,
            "payload": payload,
            "level": level,
        }
        self._events.append(item)
        return item

    def emit(
        self,
        event: str,
        payload: dict | None = None,
        *,
        message: str | None = None,
        level: str = "info",
    ) -> None:
        payload = payload or {}
        event_messages = {
            "cycle_started": "Starting targeted opportunity research",
            "source_started": f"Scanning {payload.get('source', 'source')}",
            "source_completed": f"{payload.get('source', 'source')} returned {payload.get('fetched', 0)} jobs",
            "source_failed": f"{payload.get('source', 'source')} failed",
            "discovery_completed": f"Discovery collected {payload.get('deduped', 0)} unique jobs",
            "intake_completed": f"Strict intake admitted {payload.get('admitted', 0)} of {payload.get('raw', 0)} jobs",
            "evaluation_started": f"CareerBrain evaluating {payload.get('title', 'job')} at {payload.get('company', 'company')}",
            "evaluation_completed": f"Finished checking {payload.get('title', 'job')} · {payload.get('interest_score', '—')}/100 · {payload.get('decision', 'pending')}",
            "ai_review_paused": payload.get("reason", "AI job review is temporarily unavailable. Jobster will keep going with its basic review."),
            "application_preflight_started": f"Application preflight for {payload.get('candidates', 0)} pursuit candidates",
            "cycle_completed": f"Research complete · {payload.get('discovered', 0)} relevant jobs",
        }
        with self._lock:
            if event in {"source_started", "source_completed", "discovery_completed"}:
                self.stage = "discovering"
            elif event == "intake_completed":
                self.stage = "filtering"
            elif event in {"evaluation_started", "evaluation_completed", "ai_review_paused"}:
                self.stage = "evaluating"
            elif event == "application_preflight_started":
                self.stage = "preparing"
            elif event == "cycle_completed":
                self.stage = "complete"
            self._append_locked(
                event,
                message or event_messages.get(event, event.replace("_", " ")),
                payload,
                level,
            )

    def events_after(self, sequence: int = 0) -> list[dict]:
        with self._lock:
            return [item for item in self._events if item["sequence"] > sequence]

    def finish(self, summary: dict | None = None, error: str | None = None) -> None:
        with self._lock:
            self.running = False
            self.finished_at = datetime.now(timezone.utc).isoformat()
            self.last_summary = summary
            self.last_error = error
            if error:
                self.stage = "failed"
                self._append_locked(
                    "cycle_failed",
                    f"Research cycle failed · {error}",
                    {"error": error},
                    "error",
                )
            else:
                self.stage = "complete"


cycle_controller = CycleController()


def _paths() -> tuple[Path, Path, Path]:
    return (
        Path(os.getenv("JOBSTER_PROFILE", "private_data/profile.yaml")),
        Path(os.getenv("JOBSTER_SEARCH", "config/search.yaml")),
        Path(os.getenv("JOBSTER_DB", "data/jobster.db")),
    )


def _runtime():
    profile_path, search_path, db_path = _paths()
    profile = load_profile(profile_path)
    config = load_search_config(search_path)
    store = JobsterStore(db_path)
    store.init()
    return profile, config, store


def _quota_payload(config) -> dict:
    budget = config.serpapi_budget
    quota = SerpApiQuota(
        path=budget.state_path,
        monthly_limit=budget.monthly_limit,
        reserve_queries=budget.reserve_queries,
        daily_limit=budget.daily_limit,
        window_days=budget.window_days,
    )
    status = quota.status()
    return {
        "used": status.used_in_window,
        "usable_limit": status.usable_limit,
        "used_today": status.used_today,
        "daily_limit": status.daily_limit,
        "window_started_at": status.window_started_at,
        "window_ends_at": status.window_ends_at,
    }


def _relevant_jobs(profile, config, store: JobsterStore, limit: int = 500) -> tuple[list[dict], int]:
    jobs = store.list_job_summaries(limit=limit)
    if not config.intake.enabled:
        return jobs, 0

    visible: list[dict] = []
    hidden = 0
    for item in jobs:
        result = score_job_relevance(
            profile,
            Job(
                id=item["id"],
                title=item["title"],
                company=item["company"],
                description="",
                location=item.get("location"),
                remote=item.get("remote"),
                source=item.get("source") or "unknown",
                url=item.get("url"),
            ),
        )
        item["intake_score"] = result.score
        item["intake_reason"] = result.reason
        if result.relevant and result.score >= config.intake.min_title_score:
            visible.append(item)
        else:
            hidden += 1
    return visible, hidden


async def _run_cycle_task() -> None:
    try:
        profile, config, store = _runtime()
        sources = build_sources(config)
        summary = await asyncio.to_thread(
            run_cycle,
            profile,
            config,
            store,
            sources,
            cycle_controller.emit,
        )
        cycle_controller.finish(summary=summary)
    except Exception as exc:
        cycle_controller.finish(error=str(exc))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Jobster",
        description="Private career command center",
        version="0.3.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    static_dir = Path(__file__).with_name("webui")
    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(static_dir / "index.html")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest():
        return FileResponse(static_dir / "manifest.webmanifest", media_type="application/manifest+json")

    @app.get("/service-worker.js", include_in_schema=False)
    def service_worker():
        return FileResponse(
            static_dir / "service-worker.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )

    @app.get("/api/status")
    def status():
        profile, config, store = _runtime()
        metrics = store.dashboard_metrics()
        relevant_jobs, hidden = _relevant_jobs(profile, config, store)
        attention = store.list_needs_attention(limit=200)
        pipeline = store.pipeline_counts()
        source_counts = dict(Counter(job["source"] for job in relevant_jobs))
        metrics["jobs"] = len(relevant_jobs)
        metrics["hidden_irrelevant"] = hidden
        metrics["high_priority"] = sum(
            1
            for job in relevant_jobs
            if job.get("decision") in {"high_priority", "aggressive_pursuit"}
        )
        metrics["evaluated"] = sum(1 for job in relevant_jobs if job.get("decision"))
        metrics["needs_you"] = len(attention)

        return {
            "profile": {
                "display_name": profile.display_name,
                "headline": profile.headline,
                "location": profile.location,
                "target_titles": profile.target_titles,
                "target_monthly": profile.compensation.target_monthly,
                "currency": profile.compensation.currency,
                "minimum_monthly": profile.compensation.minimum_monthly,
                "remote_only": profile.remote_only,
            },
            "metrics": metrics,
            "pipeline": pipeline,
            "source_counts": source_counts,
            "intake": {
                "enabled": config.intake.enabled,
                "min_title_score": config.intake.min_title_score,
                "max_per_source": config.intake.max_per_source,
                "max_total": config.intake.max_total,
            },
            "quota": _quota_payload(config),
            "submission": {
                "auto_submit": config.application.auto_submit,
                "window_open": is_submission_allowed(
                    config.application.submission_schedule
                ),
                "timezone": config.application.submission_schedule.timezone,
                "friday_stop_time": config.application.submission_schedule.friday_stop_time,
                "monday_resume_time": config.application.submission_schedule.monday_resume_time,
            },
            "cycle": cycle_controller.snapshot(),
        }

    @app.get("/api/missions")
    def missions():
        profile, _, store = _runtime()
        return build_daily_missions(profile, store)

    @app.get("/api/insights")
    def insights():
        profile, _, store = _runtime()
        return build_insights(profile, store)

    @app.get("/api/evidence")
    def evidence():
        profile, _, _ = _runtime()
        return build_evidence_snapshot(profile)

    @app.get("/api/companies")
    def companies(limit: int = 200):
        _, _, store = _runtime()
        return store.list_company_summaries(limit=min(max(limit, 1), 500))

    @app.post("/api/companies/watch")
    def watch_company(payload: dict):
        _, _, store = _runtime()
        company = str(payload.get("company") or "").strip()
        if not company:
            raise HTTPException(status_code=400, detail="Company is required")
        watching = payload.get("watching", True)
        if not isinstance(watching, bool):
            raise HTTPException(status_code=400, detail="watching must be true or false")
        note = payload.get("note")
        if note is not None and not isinstance(note, str):
            raise HTTPException(status_code=400, detail="note must be text")
        result = store.set_company_watch(company, watching, note)
        store.audit("company_watch_updated", result)
        return result

    @app.get("/api/feedback")
    def feedback(limit: int = 200):
        _, _, store = _runtime()
        return store.list_feedback(limit=min(max(limit, 1), 500))

    @app.post("/api/feedback")
    def add_feedback(payload: dict):
        _, _, store = _runtime()
        reaction = str(payload.get("reaction") or "").strip()
        if not reaction:
            raise HTTPException(status_code=400, detail="Reaction is required")
        if reaction not in {
            "interesting",
            "not_for_me",
            "would_apply",
            "too_generic",
            "salary_too_low",
            "outside_direction",
            "worth_stretching",
            "not_worth_stretching",
            "good_company_bad_role",
        }:
            raise HTTPException(status_code=400, detail="Unknown feedback type")
        job_id = payload.get("job_id")
        if job_id and store.get_job_bundle(str(job_id)) is None:
            raise HTTPException(status_code=404, detail="Job not found")
        note = payload.get("note")
        if note is not None and not isinstance(note, str):
            raise HTTPException(status_code=400, detail="note must be text")
        return store.save_feedback(str(job_id) if job_id else None, reaction, note)

    @app.get("/api/contacts")
    def contacts(limit: int = 300):
        _, _, store = _runtime()
        return store.list_contacts(limit=min(max(limit, 1), 500))

    @app.post("/api/contacts")
    def save_contact(payload: dict):
        _, _, store = _runtime()
        name = str(payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        contact = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "name": name,
            "company": str(payload.get("company") or "").strip() or None,
            "role": str(payload.get("role") or "").strip() or None,
            "email": str(payload.get("email") or "").strip() or None,
            "linkedin_url": str(payload.get("linkedin_url") or "").strip() or None,
            "relationship": str(payload.get("relationship") or "new").strip() or "new",
            "note": str(payload.get("note") or "").strip() or None,
        }
        result = store.upsert_contact(contact)
        store.audit("contact_saved", {"id": result["id"], "name": result["name"]})
        return result

    @app.post("/api/recruiter/advice")
    def recruiter_advice(payload: dict):
        message = str(payload.get("message") or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Paste the recruiter message first")
        return advise_recruiter_message(message).model_dump()

    @app.get("/api/interviews")
    def interviews(limit: int = 200):
        _, _, store = _runtime()
        return store.list_interviews(limit=min(max(limit, 1), 500))

    @app.post("/api/interviews")
    def save_interview(payload: dict):
        _, _, store = _runtime()
        company = str(payload.get("company") or "").strip()
        title = str(payload.get("title") or "").strip()
        if not company or not title:
            raise HTTPException(status_code=400, detail="Company and title are required")
        item = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "job_id": str(payload.get("job_id") or "").strip() or None,
            "company": company,
            "title": title,
            "scheduled_at": str(payload.get("scheduled_at") or "").strip() or None,
            "format": str(payload.get("format") or "").strip() or None,
            "status": str(payload.get("status") or "planned").strip() or "planned",
            "note": str(payload.get("note") or "").strip() or None,
        }
        result = store.upsert_interview(item)
        store.audit("interview_saved", {"id": result["id"], "company": company})
        return result

    @app.get("/api/offers")
    def offers(limit: int = 100):
        _, _, store = _runtime()
        return store.list_offers(limit=min(max(limit, 1), 300))

    @app.post("/api/offers")
    def save_offer(payload: dict):
        _, _, store = _runtime()
        company = str(payload.get("company") or "").strip()
        title = str(payload.get("title") or "").strip()
        if not company or not title:
            raise HTTPException(status_code=400, detail="Company and title are required")
        monthly_base = payload.get("monthly_base")
        if monthly_base not in (None, ""):
            try:
                monthly_base = float(monthly_base)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Monthly base must be a number")
        else:
            monthly_base = None
        item = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "job_id": str(payload.get("job_id") or "").strip() or None,
            "company": company,
            "title": title,
            "currency": str(payload.get("currency") or "USD").strip() or "USD",
            "monthly_base": monthly_base,
            "bonus": str(payload.get("bonus") or "").strip() or None,
            "equity": str(payload.get("equity") or "").strip() or None,
            "status": str(payload.get("status") or "reviewing").strip() or "reviewing",
            "note": str(payload.get("note") or "").strip() or None,
        }
        result = store.upsert_offer(item)
        store.audit("offer_saved", {"id": result["id"], "company": company})
        return result

    @app.post("/api/offers/{offer_id}/advice")
    def offer_advice(offer_id: str, payload: dict | None = None):
        profile, _, store = _runtime()
        offer = next((item for item in store.list_offers(limit=500) if item["id"] == offer_id), None)
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        payload = payload or {}
        context = NegotiationContext(
            current_offer_monthly=offer.get("monthly_base"),
            currency=offer.get("currency") or profile.compensation.currency,
            company_initiated=bool(payload.get("company_initiated", False)),
            interview_rounds=int(payload.get("interview_rounds", 0) or 0),
            urgency_signals=int(payload.get("urgency_signals", 0) or 0),
            strong_positive_signals=int(payload.get("strong_positive_signals", 0) or 0),
            competing_processes=int(payload.get("competing_processes", 0) or 0),
            published_max_monthly=payload.get("published_max_monthly"),
        )
        return negotiation_advice(profile, context).model_dump()

    @app.get("/api/authority")
    def authority():
        _, config, store = _runtime()
        result = store.get_authority()
        result["submit"]["config_auto_submit"] = config.application.auto_submit
        result["submit"]["effective_auto_submit"] = bool(
            config.application.auto_submit
            and result["submit"]["enabled"]
            and not result["submit"]["requires_approval"]
        )
        return result

    @app.post("/api/authority/{action}")
    def update_authority(action: str, payload: dict):
        _, _, store = _runtime()
        enabled = payload.get("enabled")
        requires_approval = payload.get("requires_approval", True)
        if not isinstance(enabled, bool) or not isinstance(requires_approval, bool):
            raise HTTPException(
                status_code=400,
                detail="enabled and requires_approval must be true or false",
            )
        try:
            return store.set_authority(action, enabled, requires_approval)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/notifications")
    def notifications(limit: int = 100, unread_only: bool = False):
        _, _, store = _runtime()
        return store.list_notifications(
            limit=min(max(limit, 1), 300),
            unread_only=unread_only,
        )

    @app.post("/api/notifications/{notification_id}/read")
    def mark_notification(notification_id: int, payload: dict | None = None):
        _, _, store = _runtime()
        is_read = True if payload is None else bool(payload.get("is_read", True))
        store.mark_notification_read(notification_id, is_read)
        return {"id": notification_id, "is_read": is_read}

    @app.get("/api/goals")
    def goals(limit: int = 100):
        _, _, store = _runtime()
        return store.list_goals(limit=min(max(limit, 1), 300))

    @app.post("/api/goals")
    def save_goal(payload: dict):
        _, _, store = _runtime()
        label = str(payload.get("label") or "").strip()
        if not label:
            raise HTTPException(status_code=400, detail="Goal is required")
        item = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "label": label,
            "horizon": str(payload.get("horizon") or "now").strip() or "now",
            "status": str(payload.get("status") or "active").strip() or "active",
            "note": str(payload.get("note") or "").strip() or None,
        }
        result = store.upsert_goal(item)
        store.audit("career_goal_saved", {"id": result["id"], "label": label})
        return result

    @app.get("/api/export")
    def export_data():
        profile, config, store = _runtime()
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "profile": profile.model_dump(mode="json"),
            "settings": {
                "cycle_minutes": config.cycle_minutes,
                "auto_submit": config.application.auto_submit,
            },
            "jobs": store.list_job_summaries(limit=500),
            "applications": store.list_application_summaries(limit=500),
            "feedback": store.list_feedback(limit=500),
            "contacts": store.list_contacts(limit=500),
            "interviews": store.list_interviews(limit=500),
            "offers": store.list_offers(limit=500),
            "goals": store.list_goals(limit=500),
            "outreach": store.list_outreach(limit=500),
            "star_stories": store.list_star_stories(limit=500),
            "artifacts": store.list_application_artifacts(limit=500),
            "watch_rules": store.list_watch_rules(limit=500),
            "authority": store.get_authority(),
            "activity": store.list_activity(limit=1000),
        }
        return JSONResponse(
            payload,
            headers={
                "Content-Disposition": "attachment; filename=jobster-career-export.json"
            },
        )

    @app.get("/api/outreach")
    def outreach(limit: int = 200):
        _, _, store = _runtime()
        return store.list_outreach(limit=min(max(limit, 1), 500))

    @app.post("/api/outreach")
    def save_outreach(payload: dict):
        _, _, store = _runtime()
        body = str(payload.get("body") or "").strip()
        if not body:
            raise HTTPException(status_code=400, detail="Message body is required")
        item = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "contact_id": str(payload.get("contact_id") or "").strip() or None,
            "job_id": str(payload.get("job_id") or "").strip() or None,
            "channel": str(payload.get("channel") or "email").strip() or "email",
            "subject": str(payload.get("subject") or "").strip() or None,
            "body": body,
            "status": str(payload.get("status") or "draft").strip() or "draft",
            "scheduled_for": str(payload.get("scheduled_for") or "").strip() or None,
        }
        result = store.upsert_outreach(item)
        store.audit("outreach_saved", {"id": result["id"], "status": result["status"]}, job_id=result.get("job_id"))
        return result

    @app.get("/api/star-stories")
    def star_stories(limit: int = 200):
        _, _, store = _runtime()
        return store.list_star_stories(limit=min(max(limit, 1), 500))

    @app.post("/api/star-stories")
    def save_star_story(payload: dict):
        _, _, store = _runtime()
        title = str(payload.get("title") or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Story title is required")
        skills = payload.get("skills") or []
        if isinstance(skills, str):
            skills = [item.strip() for item in skills.split(",") if item.strip()]
        item = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "title": title,
            "situation": str(payload.get("situation") or "").strip() or None,
            "task": str(payload.get("task") or "").strip() or None,
            "action": str(payload.get("action") or "").strip() or None,
            "result": str(payload.get("result") or "").strip() or None,
            "skills": skills,
            "status": str(payload.get("status") or "active").strip() or "active",
        }
        result = store.upsert_star_story(item)
        store.audit("star_story_saved", {"id": result["id"], "title": title})
        return result

    @app.get("/api/artifacts")
    def artifacts(job_id: str | None = None, limit: int = 300):
        _, _, store = _runtime()
        return store.list_application_artifacts(
            job_id=job_id,
            limit=min(max(limit, 1), 500),
        )

    @app.get("/api/watch-rules")
    def watch_rules(limit: int = 100):
        _, _, store = _runtime()
        return store.list_watch_rules(limit=min(max(limit, 1), 300))

    @app.post("/api/watch-rules")
    def save_watch_rule(payload: dict):
        _, _, store = _runtime()
        label = str(payload.get("label") or "").strip()
        if not label:
            raise HTTPException(status_code=400, detail="Rule label is required")
        criteria = payload.get("criteria") or {}
        if not isinstance(criteria, dict):
            raise HTTPException(status_code=400, detail="criteria must be an object")
        item = {
            "id": str(payload.get("id") or uuid.uuid4()),
            "label": label,
            "criteria": criteria,
            "enabled": bool(payload.get("enabled", True)),
        }
        result = store.upsert_watch_rule(item)
        store.audit("watch_rule_saved", {"id": result["id"], "label": label})
        return result

    @app.post("/api/emergency-stop")
    def emergency_stop():
        _, _, store = _runtime()
        return store.emergency_stop()

    @app.get("/api/jobs")
    def jobs(limit: int = 100, offset: int = 0, include_irrelevant: bool = False):
        profile, config, store = _runtime()
        if include_irrelevant or not config.intake.enabled:
            return store.list_job_summaries(
                limit=min(max(limit, 1), 500),
                offset=max(offset, 0),
            )
        visible, _ = _relevant_jobs(profile, config, store)
        start = max(offset, 0)
        return visible[start : start + min(max(limit, 1), 500)]

    @app.get("/api/attention")
    def attention(limit: int = 100):
        _, _, store = _runtime()
        return store.list_needs_attention(limit=min(max(limit, 1), 500))

    @app.get("/api/pipeline")
    def pipeline():
        _, _, store = _runtime()
        return store.pipeline_counts()

    @app.get("/api/readiness")
    def readiness():
        profile, config, store = _runtime()
        answers = load_answer_bank(config.application.answer_bank_path)
        verified = [answer for answer in answers if answer.verified]
        automatic = [
            answer
            for answer in verified
            if answer.allow_automatic_use
        ]
        source_count = sum(
            1
            for enabled in (
                config.sources.remoteok.enabled,
                config.sources.remotive.enabled,
                config.sources.weworkremotely.enabled,
                config.sources.himalayas.enabled,
                config.sources.google_jobs.enabled,
                config.sources.web_search.enabled,
            )
            if enabled
        )
        checks = [
            {
                "key": "profile",
                "label": "Career profile",
                "ready": bool(profile.display_name and profile.target_titles),
                "detail": "Your name and target roles are available."
                if profile.display_name and profile.target_titles
                else "Add your name and at least one target role.",
            },
            {
                "key": "answers",
                "label": "Application answers",
                "ready": bool(verified),
                "detail": f"{len(automatic)} approved answers can be used automatically."
                if verified
                else "No approved application answers are available yet.",
            },
            {
                "key": "sources",
                "label": "Job sources",
                "ready": source_count > 0,
                "detail": f"{source_count} job sources are turned on.",
            },
            {
                "key": "advanced_review",
                "label": "Advanced job review",
                "ready": bool(os.getenv("OPENAI_API_KEY")),
                "detail": "Advanced job review is available."
                if os.getenv("OPENAI_API_KEY")
                else "Jobster will use its built-in basic review until this is available.",
            },
            {
                "key": "expanded_search",
                "label": "Expanded web search",
                "ready": bool(os.getenv("SERPAPI_API_KEY"))
                or not (config.sources.google_jobs.enabled or config.sources.web_search.enabled),
                "detail": "Expanded web search is ready."
                if os.getenv("SERPAPI_API_KEY")
                else "Direct job sources still work without expanded web search.",
            },
        ]
        ready_count = sum(1 for check in checks if check["ready"])
        return {
            "checks": checks,
            "ready_count": ready_count,
            "total": len(checks),
            "answer_bank": {
                "total": len(answers),
                "verified": len(verified),
                "automatic": len(automatic),
            },
            "application_sites": [
                {"name": "Greenhouse", "level": "fill_and_submit"},
                {"name": "Lever", "level": "fill_and_submit"},
                {"name": "Ashby", "level": "fill_and_submit"},
                {"name": "Workday", "level": "check_only"},
            ],
            "auto_apply": config.application.auto_submit,
            "submission_window_open": is_submission_allowed(
                config.application.submission_schedule
            ),
            "pipeline": store.pipeline_counts(),
        }

    @app.get("/api/settings")
    def user_settings():
        profile, config, _ = _runtime()
        return {
            "job_search": {
                "cycle_minutes": config.cycle_minutes,
                "target_titles": profile.target_titles,
                "remote_only": profile.remote_only,
                "minimum_monthly": profile.compensation.minimum_monthly,
                "target_monthly": profile.compensation.target_monthly,
                "currency": profile.compensation.currency,
            },
            "relevance_filter": {
                "enabled": config.intake.enabled,
                "minimum_match": config.intake.min_title_score,
                "max_per_source": config.intake.max_per_source,
                "max_per_search": config.intake.max_total,
            },
            "applications": {
                "auto_apply": config.application.auto_submit,
                "max_per_search": config.application.max_submissions_per_cycle,
                "timezone": config.application.submission_schedule.timezone,
                "friday_stop": config.application.submission_schedule.friday_stop_time,
                "monday_resume": config.application.submission_schedule.monday_resume_time,
            },
        }

    @app.get("/api/jobs/{job_id}")
    def job_detail(job_id: str):
        _, _, store = _runtime()
        result = store.get_job_bundle(job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return result

    @app.post("/api/jobs/{job_id}/preference")
    def update_job_preference(job_id: str, payload: dict):
        _, _, store = _runtime()
        if store.get_job_bundle(job_id) is None:
            raise HTTPException(status_code=404, detail="Job not found")

        allowed = {"saved", "dismissed", "note"}
        unexpected = set(payload) - allowed
        if unexpected:
            raise HTTPException(
                status_code=400,
                detail="Only saved, dismissed, and note can be changed.",
            )

        saved = payload.get("saved")
        dismissed = payload.get("dismissed")
        note = payload.get("note")
        if saved is not None and not isinstance(saved, bool):
            raise HTTPException(status_code=400, detail="saved must be true or false")
        if dismissed is not None and not isinstance(dismissed, bool):
            raise HTTPException(status_code=400, detail="dismissed must be true or false")
        if note is not None and not isinstance(note, str):
            raise HTTPException(status_code=400, detail="note must be text")
        if isinstance(note, str):
            note = note.strip()[:2000] or ""

        result = store.save_job_preference(
            job_id,
            saved=saved,
            dismissed=dismissed,
            note=note,
        )
        store.audit("job_preference_updated", result, job_id=job_id)
        return result

    @app.post("/api/jobs/{job_id}/verify")
    async def verify_job(job_id: str):
        _, _, store = _runtime()
        bundle = store.get_job_bundle(job_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Job not found")
        cycle_controller.emit(
            "verification_started",
            {"job_id": job_id, "title": bundle["job"]["title"]},
            message=f"Verifying live source · {bundle['job']['title']}",
        )
        result = await asyncio.to_thread(verify_job_url, bundle["job"].get("url"))
        payload = result.as_dict()
        store.save_job_verification(job_id, payload)
        store.audit("job_verified", payload, job_id=job_id)
        cycle_controller.emit(
            "verification_completed",
            {"job_id": job_id, **payload},
            message=f"Verification result · {result.state}",
            level="error" if result.state in {"expired", "unreachable"} else "info",
        )
        return payload

    @app.get("/api/applications")
    def applications(limit: int = 100):
        _, _, store = _runtime()
        return store.list_application_summaries(limit=min(max(limit, 1), 500))

    @app.get("/api/activity")
    def activity(limit: int = 100):
        _, _, store = _runtime()
        return store.list_activity(limit=min(max(limit, 1), 500))

    @app.get("/api/terminal")
    def terminal(after: int = 0):
        return {
            "cycle": cycle_controller.snapshot(),
            "events": cycle_controller.events_after(max(after, 0)),
        }

    @app.post("/api/cycles")
    async def start_cycle():
        if not cycle_controller.start():
            return {"started": False, "reason": "cycle_already_running"}
        asyncio.create_task(_run_cycle_task())
        return {"started": True, "cycle": cycle_controller.snapshot()}

    @app.get("/api/cycles/current")
    def current_cycle():
        return cycle_controller.snapshot()

    @app.post("/api/jobs/{job_id}/prepare")
    async def prepare_job(job_id: str):
        profile, _, store = _runtime()
        bundle = store.get_job_bundle(job_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if not bundle.get("evaluation"):
            raise HTTPException(status_code=409, detail="Job has not been evaluated")

        verification = await asyncio.to_thread(verify_job_url, bundle["job"].get("url"))
        verification_payload = verification.as_dict()
        store.save_job_verification(job_id, verification_payload)
        if verification.state in {"expired", "unreachable"}:
            raise HTTPException(
                status_code=409,
                detail=f"Application preparation stopped: source is {verification.state}",
            )

        job = Job.model_validate(bundle["job"])
        evaluation = JobEvaluation.model_validate(bundle["evaluation"])
        output = Path("artifacts")
        result = build_application_packet(profile, job, evaluation, output)
        if result.get("resume_markdown"):
            store.save_application_artifact(
                job_id,
                "resume",
                result["resume_markdown"],
                "Tailored resume",
            )
        if result.get("decision_summary"):
            store.save_application_artifact(
                job_id,
                "decision_summary",
                result["decision_summary"],
                "CareerBrain decision summary",
            )
        store.audit("application_packet_prepared_from_ui", result, job_id=job_id)
        return {**result, "verification": verification_payload}

    return app


app = create_app()


def run_web(host: str = "127.0.0.1", port: int = 8765, reload: bool = False) -> None:
    import uvicorn

    uvicorn.run(
        "jobster.webapp:app",
        host=host,
        port=port,
        reload=reload,
    )
