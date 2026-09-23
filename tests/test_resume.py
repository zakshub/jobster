from jobster.brain import CareerBrain
from jobster.models import CareerProfile, Capability, CapabilityLevel, Confidence, ExperienceEntry, Job
from jobster.resume import tailor_resume


def test_resume_only_uses_profile_highlights():
    profile = CareerProfile(
        profile_id="p",
        display_name="Candidate",
        target_titles=["Senior Product Designer"],
        capabilities=[Capability(name="Design Systems", level=CapabilityLevel.STRONG, confidence=Confidence.HIGH, aliases=["design system"])],
        experiences=[ExperienceEntry(company="Acme", title="Designer", highlights=["Built a design system", "Worked on a dashboard"])],
    )
    job = Job(id="j", title="Senior Product Designer", company="Target", description="Own our design system", remote=True)
    evaluation = CareerBrain().evaluate(profile, job)
    packet = tailor_resume(profile, job, evaluation)
    assert "Built a design system" in packet.markdown
    assert "invent" not in packet.markdown.lower()
