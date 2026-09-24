import base64
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path

from jobster.cover_letter import build_email_application
from jobster.gmail_drafts import GmailDraftProvider
from jobster.models import CareerProfile, CareerValue, Job, JobEvaluation, PursuitDecision


def _profile():
    return CareerProfile(
        profile_id="zak",
        display_name="Zak",
        headline="Senior Product Designer",
        portfolio_url="https://portfolio.example",
    )


def _job():
    return Job(
        id="job-1",
        title="Senior Product Designer",
        company="Acme Health",
        description="Design complex healthcare products",
    )


def _evaluation():
    return JobEvaluation(
        job_id="job-1",
        summary="Strong fit",
        eligible=True,
        role_interpretation="Senior product role",
        strong_matches=["healthcare UX", "complex product systems"],
        interest_score=90,
        career_value=CareerValue(),
        pursuit_decision=PursuitDecision.APPLY,
        positioning=["product systems thinker"],
        confidence=0.9,
        next_action="Apply",
    )


def test_contextual_email_uses_job_and_verified_evaluation():
    result = build_email_application(_profile(), _job(), _evaluation())
    assert "Senior Product Designer" in result.subject
    assert "Acme Health" in result.body
    assert "healthcare UX" in result.body
    assert "https://portfolio.example" in result.body


def test_gmail_provider_creates_draft_with_attachment(tmp_path: Path, monkeypatch):
    secret = tmp_path / "client.json"
    token = tmp_path / "token.json"
    resume = tmp_path / "resume.pdf"
    secret.write_text(
        json.dumps({"installed": {"client_id": "id", "client_secret": "secret"}}),
        encoding="utf-8",
    )
    token.write_text(
        json.dumps({"access_token": "token", "expires_at": 99999999999}),
        encoding="utf-8",
    )
    resume.write_bytes(b"resume-content")
    captured = {}

    class Response:
        is_error = False

        def json(self):
            return {"id": "draft-123"}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr("jobster.gmail_drafts.httpx.post", fake_post)
    provider = GmailDraftProvider(secret, token)
    result = provider.create_draft(
        recipient="jobs@example.com",
        subject="Application",
        body="Hello",
        attachment_path=resume,
    )

    assert result["id"] == "draft-123"
    raw = base64.urlsafe_b64decode(captured["json"]["message"]["raw"])
    message = BytesParser(policy=policy.default).parsebytes(raw)
    assert message["To"] == "jobs@example.com"
    assert message["Subject"] == "Application"
    assert any(part.get_filename() == "resume.pdf" for part in message.walk())
