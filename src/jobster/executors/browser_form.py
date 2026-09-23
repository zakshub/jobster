from __future__ import annotations

from jobster.ats import detect_ats
from jobster.field_keys import normalize_question
from jobster.models import ApplicationPlan, ApplicationQuestion, Job
from .base import ApplicationExecutor, ExecutorCapability


class BrowserExecutionError(RuntimeError):
    pass


class BrowserFormExecutor(ApplicationExecutor):
    """Conservative Playwright form executor."""

    ats_name = "generic_careers"
    capability = ExecutorCapability(
        ats="generic_careers",
        can_inspect=True,
        can_fill=True,
        can_upload=True,
        can_submit=True,
    )

    def supports(self, job: Job) -> bool:
        return detect_ats(job.url) == self.ats_name

    def _playwright(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserExecutionError(
                "Playwright is required for browser application execution. Install project dependencies and run playwright install chromium."
            ) from exc
        return sync_playwright

    def _captcha_present(self, page) -> bool:
        return bool(page.locator("iframe[title*='captcha' i], iframe[src*='captcha' i], [class*='captcha' i]").count())

    def _inspect_page(self, page) -> list[ApplicationQuestion]:
        questions: list[ApplicationQuestion] = []
        fields = page.locator("input, textarea, select")
        for index in range(fields.count()):
            field = fields.nth(index)
            tag = field.evaluate("el => el.tagName.toLowerCase()")
            input_type = field.get_attribute("type") or tag
            if input_type in {"hidden", "submit", "button", "reset"}:
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

            required = field.get_attribute("required") is not None or field.get_attribute("aria-required") == "true"
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

    def inspect_questions(self, job: Job) -> list[ApplicationQuestion]:
        if not job.url:
            raise BrowserExecutionError("Job has no application URL")

        sync_playwright = self._playwright()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
            if self._captcha_present(page):
                browser.close()
                raise BrowserExecutionError("CAPTCHA detected. Human input is required")
            questions = self._inspect_page(page)
            browser.close()
            return questions

    def execute(self, job: Job, plan: ApplicationPlan) -> dict:
        if not plan.can_submit_automatically:
            raise BrowserExecutionError("Application plan does not authorize automatic submission")
        if not job.url:
            raise BrowserExecutionError("Job has no application URL")

        sync_playwright = self._playwright()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(job.url, wait_until="domcontentloaded", timeout=60000)

            if self._captcha_present(page):
                browser.close()
                raise BrowserExecutionError("CAPTCHA detected. Human input is required")

            questions = self._inspect_page(page)
            by_key = {question.key: question for question in questions}
            filled = []

            for key, value in plan.known_answers.items():
                question = by_key.get(key)
                if not question or not question.selector:
                    continue
                locator = page.locator(question.selector).first
                if question.input_type == "file":
                    locator.set_input_files(value)
                elif question.input_type in {"checkbox", "radio"}:
                    if str(value).lower() in {"true", "yes", "1", "on"}:
                        locator.check()
                elif question.input_type == "select":
                    locator.select_option(label=value)
                else:
                    locator.fill(value)
                filled.append(key)

            submit = page.locator("button[type='submit'], input[type='submit']")
            if submit.count() == 0:
                browser.close()
                raise BrowserExecutionError("No submit control found")

            before_url = page.url
            submit.first.click()
            page.wait_for_timeout(2500)
            body_text = page.locator("body").inner_text().lower()
            confirmations = (
                "application submitted",
                "application has been submitted",
                "thank you for applying",
                "received your application",
            )
            confirmed = any(text in body_text for text in confirmations)
            receipt = {
                "status": "submitted_confirmed" if confirmed else "needs_verification",
                "url_before_submit": before_url,
                "url_after_submit": page.url,
                "filled_keys": filled,
                "ats": self.ats_name,
            }
            browser.close()
            return receipt


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
        raise BrowserExecutionError("Workday execution is inspection only until a dedicated flow is validated")


class GenericCareersExecutor(BrowserFormExecutor):
    """Inspect and prepare ordinary company career forms conservatively.

    Generic company forms vary too much for unattended final submission.
    Jobster may inspect and prepare them, but the final submit action stays
    human-controlled until a site-specific flow has been validated.
    """

    ats_name = "generic_careers"
    capability = ExecutorCapability("generic_careers", True, True, True, False)

    def execute(self, job: Job, plan: ApplicationPlan) -> dict:
        raise BrowserExecutionError(
            "This company career form can be prepared, but final submission still needs a human check"
        )
