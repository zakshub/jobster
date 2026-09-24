from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .application_policy import build_application_plan
from .executors.browser_form import BrowserFormExecutor, classify_form_action
from .models import ApplicationAnswer, Job


TERMINAL_REVIEW_STATES = {"submitted", "cancelled", "failed", "interrupted"}


@dataclass
class ReviewSnapshot:
    job_id: str
    status: str = "launching"
    message: str = "Opening the application in a visible browser."
    current_url: str | None = None
    filled_fields: list[str] = field(default_factory=list)
    missing_questions: list[str] = field(default_factory=list)
    email_recipient: str | None = None
    final_action_label: str | None = None
    updated_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "message": self.message,
            "current_url": self.current_url,
            "filled_fields": list(self.filled_fields),
            "missing_questions": list(self.missing_questions),
            "email_recipient": self.email_recipient,
            "final_action_label": self.final_action_label,
            "updated_at": self.updated_at,
        }


class ReviewSession:
    def __init__(
        self,
        job: Job,
        answers: list[ApplicationAnswer],
        browser_profile_path: str | Path,
    ):
        self.job = job
        self.answers = answers
        self.browser_profile_path = Path(browser_profile_path)
        self._snapshot = ReviewSnapshot(job_id=job.id)
        self._lock = threading.Lock()
        self._commands: queue.Queue[str] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def command(self, value: str) -> None:
        self._commands.put(value)

    def snapshot(self) -> dict:
        with self._lock:
            return self._snapshot.as_dict()

    def _set(self, status: str, message: str, **values) -> None:
        with self._lock:
            self._snapshot.status = status
            self._snapshot.message = message
            self._snapshot.updated_at = time.time()
            for key, value in values.items():
                setattr(self._snapshot, key, value)

    def _visible_apply_controls(self, page):
        controls = page.locator("a, button, input[type='button'], input[type='submit'], [role='button']")
        found = []
        executor = BrowserFormExecutor()
        for index in range(controls.count()):
            control = controls.nth(index)
            try:
                if not control.is_visible() or not control.is_enabled():
                    continue
            except Exception:
                continue
            label = executor._control_text(control)
            low = label.strip().lower()
            if "easy apply" in low or classify_form_action(label) == "final":
                found.append((control, label))
        return found

    def _activate_page_after_click(self, context, page):
        try:
            page.wait_for_timeout(1000)
        except Exception:
            pass
        live_pages = [candidate for candidate in context.pages if not candidate.is_closed()]
        return live_pages[-1] if live_pages else page

    def _is_route_control(self, control) -> bool:
        """Only click Apply automatically when it cannot submit a form."""
        try:
            details = control.evaluate(
                "el => ({tag: el.tagName.toLowerCase(), inForm: !!el.closest('form'), href: el.href || ''})"
            )
            return not details.get("inForm") and (
                details.get("tag") == "a" or bool(details.get("href"))
            )
        except Exception:
            return False

    def _prepare(self, context, page):
        executor = BrowserFormExecutor()
        for _ in range(executor.max_steps):
            if page.is_closed():
                self._set("interrupted", "The application window was closed.")
                return page
            self._set(
                "preparing",
                "Checking this application page and filling verified answers.",
                current_url=page.url,
                missing_questions=[],
                final_action_label=None,
            )

            if executor._captcha_present(page):
                self._set(
                    "needs_user",
                    "Complete the CAPTCHA in the open browser, then choose Continue filling.",
                    current_url=page.url,
                )
                return page
            if executor._login_present(page):
                self._set(
                    "needs_login",
                    "Log in, create the required account, or complete verification in the open browser, then choose Continue filling.",
                    current_url=page.url,
                )
                return page

            mail_links = page.locator("a[href^='mailto:']")
            if mail_links.count():
                href = mail_links.first.get_attribute("href") or ""
                recipient = href.split(":", 1)[-1].split("?", 1)[0].strip()
                if recipient:
                    self._set(
                        "email_available",
                        "This employer accepts applications by email. Jobster can save a Gmail draft.",
                        current_url=page.url,
                        email_recipient=recipient,
                    )
                    return page

            questions = executor._inspect_page(page)
            visible_apply = self._visible_apply_controls(page)
            is_linkedin = "linkedin.com" in page.url.lower()
            easy_apply = any("easy apply" in label.lower() for _, label in visible_apply)
            if is_linkedin and easy_apply:
                self._set(
                    "needs_user",
                    "LinkedIn Easy Apply is open for manual completion. Jobster will not automate LinkedIn controls.",
                    current_url=page.url,
                )
                return page

            # A listing page often contains only a search field. In that case,
            # Apply is navigation to the real form rather than final submission.
            substantive_questions = [
                question for question in questions
                if question.input_type.lower() not in {"search", "hidden"}
            ]
            if len(substantive_questions) < 2 and visible_apply:
                if len(visible_apply) > 1:
                    self._set(
                        "needs_user",
                        "Several Apply choices are visible. Choose the correct role in the browser, then Continue filling.",
                        current_url=page.url,
                    )
                    return page
                control, label = visible_apply[0]
                if self._is_route_control(control):
                    control.click()
                    page = self._activate_page_after_click(context, page)
                    continue
                self._set(
                    "awaiting_review",
                    "Review the application in the open browser and click the final action yourself.",
                    current_url=page.url,
                    final_action_label=label,
                )
                return page

            plan = build_application_plan(
                self.job,
                questions,
                self.answers,
                allow_final_submit=False,
            )
            filled, missing = executor._fill_current_page(
                page,
                questions,
                plan,
                preserve_existing=True,
            )
            if missing:
                self._set(
                    "needs_input",
                    "Complete the highlighted required questions, then choose Continue filling.",
                    current_url=page.url,
                    filled_fields=filled,
                    missing_questions=missing,
                )
                return page

            final_action = executor._find_action(page, "final")
            if final_action is not None:
                _, label = final_action
                self._set(
                    "awaiting_review",
                    "The application is filled. Review it in the open browser and click Submit yourself.",
                    current_url=page.url,
                    filled_fields=filled,
                    final_action_label=label,
                )
                return page

            next_action = executor._find_action(page, "next")
            if next_action is not None:
                control, _ = next_action
                control.click()
                page = self._activate_page_after_click(context, page)
                continue

            self._set(
                "needs_user",
                "Jobster could not identify the next safe action. Continue manually in the open browser.",
                current_url=page.url,
                filled_fields=filled,
            )
            return page

        self._set(
            "needs_user",
            "The application exceeded Jobster's safe navigation limit. Continue manually.",
            current_url=page.url,
        )
        return page

    def _run(self) -> None:
        try:
            from playwright.sync_api import sync_playwright

            self.browser_profile_path.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.browser_profile_path),
                    headless=False,
                    no_viewport=True,
                    args=["--start-maximized"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(self.job.url, wait_until="domcontentloaded", timeout=60000)
                page = self._prepare(context, page)

                while True:
                    command = self._commands.get()
                    if command == "close":
                        self._set("cancelled", "The application review session was closed.")
                        context.close()
                        return
                    if page.is_closed():
                        self._set("interrupted", "The application window was closed.")
                        context.close()
                        return
                    if command == "continue":
                        page = self._prepare(context, page)
                    elif command == "check":
                        executor = BrowserFormExecutor()
                        if executor._success_detected(page):
                            self._set(
                                "submitted",
                                "The application site shows a submission confirmation.",
                                current_url=page.url,
                            )
                        else:
                            self._set(
                                "unconfirmed",
                                "Jobster cannot confirm submission yet. Check the open browser and try again.",
                                current_url=page.url,
                            )
        except Exception as exc:
            self._set("failed", f"Application browser failed: {exc}")


class ReviewSessionManager:
    def __init__(self):
        self._sessions: dict[str, ReviewSession] = {}
        self._lock = threading.Lock()

    def start(
        self,
        job: Job,
        answers: list[ApplicationAnswer],
        browser_profile_path: str | Path,
    ) -> dict:
        with self._lock:
            existing = self._sessions.get(job.id)
            if existing and existing.snapshot()["status"] not in TERMINAL_REVIEW_STATES:
                return existing.snapshot()
            active = [
                session for session in self._sessions.values()
                if session.snapshot()["status"] not in TERMINAL_REVIEW_STATES
            ]
            if active:
                raise RuntimeError("Finish or close the current application review before opening another one")
            session = ReviewSession(job, answers, browser_profile_path)
            self._sessions[job.id] = session
            session.start()
            return session.snapshot()

    def get(self, job_id: str) -> dict | None:
        session = self._sessions.get(job_id)
        return session.snapshot() if session else None

    def command(self, job_id: str, command: str) -> dict:
        session = self._sessions.get(job_id)
        if session is None:
            raise KeyError(job_id)
        session.command(command)
        return session.snapshot()
