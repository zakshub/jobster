from __future__ import annotations

import re

from .models import CareerProfile, Job, JobEvaluation, ResumeExperience, ResumePacket


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9+#.]{3,}", text.lower())}


def _score_text(text: str, job_tokens: set[str]) -> int:
    return len(_tokens(text) & job_tokens)


def tailor_resume(profile: CareerProfile, job: Job, evaluation: JobEvaluation) -> ResumePacket:
    job_tokens = _tokens(job.title + " " + job.description)
    capabilities = sorted(
        profile.capabilities,
        key=lambda c: (
            c.name in evaluation.strong_matches,
            _score_text(" ".join([c.name, *c.aliases]), job_tokens),
            c.level.value in {"core", "strong"},
        ),
        reverse=True,
    )
    selected_skills = [c.name for c in capabilities[:10]]

    ranked = []
    for exp in profile.experiences:
        text = " ".join([exp.title, exp.company, *exp.domain, *exp.skills, *exp.highlights])
        ranked.append((_score_text(text, job_tokens), exp))
    ranked.sort(key=lambda x: x[0], reverse=True)

    experiences = []
    for score, exp in ranked:
        highlights = sorted(exp.highlights, key=lambda h: _score_text(h, job_tokens), reverse=True)
        period = " – ".join([x for x in [exp.start, exp.end] if x]) or None
        experiences.append(
            ResumeExperience(
                company=exp.company,
                title=exp.title,
                period=period,
                highlights=highlights[:5],
            )
        )

    headline = evaluation.positioning[0] if evaluation.positioning else profile.headline or job.title
    strengths = ", ".join(evaluation.strong_matches[:4]) or ", ".join(selected_skills[:4])
    summary = (
        f"{profile.display_name} — {headline}. "
        f"Relevant strengths for {job.title}: {strengths}. "
        "All claims below are selected from the verified profile; Jobster does not create new credentials."
    )

    lines = [f"# {profile.display_name}", "", f"## {headline}", "", summary, "", "## Relevant Skills"]
    lines.extend([f"- {skill}" for skill in selected_skills])
    lines.extend(["", "## Experience"])
    for exp in experiences:
        period = f" | {exp.period}" if exp.period else ""
        lines.append(f"### {exp.title} — {exp.company}{period}")
        for bullet in exp.highlights:
            lines.append(f"- {bullet}")
        lines.append("")

    if profile.education:
        lines.append("## Education")
        for ed in profile.education:
            period = f" | {ed.period}" if ed.period else ""
            lines.append(f"- {ed.qualification}, {ed.institution}{period}")

    omitted = []
    for gap in evaluation.learnable_gaps:
        omitted.append(f"Not presented as an existing capability: {gap}")

    return ResumePacket(
        job_id=job.id,
        headline=headline,
        summary=summary,
        selected_skills=selected_skills,
        experiences=experiences,
        omitted_claims=omitted,
        markdown="\n".join(lines).strip() + "\n",
    )
