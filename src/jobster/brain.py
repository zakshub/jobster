from __future__ import annotations

import re

from .models import CareerProfile, CareerValue, Job, JobEvaluation, PursuitDecision, RequirementAssessment, RequirementFit


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9+#. ]+", " ", text.lower())


def _contains(text: str, phrase: str) -> bool:
    return _norm(phrase) in _norm(text)


class CareerBrain:
    """Deterministic and inspectable baseline CareerBrain."""

    def evaluate(self, profile: CareerProfile, job: Job) -> JobEvaluation:
        combined = f"{job.title}\n{job.description}\n{job.location or ''}"
        blockers = []
        unknowns = []
        reasons = []
        strong_matches = []
        learnable_gaps = []
        assessments = []
        positioning = []

        if profile.remote_only and job.remote is False:
            blockers.append("Profile requires remote work but the posting is explicitly not remote")

        if profile.remote_only and job.remote is None:
            unknowns.append("Remote status is not explicit")

        title_match = any(_contains(job.title, title) or _contains(title, job.title) for title in profile.target_titles)
        if title_match:
            reasons.append("The role title aligns with at least one target title")

        capability_hits = 0
        for cap in profile.capabilities:
            terms = [cap.name, *cap.aliases]
            matched = [term for term in terms if _contains(combined, term)]
            if matched:
                capability_hits += 1
                strong_matches.append(cap.name)
                fit = RequirementFit.STRONG_EVIDENCE if cap.level.value in {"core", "strong"} else RequirementFit.SUPPORTED
                assessments.append(
                    RequirementAssessment(
                        requirement=cap.name,
                        fit=fit,
                        reason=f"Posting overlaps with verified capability terms: {', '.join(matched)}",
                        evidence_ids=cap.evidence_ids,
                    )
                )
                if len(positioning) < 3 and cap.level.value in {"core", "strong"}:
                    positioning.append(cap.name)

        preference_points = 0
        positive_signals = []
        negative_signals = []
        for pref in profile.preferences:
            if any(_contains(combined, kw) for kw in pref.keywords):
                preference_points += pref.weight
                if pref.weight > 0:
                    positive_signals.append(pref.name)
                elif pref.weight < 0:
                    negative_signals.append(pref.name)

        interest = 50 + preference_points * 8
        if title_match:
            interest += 10
        if capability_hits >= 3:
            interest += 10
        interest = max(0, min(100, interest))

        if positive_signals:
            reasons.append("Positive interest signals: " + ", ".join(positive_signals))
        if negative_signals:
            reasons.append("Negative interest signals: " + ", ".join(negative_signals))

        compensation = "unknown"
        minimum = profile.compensation.minimum_monthly
        if job.salary_max_monthly is not None and minimum is not None:
            if job.salary_max_monthly < minimum:
                compensation = "poor"
                blockers.append("Published maximum compensation is below the configured minimum")
            elif job.salary_min_monthly is not None and job.salary_min_monthly >= minimum:
                compensation = "good"
            else:
                compensation = "acceptable"
        elif job.salary_min_monthly is None and job.salary_max_monthly is None:
            unknowns.append("Compensation is not known")

        career_value = CareerValue(
            compensation=compensation,
            growth="high" if capability_hits >= 2 and interest >= 65 else "unknown",
            interesting_work="high" if interest >= 75 else "medium" if interest >= 55 else "low",
            global_exposure="high" if job.remote is True else "unknown",
            future_positioning="high" if title_match and capability_hits >= 2 else "medium" if capability_hits >= 1 else "unknown",
        )

        eligible = len(blockers) == 0
        if not eligible:
            decision = PursuitDecision.IGNORE
            next_action = "Do not apply unless Zak explicitly overrides the blocker"
        elif title_match and capability_hits >= 3 and interest >= 80:
            decision = PursuitDecision.HIGH_PRIORITY
            next_action = "Prepare a tailored application and move to the application queue"
        elif capability_hits >= 2 and interest >= 65:
            decision = PursuitDecision.APPLY
            next_action = "Prepare application materials"
        elif capability_hits >= 1 and interest >= 50:
            decision = PursuitDecision.WATCH
            next_action = "Review manually before spending application effort"
        else:
            decision = PursuitDecision.LOW_PRIORITY
            next_action = "Keep only if new evidence increases the opportunity value"

        if not assessments:
            learnable_gaps.append("The deterministic baseline found no explicit overlap with configured capabilities")
            unknowns.append("Semantic requirement extraction has not yet been run")

        confidence = 0.45
        if title_match:
            confidence += 0.15
        confidence += min(capability_hits, 4) * 0.08
        if job.remote is not None:
            confidence += 0.06
        confidence = min(0.92, confidence)

        role_interpretation = (
            f"{job.title} at {job.company}. "
            f"Baseline analysis found {capability_hits} configured capability overlaps. "
            "Semantic role decomposition will be added in the next reasoning layer."
        )

        summary = (
            f"{decision.value}: {job.title} at {job.company}. "
            f"Interest {interest}/100, {capability_hits} verified capability overlaps, "
            f"{len(blockers)} hard blockers, {len(unknowns)} unknowns."
        )

        return JobEvaluation(
            job_id=job.id,
            summary=summary,
            eligible=eligible,
            role_interpretation=role_interpretation,
            requirement_assessments=assessments,
            strong_matches=strong_matches,
            learnable_gaps=learnable_gaps,
            hard_blockers=blockers,
            unknowns=unknowns,
            interest_score=interest,
            career_value=career_value,
            pursuit_decision=decision,
            positioning=positioning,
            confidence=confidence,
            reasons=reasons,
            next_action=next_action,
        )
