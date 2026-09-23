from __future__ import annotations

import re
from pathlib import Path

from jobster.ats import detect_ats
from jobster.field_keys import normalize_question
from jobster.models import ApplicationPlan, ApplicationQuestion, Job
from .base import ApplicationExecutor, ExecutorCapability


class BrowserExecutionError(RuntimeError):
    pass


_FINAL_ACTION_WORDS = (
    "submit application",
    "submit",
    "apply now",
    "apply",
    "finish application",
    "complete application",
    "send application",
)

_NEXT_ACTION_WORDS = (
    "next",
    "continue",
    "save and continue",
    "review",
    "review application",
    "proceed",
)


def classify_form_action(label: str) -> str:
    """Classify a button label without clicking it.

    The executor uses this to avoid treating a harmless "Next" button as the
    final application submission.
    """
    low = re.sub(r"\s+", " ", (label or "").strip().lower())
    if not low:
        return "other"
    if low in _FINAL_ACTION_WORDS:
        return "final"
    if low in _NEXT_ACTION_WORDS:
        return "next"
    if any(low.startswith(f"{value} ") for value in _FINAL_ACTION_WORDS):
        return "final"
    if any(low.startswith(f"{value} ") for value in _NEXT_ACTION_WORDS):
        return "next"
    return "other"


