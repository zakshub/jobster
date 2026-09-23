from jobster.brain import CareerBrain
from jobster.models import CareerProfile, Job
import httpx

from jobster.semantic import SemanticCareerBrain, friendly_semantic_error


def test_semantic_without_key_falls_back_to_baseline(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = CareerProfile(profile_id="p", display_name="Candidate")
    job = Job(id="j", title="Designer", company="Acme", description="x", remote=True)
    baseline = CareerBrain().evaluate(profile, job)
    result = SemanticCareerBrain(api_key=None).evaluate(profile, job, baseline)
    assert result == baseline


def test_friendly_semantic_error_explains_429_rate_limit():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(
        429,
        request=request,
        json={"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}},
    )
    exc = httpx.HTTPStatusError("429", request=request, response=response)
    result = friendly_semantic_error(exc)
    assert result["kind"] == "rate_limit"
    assert "too many" in result["message"].lower()


def test_friendly_semantic_error_explains_credit_limit():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(
        429,
        request=request,
        json={"error": {"type": "insufficient_quota", "code": "credit_balance_exhausted"}},
    )
    exc = httpx.HTTPStatusError("429", request=request, response=response)
    result = friendly_semantic_error(exc)
    assert result["kind"] == "usage_limit"
    assert "credit or spending limit" in result["message"].lower()
