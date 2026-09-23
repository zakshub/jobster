from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from .intelligence import build_gap_signals
from .models import CareerProfile
from .storage import JobsterStore


_PRIORITY_DECISIONS = {"aggressive_pursuit", "high_priority", "apply"}


def _confidence_label(value: float | None) -> str:
    if value is None:
        return "Unknown"
    if value >= 0.85:
        return "High"
    if value >= 0.65:
        return "Medium"
    return "Needs checking"


def build_job_explanation(
    profile: CareerProfile,
    store: JobsterStore,
    job_id: str,
) -> dict[str, Any] | None:
    bundle = store.get_job_bundle(job_id)
    if bundle is None:
        return None

    job = bundle.get("job") or {}
    evaluation = bundle.get("evaluation") or {}
    application = bundle.get("application") or {}
    verification = bundle.get("verification") or {}

    evidence_index = {item.id: item for item in profile.evidence}
    evidence_refs: list[dict[str, Any]] = []
    seen: set[str] = set()

    for requirement in evaluation.get("requirement_assessments") or []:
        for evidence_id in requirement.get("evidence_ids") or []:
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            item = evidence_index.get(evidence_id)
            if item is None:
                evidence_refs.append(
                    {
                        "id": evidence_id,
                        "statement": "Evidence reference exists but the item is not present in the current profile.",
                        "source": "Unknown",
                        "confidence": None,
                        "status": "missing",
                    }
                )
                continue
            evidence_refs.append(
                {
                    "id": item.id,
                    "statement": item.statement,
                    "source": item.source,
                    "evidence_class": item.evidence_class.value,
                    "confidence": item.confidence,
                    "status": item.status,
                }
            )

    reasons = list(evaluation.get("reasons") or [])
    strong_matches = list(evaluation.get("strong_matches") or [])
    gaps = list(evaluation.get("learnable_gaps") or [])
    unknowns = list(evaluation.get("unknowns") or [])
    blockers = list(evaluation.get("hard_blockers") or [])

    why_kept: list[str] = []
    if evaluation.get("eligible"):
        why_kept.append("The role passed the eligibility checks.")
    if strong_matches:
        why_kept.append(f"{len(strong_matches)} strong match{'es' if len(strong_matches) != 1 else ''} were found.")
    if evaluation.get("pursuit_decision") in _PRIORITY_DECISIONS:
        why_kept.append("Jobster considers this role worth active pursuit.")
    if verification.get("state") == "live":
        why_kept.append("The job page was checked and appears to be live.")

    why_not_auto: list[str] = []
    state = application.get("state")
    if state == "blocked":
        why_not_auto.extend(application.get("reasons") or [])
    if application.get("unknown_questions"):
        why_not_auto.append("The application contains questions Jobster cannot answer safely yet.")
    if application.get("blocked_questions"):
        why_not_auto.append("At least one question needs an approved answer.")
    if verification.get("state") in {"expired", "unreachable", "needs_review"}:
        why_not_auto.append("The job page needs a human check before an application can continue.")
    if not application:
        why_not_auto.append("No application plan has been prepared for this job yet.")

    return {
        "job": {
            "id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
        },
        "decision": evaluation.get("pursuit_decision"),
        "match_score": evaluation.get("interest_score"),
        "confidence": evaluation.get("confidence"),
        "confidence_label": _confidence_label(evaluation.get("confidence")),
        "summary": evaluation.get("summary") or evaluation.get("role_interpretation"),
        "reasons": reasons,
        "strong_matches": strong_matches,
        "learnable_gaps": gaps,
        "unknowns": unknowns,
        "hard_blockers": blockers,
        "requirements": evaluation.get("requirement_assessments") or [],
        "career_value": evaluation.get("career_value") or {},
        "positioning": evaluation.get("positioning") or [],
        "evidence": evidence_refs,
        "why_kept": why_kept,
        "why_not_auto": list(dict.fromkeys(why_not_auto)),
        "next_action": evaluation.get("next_action"),
        "verification": verification,
        "application_state": state,
    }


