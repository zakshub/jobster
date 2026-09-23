from jobster.models import CareerProfile, Job
from jobster.relevance import score_job_relevance, select_relevant_jobs
from jobster.text_utils import repair_text


def profile() -> CareerProfile:
    return CareerProfile(
        profile_id="zak",
        display_name="Zak",
        target_titles=[
            "Senior Product Designer",
            "UX Architect",
            "Product Designer",
            "UX Engineer",
            "AI Product Designer",
        ],
    )


def job(title: str, source: str = "remoteok") -> Job:
    return Job(
        id=f"{source}:{title}",
        title=title,
        company="Acme",
        description="",
        source=source,
        remote=True,
        url="https://example.com/job",
    )


def test_target_product_design_roles_are_admitted():
    result = score_job_relevance(profile(), job("Staff Product Designer"))
    assert result.relevant is True
    assert result.score >= 70


def test_target_ux_architect_is_admitted():
    result = score_job_relevance(profile(), job("Senior UX Architect"))
    assert result.relevant is True
    assert result.score >= 90


def test_generic_engineering_and_product_management_are_rejected():
    for title in (
        "Frontend Engineer",
        "AI Agent Engineer",
        "Senior Growth Product Manager AI Native",
        "Backend Software Engineer",
        "People Operations Coordinator",
    ):
        result = score_job_relevance(profile(), job(title))
        assert result.relevant is False, title


def test_course_and_education_jobs_are_rejected_even_with_ux_words():
    for title in (
        "Education Designer UX UI and AI",
        "Course Director UX UI and AI",
        "Course Writer and Editor UX UI and AI",
    ):
        assert score_job_relevance(profile(), job(title)).relevant is False


def test_source_cap_enforces_diversity():
    jobs = [
        job("Senior Product Designer", "remoteok"),
        job("Product Designer", "remoteok"),
        job("UX Architect", "remoteok"),
        job("AI Product Designer", "himalayas"),
    ]
    selected, rejected = select_relevant_jobs(
        profile(),
        jobs,
        min_score=70,
        max_per_source=2,
        max_total=10,
    )
    assert len([item for item in selected if item.source == "remoteok"]) == 2
    assert any(item.source == "himalayas" for item in selected)
    assert len(rejected) == 1


def test_repair_text_fixes_utf8_mojibake():
    assert repair_text("grabaciÃ³n") == "grabación"
    assert repair_text("ÙØ³ÙØ·") == "مسقط"
