from __future__ import annotations

import asyncio
import os
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .application_packet import build_application_packet
from .models import Job, JobEvaluation
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
            "evaluation_completed": f"Scored {payload.get('title', 'job')} · {payload.get('interest_score', '—')}/100 · {payload.get('decision', 'pending')}",
            "application_preflight_started": f"Application preflight for {payload.get('candidates', 0)} pursuit candidates",
            "cycle_completed": f"Research complete · {payload.get('discovered', 0)} relevant jobs",
        }
        with self._lock:
            if event in {"source_started", "source_completed", "discovery_completed"}:
                self.stage = "discovering"
            elif event == "intake_completed":
                self.stage = "filtering"
            elif event in {"evaluation_started", "evaluation_completed"}:
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

    @app.get("/api/status")
    def status():
        profile, config, store = _runtime()
        metrics = store.dashboard_metrics()
        relevant_jobs, hidden = _relevant_jobs(profile, config, store)
        source_counts = dict(Counter(job["source"] for job in relevant_jobs))
        metrics["jobs"] = len(relevant_jobs)
        metrics["hidden_irrelevant"] = hidden
        metrics["high_priority"] = sum(
            1
            for job in relevant_jobs
            if job.get("decision") in {"high_priority", "aggressive_pursuit"}
        )
        metrics["evaluated"] = sum(1 for job in relevant_jobs if job.get("decision"))

        return {
            "profile": {
                "display_name": profile.display_name,
                "headline": profile.headline,
                "location": profile.location,
                "target_titles": profile.target_titles,
                "target_monthly": profile.compensation.target_monthly,
                "currency": profile.compensation.currency,
            },
            "metrics": metrics,
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

    @app.get("/api/jobs/{job_id}")
    def job_detail(job_id: str):
        _, _, store = _runtime()
        result = store.get_job_bundle(job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Job not found")
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