def build_career_graph(
    profile: CareerProfile,
    store: JobsterStore,
    *,
    job_limit: int = 24,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    person_id = f"person:{profile.profile_id}"
    nodes.append(
        {
            "id": person_id,
            "type": "person",
            "label": profile.display_name,
            "meta": profile.headline or "Career profile",
            "weight": 10,
        }
    )

    for index, title in enumerate(profile.target_titles):
        node_id = f"role:{index}:{title}"
        nodes.append(
            {
                "id": node_id,
                "type": "target_role",
                "label": title,
                "meta": "Target role",
                "weight": 8,
            }
        )
        edges.append({"source": person_id, "target": node_id, "type": "targets"})

    evidence_by_capability: Counter[str] = Counter()
    for capability in profile.capabilities:
        node_id = f"capability:{capability.name}"
        evidence_by_capability[capability.name] = len(capability.evidence_ids)
        nodes.append(
            {
                "id": node_id,
                "type": "capability",
                "label": capability.name,
                "meta": capability.level.value.replace("_", " ").title(),
                "confidence": capability.confidence.value,
                "evidence_count": len(capability.evidence_ids),
                "weight": 4 + min(len(capability.evidence_ids), 4),
            }
        )
        edges.append({"source": person_id, "target": node_id, "type": "has"})

    for index, experience in enumerate(profile.experiences):
        node_id = f"experience:{index}"
        nodes.append(
            {
                "id": node_id,
                "type": "experience",
                "label": experience.company,
                "meta": experience.title,
                "weight": 6,
            }
        )
        edges.append({"source": person_id, "target": node_id, "type": "worked_at"})

    jobs = [
        item
        for item in store.list_job_summaries(limit=300)
        if not item.get("dismissed")
        and item.get("decision") in _PRIORITY_DECISIONS
    ]
    jobs.sort(key=lambda item: int(item.get("interest_score") or 0), reverse=True)

    seen_companies: set[str] = set()
    for job in jobs[:job_limit]:
        company = job.get("company") or "Unknown company"
        company_id = f"company:{company.lower()}"
        if company_id not in seen_companies:
            seen_companies.add(company_id)
            nodes.append(
                {
                    "id": company_id,
                    "type": "company",
                    "label": company,
                    "meta": "Observed company",
                    "weight": 5,
                }
            )

        job_id = f"job:{job['id']}"
        nodes.append(
            {
                "id": job_id,
                "type": "job",
                "label": job.get("title") or "Job",
                "meta": company,
                "score": job.get("interest_score"),
                "decision": job.get("decision"),
                "weight": 3,
            }
        )
        edges.append({"source": company_id, "target": job_id, "type": "offers"})
        edges.append({"source": person_id, "target": job_id, "type": "matches"})

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "target_roles": len(profile.target_titles),
            "capabilities": len(profile.capabilities),
            "experiences": len(profile.experiences),
            "strong_jobs": min(len(jobs), job_limit),
        },
    }


def build_portfolio_map(profile: CareerProfile, store: JobsterStore) -> dict[str, Any]:
    gap_signals = build_gap_signals(store)
    recurring = {item["gap"]: item["jobs"] for item in gap_signals}

    capabilities = []
    for capability in profile.capabilities:
        evidence_count = len(capability.evidence_ids)
        proof = "strong" if evidence_count >= 2 else "some" if evidence_count == 1 else "missing"
        capabilities.append(
            {
                "name": capability.name,
                "level": capability.level.value,
                "confidence": capability.confidence.value,
                "evidence_count": evidence_count,
                "proof": proof,
            }
        )

    case_studies = []
    for experience in profile.experiences:
        score = len(experience.highlights) + len(experience.skills) + len(experience.evidence_ids) * 2
        case_studies.append(
            {
                "company": experience.company,
                "title": experience.title,
                "skills": experience.skills,
                "highlights": experience.highlights,
                "evidence_count": len(experience.evidence_ids),
                "case_study_strength": min(100, score * 8),
            }
        )
    case_studies.sort(key=lambda item: item["case_study_strength"], reverse=True)

    missing_proof = [
        item
        for item in capabilities
        if item["proof"] == "missing"
        and item["level"] in {"core", "strong", "working", "emerging"}
    ]

    return {
        "portfolio_connected": bool(profile.portfolio_url),
        "portfolio_url": profile.portfolio_url,
        "case_studies": case_studies,
        "capabilities": capabilities,
        "missing_proof": missing_proof,
        "recurring_market_gaps": recurring,
    }


def build_data_health(profile: CareerProfile, store: JobsterStore) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    if not profile.portfolio_url:
        issues.append(
            {
                "kind": "missing",
                "severity": "medium",
                "title": "Portfolio link is missing",
                "detail": "Jobster cannot connect portfolio proof to opportunities until a portfolio link is present.",
            }
        )
    if not profile.linkedin_url:
        issues.append(
            {
                "kind": "missing",
                "severity": "low",
                "title": "LinkedIn link is missing",
                "detail": "This does not block applications, but it reduces profile completeness.",
            }
        )

    for capability in profile.capabilities:
        if capability.level.value in {"core", "strong"} and not capability.evidence_ids:
            issues.append(
                {
                    "kind": "evidence",
                    "severity": "medium",
                    "title": f"{capability.name} has no linked evidence",
                    "detail": "A strong capability is more credible when it points to a real project, record, or artifact.",
                }
            )

    unresolved_evidence = [
        item for item in profile.evidence if item.status == "unresolved"
    ]
    if unresolved_evidence:
        issues.append(
            {
                "kind": "evidence",
                "severity": "medium",
                "title": f"{len(unresolved_evidence)} evidence item{'s' if len(unresolved_evidence) != 1 else ''} need review",
                "detail": "Unresolved evidence is kept separate so Jobster does not treat it as confirmed fact.",
            }
        )

    compensation = profile.compensation
    if (
        compensation.minimum_monthly is not None
        and compensation.target_monthly is not None
        and compensation.minimum_monthly > compensation.target_monthly
    ):
        issues.append(
            {
                "kind": "contradiction",
                "severity": "high",
                "title": "Pay settings conflict",
                "detail": "The minimum monthly pay is higher than the target monthly pay.",
            }
        )

    seen_experiences: set[tuple[str, str]] = set()
    for experience in profile.experiences:
        key = (experience.company.strip().lower(), experience.title.strip().lower())
        if key in seen_experiences:
            issues.append(
                {
                    "kind": "duplicate",
                    "severity": "low",
                    "title": f"Possible duplicate experience: {experience.company}",
                    "detail": "Two experience entries use the same company and title. Check whether both are intentional.",
                }
            )
        seen_experiences.add(key)

    jobs = store.list_job_summaries(limit=500)
    unchecked = sum(1 for item in jobs if not item.get("verification_state"))
    if unchecked:
        issues.append(
            {
                "kind": "freshness",
                "severity": "low",
                "title": f"{unchecked} job{'s' if unchecked != 1 else ''} have not been live-checked",
                "detail": "A source result can be real but already closed. Live-check strong jobs before applying.",
            }
        )

    weights = {"high": 18, "medium": 9, "low": 3}
    penalty = sum(weights.get(item["severity"], 4) for item in issues)
    score = max(0, 100 - min(100, penalty))

    return {
        "score": score,
        "status": "healthy" if score >= 85 else "review" if score >= 65 else "attention",
        "issues": issues[:40],
        "counts": dict(Counter(item["kind"] for item in issues)),
    }


