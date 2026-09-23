from jobster.settings import SearchConfig


def test_search_config_has_safe_defaults():
    config = SearchConfig()
    assert config.cycle_minutes >= 15
    assert config.sources.remoteok.enabled is True
    assert config.sources.google_jobs.enabled is False


def test_cycle_continues_when_ai_review_fails(tmp_path, monkeypatch):
    from jobster.models import CareerProfile, Job
    from jobster.runner import run_cycle
    from jobster.sources.base import JobSource
    from jobster.storage import JobsterStore

    class OneJobSource(JobSource):
        name = "one"

        def fetch(self):
            return [
                Job(
                    id="one:1",
                    title="Senior Product Designer",
                    company="Acme",
                    description="Product design and UX",
                    remote=True,
                    source="one",
                    url="https://example.com/job",
                )
            ]

    profile = CareerProfile(
        profile_id="p",
        display_name="Candidate",
        target_titles=["Senior Product Designer"],
    )
    config = SearchConfig()
    config.intake.enabled = False
    config.application.semantic_reasoning = True
    config.application.answer_bank_path = str(tmp_path / "answers.yaml")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fail_review(self, profile, job, baseline):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("jobster.runner.SemanticCareerBrain.evaluate", fail_review)

    store = JobsterStore(tmp_path / "jobster.db")
    store.init()
    events = []
    summary = run_cycle(
        profile,
        config,
        store,
        sources=[OneJobSource()],
        on_event=lambda event, payload: events.append((event, payload)),
    )

    assert summary["evaluated"] == 1
    assert summary["ai_review_paused"] is True
    assert any(event == "ai_review_paused" for event, _ in events)
