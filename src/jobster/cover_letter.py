from __future__ import annotations

from dataclasses import dataclass

from .models import CareerProfile, Job, JobEvaluation


@dataclass(frozen=True)
class EmailApplication:
    subject: str
    body: str


def build_email_application(
    profile: CareerProfile,
    job: Job,
    evaluation: JobEvaluation,
) -> EmailApplication:
    """Create a concise application email using verified CareerBrain output."""
    subject = f"Application: {job.title} — {profile.display_name}"
    positioning = evaluation.positioning[:2]
    matches = evaluation.strong_matches[:3]

    if positioning:
        opening = (
            f"I am applying for the {job.title} role at {job.company}. "
            f"My background as a {', '.join(positioning)} aligns well with the role."
        )
    else:
        opening = (
            f"I am applying for the {job.title} role at {job.company}. "
            f"My experience is closely aligned with the work described in the posting."
        )

    evidence = ""
    if matches:
        evidence = " In particular, I would bring experience in " + ", ".join(matches) + "."

    portfolio = (
        f" You can review my work at {profile.portfolio_url}."
        if profile.portfolio_url
        else ""
    )
    body = (
        "Hello,\n\n"
        f"{opening}{evidence}\n\n"
        "I have attached my resume for your review. I would welcome the opportunity "
        f"to discuss how I could contribute to {job.company}.{portfolio}\n\n"
        f"Best regards,\n{profile.display_name}"
    )
    return EmailApplication(subject=subject, body=body)
