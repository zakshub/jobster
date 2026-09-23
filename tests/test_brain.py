from jobster.brain import CareerBrain
from jobster.models import CareerProfile, Capability, CapabilityLevel, Confidence, CareerPreference, Job, PursuitDecision


def profile() -> CareerProfile:
    return CareerProfile(
        profile_id="test",
        display_name="Test",
        target_titles=["Senior Product Designer"],
        capabilities=[
            Capability(name="Product Design", level=CapabilityLevel.CORE, confidence=Confidence.HIGH, aliases=["product designer"]),
            Capability(name="UX Architecture", level=CapabilityLevel.CORE, confidence=Confidence.HIGH, aliases=["information architecture"]),
            Capability(name="Design Systems", level=CapabilityLevel.STRONG, confidence=Confidence.HIGH, aliases=["design system"]),
        ],
        preferences=[
            CareerPreference(name="Complex systems", weight=4, keywords=["complex workflows"]),
            CareerPreference(name="Design systems", weight=3, keywords=["design system"]),
        ],
    )


def test_good_remote_role_is_pursued():
    job = Job(
        id="1",
        title="Senior Product Designer",
        company="Acme",
        description="Own product design, complex workflows, information architecture and the design system.",
        remote=True,
    )
    result = CareerBrain().evaluate(profile(), job)
    assert result.eligible is True
    assert result.pursuit_decision in {PursuitDecision.APPLY, PursuitDecision.HIGH_PRIORITY, PursuitDecision.AGGRESSIVE_PURSUIT}
    assert "Product Design" in result.strong_matches


def test_non_remote_role_is_blocked():
    job = Job(
        id="2",
        title="Senior Product Designer",
        company="Acme",
        description="Product design role",
        remote=False,
    )
    result = CareerBrain().evaluate(profile(), job)
    assert result.eligible is False
    assert result.pursuit_decision == PursuitDecision.IGNORE
    assert result.hard_blockers


def test_unknowns_remain_visible():
    job = Job(
        id="3",
        title="Designer",
        company="Acme",
        description="A broad design position",
        remote=None,
    )
    result = CareerBrain().evaluate(profile(), job)
    assert result.unknowns
