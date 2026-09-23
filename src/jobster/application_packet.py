from __future__ import annotations

from pathlib import Path

from .models import CareerProfile, Job, JobEvaluation, ResumePacket
from .resume import tailor_resume


def build_application_packet(
    profile: CareerProfile,
    job: Job,
    evaluation: JobEvaluation,
    output_dir: str | Path,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume: ResumePacket = tailor_resume(profile, job, evaluation)

    resume_path = output_dir / f"{job.id.replace(':', '_')}_resume.md"
    resume_path.write_text(resume.markdown, encoding="utf-8")

    summary_path = output_dir / f"{job.id.replace(':', '_')}_decision.txt"
    summary_path.write_text(
        "\n".join([
            evaluation.summary,
            "",
            "Decision: " + evaluation.pursuit_decision.value,
            "Positioning: " + ", ".join(evaluation.positioning),
            "Strong matches: " + ", ".join(evaluation.strong_matches),
            "Learnable gaps: " + ", ".join(evaluation.learnable_gaps),
            "Unknowns: " + ", ".join(evaluation.unknowns),
            "Next: " + evaluation.next_action,
        ]),
        encoding="utf-8",
    )

    return {
        "job_id": job.id,
        "resume_markdown": str(resume_path),
        "decision_summary": str(summary_path),
    }
