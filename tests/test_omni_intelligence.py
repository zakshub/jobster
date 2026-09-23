from pathlib import Path

from jobster.models import (
    Capability,
    CapabilityLevel,
    CareerProfile,
    Confidence,
    EvidenceClass,
    EvidenceItem,
    Job,
    JobEvaluation,
    PursuitDecision,
    CareerValue,
)
from jobster.omni_intelligence import (
    build_career_graph,
    build_data_health,
    build_job_explanation,
    build_learning_suggestions,
    build_portfolio_map,
)
from jobster.storage import JobsterStore


def profile() -> CareerProfile:
    return CareerProfile(
        profile_id="zak",
        display_name="Zak",
        headline="Senior Product Designer",
        location="Karachi, Pakistan",
        target_titles=["Senior Product Designer", "UX Architect"],
        portfolio_url="https://example.com/portfolio",
        linkedin_url="https://example.com/linkedin",
        capabilities=[
            Capability(
                name="Design systems",
                level=CapabilityLevel.STRONG,
                confidence=Confidence.HIGH,
                evidence_ids=["e1"],
            ),
            Capability(
                name="AI product design",
                level=CapabilityLevel.EMERGING,
                confidence=Confidence.MEDIUM,
                evidence_ids=[],
            ),
        ],
        evidence=[
            EvidenceItem(
                id="e1",
                statement="Built and maintained a production design system.",
                evidence_class=EvidenceClass.PROFESSIONAL_RECORD,
                source="Career Master File",
                domain="product_design",
                confidence=0.95,
            )
        ],
    )


def seed(store: JobsterStore) -> str:
    store.init()
    job = Job(
        id="job-1",
        title="Senior Product Designer",
        company="Acme Health",
        description="Healthcare SaaS design systems role",
        remote=True,
        source="manual",
        url="https://example.com/job-1",
    )
    store.save_job(job)
    store.save_evaluation(
        JobEvaluation(
            job_id=job.id,
            summary="Strong fit.",
            eligible=True,
            role_interpretation="Senior product design role",
            strong_matches=["Design systems"],
            interest_score=92,
            career_value=CareerValue(
                compensation="good",
                growth="high",
                interesting_work="high",
                global_exposure="high",
                future_positioning="high",
            ),
            pursuit_decision=PursuitDecision.HIGH_PRIORITY,
            confidence=0.93,
            positioning=["Design systems"],
            next_action="Prepare application",
        )
    )
    return job.id


def test_explanation_and_graph(tmp_path: Path):
    store = JobsterStore(tmp_path / "jobster.db")
    job_id = seed(store)
    p = profile()

    explanation = build_job_explanation(p, store, job_id)
    assert explanation is not None
    assert explanation["confidence_label"] == "High"
    assert explanation["decision"] == "high_priority"
    assert explanation["why_kept"]

    graph = build_career_graph(p, store)
    assert graph["summary"]["target_roles"] == 2
    assert any(node["type"] == "person" for node in graph["nodes"])
    assert any(node["type"] == "job" for node in graph["nodes"])


def test_portfolio_and_data_health(tmp_path: Path):
    store = JobsterStore(tmp_path / "jobster.db")
    seed(store)
    p = profile()

    portfolio = build_portfolio_map(p, store)
    assert portfolio["portfolio_connected"] is True
    assert any(item["name"] == "Design systems" for item in portfolio["capabilities"])

    health = build_data_health(p, store)
    assert 0 <= health["score"] <= 100
    assert health["status"] in {"healthy", "review", "attention"}


def test_learning_suggestions_do_not_mutate_profile(tmp_path: Path):
    store = JobsterStore(tmp_path / "jobster.db")
    job_id = seed(store)
    p = profile()
    original_targets = list(p.target_titles)

    for _ in range(3):
        store.save_feedback(job_id, "outside_direction", None)

    suggestions = build_learning_suggestions(p, store)
    assert any(item["id"] == "reduce-outside-direction" for item in suggestions)
    assert p.target_titles == original_targets


def test_archive_journal_and_learning_storage(tmp_path: Path):
    store = JobsterStore(tmp_path / "jobster.db")
    job_id = seed(store)

    archive = store.set_job_archived(job_id, True)
    assert archive["archived"] is True
    assert store.list_job_summaries()[0]["archived"] is True

    entry = store.add_decision_journal(job_id, "pursue", "Strong healthcare fit")
    assert entry["decision"] == "pursue"
    assert store.list_decision_journal(job_id)[0]["reason"] == "Strong healthcare fit"

    proposal = store.upsert_learning_proposal({
        "id": "p1",
        "kind": "preference",
        "title": "Review direction",
        "detail": "Repeated explicit feedback",
        "evidence": "3 events",
    })
    assert proposal["status"] == "suggested"

    decided = store.set_learning_proposal_status("p1", "approved")
    assert decided is not None
    assert decided["status"] == "approved"
