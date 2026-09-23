from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .application_packet import build_application_packet
from .profile import load_profile
from .quota import SerpApiQuota
from .runner import build_sources, run_cycle
from .settings import load_search_config
from .storage import JobsterStore
from .submission_schedule import is_submission_allowed


class CycleController:
    def __init__(self) -> None:
        self._lock = Lock()
        self.running = False
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.last_summary: dict | None = None
        self.last_error: str | None = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "running": self.running,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "last_summary": self.last_summary,
                "last_error": self.last_error,
            }

    def start(self) -> bool:
        with self._lock:
            if self.running:
                return False
            self.running = True
            self.started_at = datetime.now(timezone.utc).isoformat()
            self.last_error = None
            return True

    def finish(self, summary: dict | None = None, error: str | None = None) -> None:
        with self._lock:
            self.running = False
            self.finished_at = datetime.now(timezone.utc).isoformat()
            self.last_summary = summary
            self.last_error = error


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
        )
        cycle_controller.finish(summary=summary)
    except Exception as exc:  # UI must report failures instead of killing server.
        cycle_controller.finish(error=str(exc))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Jobster",
        description="Private career command center",
        version="0.2.0",
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
        return {
            "profile": {
                "display_name": profile.display_name,
                "headline": profile.headline,
                "location": profile.location,
                "target_titles": profile.target_titles,
                "target_monthly": profile.compensation.target_monthly,
                "currency": profile.compensation.currency,
            },
            "metrics": store.dashboard_metrics(),
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
    def jobs(limit: int = 100, offset: int = 0):
        _, _, store = _runtime()
        return store.list_job_summaries(limit=min(max(limit, 1), 500), offset=max(offset, 0))

    @app.get("/api/jobs/{job_id}")
    def job_detail(job_id: str):
        _, _, store = _runtime()
        result = store.get_job_bundle(job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return result

    @app.get("/api/applications")
    def applications(limit: int = 100):
        _, _, store = _runtime()
        return store.list_application_summaries(limit=min(max(limit, 1), 500))

    @app.get("/api/activity")
    def activity(limit: int = 100):
        _, _, store = _runtime()
        return store.list_activity(limit=min(max(limit, 1), 500))

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
    def prepare_job(job_id: str):
        profile, _, store = _runtime()
        bundle = store.get_job_bundle(job_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if not bundle.get("evaluation"):
            raise HTTPException(status_code=409, detail="Job has not been evaluated")

        from .models import Job, JobEvaluation

        job = Job.model_validate(bundle["job"])
        evaluation = JobEvaluation.model_validate(bundle["evaluation"])
        output = Path("artifacts")
        result = build_application_packet(profile, job, evaluation, output)
        store.audit("application_packet_prepared_from_ui", result, job_id=job_id)
        return result

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