class BrowserFormExecutor(ApplicationExecutor):
    """Conservative Playwright form executor.

    Supported ATS-specific subclasses may submit when all policy gates allow
    it. The executor handles simple multi-page flows but stops whenever a new
    required question, CAPTCHA, login, or unexpected page state appears.
    """

    ats_name = "generic_careers"
    capability = ExecutorCapability(
        ats="generic_careers",
        can_inspect=True,
        can_fill=True,
        can_upload=True,
        can_submit=True,
    )
    max_steps = 8

    def supports(self, job: Job) -> bool:
        return detect_ats(job.url) == self.ats_name

    def _playwright(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserExecutionError(
                "Browser support is not installed. Install project dependencies and run playwright install chromium."
            ) from exc
        return sync_playwright

    def _captcha_present(self, page) -> bool:
        return bool(
            page.locator(
                "iframe[title*='captcha' i], iframe[src*='captcha' i], "
                "[class*='captcha' i], [id*='captcha' i]"
            ).count()
        )

    def _login_present(self, page) -> bool:
        password = page.locator("input[type='password']")
        for index in range(password.count()):
            try:
                if password.nth(index).is_visible():
                    return True
            except Exception:
                continue
        return False

    def _inspect_page(self, page) -> list[ApplicationQuestion]:
        questions: list[ApplicationQuestion] = []
        fields = page.locator("input, textarea, select")
        for index in range(fields.count()):
            field = fields.nth(index)
            try:
                if not field.is_visible():
                    continue
            except Exception:
                pass

            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = (field.get_attribute("type") or tag).lower()
            if input_type in {"hidden", "submit", "button", "reset", "image"}:
                continue

            field_id = field.get_attribute("id")
            name = field.get_attribute("name")
            aria = field.get_attribute("aria-label")
            placeholder = field.get_attribute("placeholder")

            label = ""
            if field_id:
                label_node = page.locator(f"label[for='{field_id}']")
                if label_node.count():
                    label = label_node.first.inner_text().strip()
            if not label:
                parent_label = field.locator("xpath=ancestor::label[1]")
                if parent_label.count():
                    label = parent_label.first.inner_text().strip()
            if not label:
                label = aria or placeholder or name or field_id or f"field_{index}"

            selector = None
            if field_id:
                selector = f"#{field_id}"
            elif name:
                selector = f"[name='{name}']"

            required = (
                field.get_attribute("required") is not None
                or field.get_attribute("aria-required") == "true"
            )
            options = field.locator("option").all_inner_texts() if tag == "select" else []

            questions.append(
                ApplicationQuestion(
                    key=normalize_question(label),
                    label=label,
                    required=required,
                    input_type=input_type,
                    options=options,
                    selector=selector,
                )
            )
        return questions

    def _control_text(self, control) -> str:
        try:
            tag = control.evaluate("el => el.tagName.toLowerCase()")
        except Exception:
            tag = ""
        if tag == "input":
            return (
                control.get_attribute("value")
                or control.get_attribute("aria-label")
                or ""
            ).strip()
        try:
            text = control.inner_text().strip()
        except Exception:
            text = ""
        return text or (control.get_attribute("aria-label") or "").strip()

    def _find_action(self, page, kind: str):
        controls = page.locator(
            "button, input[type='submit'], input[type='button'], [role='button']"
        )
        candidates = []
        for index in range(controls.count()):
            control = controls.nth(index)
            try:
                if not control.is_visible() or not control.is_enabled():
                    continue
            except Exception:
                continue
            label = self._control_text(control)
            if classify_form_action(label) == kind:
                # Prefer exact, short labels over verbose controls.
                candidates.append((len(label), control, label))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1], candidates[0][2]

    def _fill_question(self, page, question: ApplicationQuestion, value: str) -> bool:
        if not question.selector:
            return False
        locator = page.locator(question.selector).first
        try:
            if not locator.is_visible():
                return False
        except Exception:
            pass

        input_type = question.input_type.lower()
        try:
            if input_type == "file":
                path = Path(str(value)).expanduser()
                if not path.exists():
                    return False
                locator.set_input_files(str(path))
            elif input_type == "checkbox":
                truthy = str(value).strip().lower() in {"true", "yes", "1", "on"}
                if truthy:
                    locator.check()
                else:
                    locator.uncheck()
            elif input_type == "radio":
                group = page.locator(question.selector)
                selected = False
                for index in range(group.count()):
                    option = group.nth(index)
                    option_value = (option.get_attribute("value") or "").strip()
                    option_label = ""
                    option_id = option.get_attribute("id")
                    if option_id:
                        label_node = page.locator(f"label[for='{option_id}']")
                        if label_node.count():
                            option_label = label_node.first.inner_text().strip()
                    if str(value).strip().lower() in {
                        option_value.lower(),
                        option_label.lower(),
                    }:
                        option.check()
                        selected = True
                        break
                if not selected and str(value).strip().lower() in {"true", "yes", "1", "on"}:
                    locator.check()
            elif input_type == "select":
                try:
                    locator.select_option(label=str(value))
                except Exception:
                    locator.select_option(value=str(value))
            else:
                locator.fill(str(value))
            return True
        except Exception:
            return False

    def _fill_current_page(
        self,
        page,
        questions: list[ApplicationQuestion],
        plan: ApplicationPlan,
    ) -> tuple[list[str], list[str]]:
        filled: list[str] = []
        missing_required: list[str] = []

        for question in questions:
            key = normalize_question(question.key or question.label)
            answer = plan.known_answers.get(key)
            if answer is None:
                answer = plan.known_answers.get(question.key)

            if answer is None:
                if question.required:
                    missing_required.append(question.label)
                continue

            if self._fill_question(page, question, answer):
                filled.append(key)
            elif question.required:
                missing_required.append(question.label)

        # Preserve order while removing duplicate radio/checkbox group labels.
        missing_required = list(dict.fromkeys(missing_required))
        return filled, missing_required

    def _page_signature(self, page, questions: list[ApplicationQuestion]) -> str:
        keys = "|".join(sorted({question.key for question in questions}))
        return f"{page.url}|{keys}"

    def _wait_after_click(self, page) -> None:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(900)

    def _success_detected(self, page) -> bool:
        try:
            body_text = page.locator("body").inner_text().lower()
        except Exception:
            body_text = ""
        confirmations = (
            "application submitted",
            "application has been submitted",
            "thank you for applying",
            "thanks for applying",
            "received your application",
            "application received",
            "we've received your application",
            "we have received your application",
        )
        return any(text in body_text for text in confirmations)

    def inspect_questions(self, job: Job) -> list[ApplicationQuestion]:
        if not job.url:
            raise BrowserExecutionError("Job has no application URL")

        sync_playwright = self._playwright()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
                if self._captcha_present(page):
                    raise BrowserExecutionError(
                        "This application page has a CAPTCHA. A human check is required."
                    )
                if self._login_present(page):
                    raise BrowserExecutionError(
                        "This application page requires a login. A human check is required."
                    )
                return self._inspect_page(page)
            finally:
                browser.close()

    def execute(self, job: Job, plan: ApplicationPlan) -> dict:
        if not plan.can_submit_automatically:
            raise BrowserExecutionError(
                "This application is not authorized for automatic final submission."
            )
        if not job.url:
            raise BrowserExecutionError("Job has no application URL")

        sync_playwright = self._playwright()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            trace: list[dict] = []
            all_filled: list[str] = []
            try:
                page.goto(job.url, wait_until="domcontentloaded", timeout=60000)

                for step in range(1, self.max_steps + 1):
                    if self._captcha_present(page):
                        return {
                            "status": "human_required",
                            "reason": "CAPTCHA detected",
                            "ats": self.ats_name,
                            "step": step,
                            "trace": trace,
                        }
                    if self._login_present(page):
                        return {
                            "status": "human_required",
                            "reason": "Login required",
                            "ats": self.ats_name,
                            "step": step,
                            "trace": trace,
                        }

                    questions = self._inspect_page(page)
                    signature_before = self._page_signature(page, questions)
                    filled, missing = self._fill_current_page(page, questions, plan)
                    all_filled.extend(filled)
                    trace.append(
                        {
                            "step": step,
                            "url": page.url,
                            "questions": len(questions),
                            "filled_keys": filled,
                        }
                    )

                    if missing:
                        return {
                            "status": "blocked_new_question",
                            "reason": "A later page contains required questions without approved answers",
                            "new_required_questions": missing,
                            "ats": self.ats_name,
                            "step": step,
                            "trace": trace,
                        }

                    final_action = self._find_action(page, "final")
                    next_action = self._find_action(page, "next")

                    if final_action is not None:
                        control, label = final_action
                        before_url = page.url
                        control.click()
                        self._wait_after_click(page)
                        confirmed = self._success_detected(page)

                        screenshot_path = None
                        if confirmed:
                            safe_job_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", job.id)
                            target = Path("artifacts") / "application_receipts"
                            target.mkdir(parents=True, exist_ok=True)
                            screenshot = target / f"{safe_job_id}_submitted.png"
                            try:
                                page.screenshot(path=str(screenshot), full_page=True)
                                screenshot_path = str(screenshot)
                            except Exception:
                                screenshot_path = None

                        return {
                            "status": "submitted_confirmed" if confirmed else "needs_verification",
                            "reason": (
                                "Submission confirmation detected"
                                if confirmed
                                else "Final action was clicked but a clear confirmation was not detected"
                            ),
                            "final_action_label": label,
                            "url_before_submit": before_url,
                            "url_after_submit": page.url,
                            "filled_keys": list(dict.fromkeys(all_filled)),
                            "ats": self.ats_name,
                            "steps": step,
                            "trace": trace,
                            "confirmation_screenshot": screenshot_path,
                        }

                    if next_action is not None:
                        control, label = next_action
                        control.click()
                        self._wait_after_click(page)
                        next_questions = self._inspect_page(page)
                        signature_after = self._page_signature(page, next_questions)
                        if signature_after == signature_before:
                            return {
                                "status": "needs_verification",
                                "reason": f"The form did not clearly advance after '{label}'",
                                "ats": self.ats_name,
                                "step": step,
                                "trace": trace,
                            }
                        continue

                    return {
                        "status": "needs_verification",
                        "reason": "No clear Next or final Submit control was found",
                        "ats": self.ats_name,
                        "step": step,
                        "trace": trace,
                    }

                return {
                    "status": "needs_verification",
                    "reason": f"The application exceeded Jobster's {self.max_steps}-step safety limit",
                    "ats": self.ats_name,
                    "steps": self.max_steps,
                    "trace": trace,
                }
            finally:
                browser.close()


class GreenhouseExecutor(BrowserFormExecutor):
    ats_name = "greenhouse"
    capability = ExecutorCapability("greenhouse", True, True, True, True)


class LeverExecutor(BrowserFormExecutor):
    ats_name = "lever"
    capability = ExecutorCapability("lever", True, True, True, True)


class AshbyExecutor(BrowserFormExecutor):
    ats_name = "ashby"
    capability = ExecutorCapability("ashby", True, True, True, True)


class WorkdayExecutor(BrowserFormExecutor):
    ats_name = "workday"
    capability = ExecutorCapability("workday", True, False, False, False)

    def execute(self, job: Job, plan: ApplicationPlan) -> dict:
        raise BrowserExecutionError(
            "Workday can be inspected, but final submission still needs a dedicated validated flow."
        )


class GenericCareersExecutor(BrowserFormExecutor):
    """Inspect and prepare ordinary company career forms conservatively."""

    ats_name = "generic_careers"
    capability = ExecutorCapability("generic_careers", True, True, True, False)

    def execute(self, job: Job, plan: ApplicationPlan) -> dict:
        raise BrowserExecutionError(
            "This company career form can be prepared, but final submission still needs a human check."
        )