def build_learning_suggestions(profile: CareerProfile, store: JobsterStore) -> list[dict[str, Any]]:
    feedback = store.list_feedback(limit=300)
    reactions = Counter(item.get("reaction") for item in feedback)
    suggestions: list[dict[str, Any]] = []

    if reactions.get("outside_direction", 0) >= 3:
        suggestions.append(
            {
                "id": "reduce-outside-direction",
                "kind": "preference",
                "title": "Tighten role direction",
                "detail": "You have marked several jobs as the wrong direction. Jobster can keep showing them for now, or you can tighten the target-role rules.",
                "evidence": f"{reactions['outside_direction']} explicit feedback events",
                "requires_approval": True,
            }
        )

    if reactions.get("salary_too_low", 0) >= 2:
        suggestions.append(
            {
                "id": "review-minimum-pay",
                "kind": "compensation",
                "title": "Review your minimum pay",
                "detail": "You have repeatedly marked jobs as paying too little. Consider checking whether your minimum-pay rule still matches what you want.",
                "evidence": f"{reactions['salary_too_low']} pay-related feedback events",
                "requires_approval": True,
            }
        )

    gaps = build_gap_signals(store)
    for item in gaps[:4]:
        if item.get("jobs", 0) < 2:
            continue
        suggestions.append(
            {
                "id": f"gap:{item['gap']}",
                "kind": "skill_gap",
                "title": f"Repeated gap: {item['gap']}",
                "detail": "This gap appears across multiple strong opportunities. It may be worth proving, learning, or explicitly deciding not to pursue.",
                "evidence": f"Appears in {item['jobs']} strong jobs",
                "requires_approval": True,
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "id": "not-enough-signal",
                "kind": "observation",
                "title": "No strong learning change yet",
                "detail": "Jobster is keeping your current career model stable because there is not enough repeated evidence to suggest a change.",
                "evidence": "Not enough repeated feedback yet",
                "requires_approval": False,
            }
        )

    return suggestions[:8]


def build_search_history(store: JobsterStore, limit: int = 30) -> list[dict[str, Any]]:
    history = []
    for event in store.list_activity(limit=500):
        if event.get("event_type") != "discovery_cycle_completed":
            continue
        payload = event.get("payload") or {}
        history.append(
            {
                "id": event.get("id"),
                "created_at": event.get("created_at"),
                "raw_discovered": payload.get("raw_discovered"),
                "relevant": payload.get("discovered"),
                "rejected": payload.get("rejected_irrelevant"),
                "sources": payload.get("sources") or [],
                "decisions": payload.get("decisions") or {},
                "ai_review_paused": payload.get("ai_review_paused", False),
            }
        )
        if len(history) >= limit:
            break
    return history


def build_decision_brief(
    profile: CareerProfile,
    store: JobsterStore,
    job_id: str,
) -> dict[str, Any] | None:
    explanation = build_job_explanation(profile, store, job_id)
    if explanation is None:
        return None

    score = explanation.get("match_score")
    confidence = explanation.get("confidence_label")
    decision = explanation.get("decision") or "pending"
    company = explanation["job"].get("company")
    title = explanation["job"].get("title")

    headline = f"{title} at {company}"
    if score is not None:
        headline += f" · {score}/100 match"

    return {
        "headline": headline,
        "decision": decision,
        "confidence": confidence,
        "why": explanation.get("why_kept") or explanation.get("reasons") or [],
        "risks": list(
            dict.fromkeys(
                [
                    *explanation.get("hard_blockers", []),
                    *explanation.get("unknowns", []),
                    *explanation.get("learnable_gaps", []),
                ]
            )
        )[:8],
        "positioning": explanation.get("positioning") or [],
        "next_action": explanation.get("next_action"),
        "auto_action_blockers": explanation.get("why_not_auto") or [],
    }
