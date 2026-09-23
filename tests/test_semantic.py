from jobster.brain import CareerBrain
from jobster.models import CareerProfile, Job
from jobster.semantic import SemanticCareerBrain


def test_semantic_without_key_falls_back_to_baseline(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = CareerProfile(profile_id="p", display_name="Candidate")
    job = Job(id="j", title="Designer", company="Acme", description="x", remote=True)
    baseline = CareerBrain().evaluate(profile, job)
    result = SemanticCareerBrain(api_key=None).evaluate(profile, job, baseline)
    assert result == baseline
