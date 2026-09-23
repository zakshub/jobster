from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median
from typing import Iterable

from .models import CareerProfile
from .storage import JobsterStore


_PRIORITY_DECISIONS = {"aggressive_pursuit", "high_priority", "apply"}


def _clean_items(values: Iterable[str | None]) -> list[str]:
    return [str(value).strip() for value in values if value and str(value).strip()]


def build_funnel(store: JobsterStore) -> dict:
    metrics = store.dashboard_metrics()
    pipeline = store.pipeline_counts()
    evaluated = int(metrics.get("evaluated", 0))
    strong = int(metrics.get("high_priority", 0))
    applications = int(metrics.get("applications", 0))
    submitted = int(metrics.get("submitted", 0))
    interviews = len(
        [item for item in store.list_interviews(limit=500) if item.get("status") not in {"cancelled", "closed"}]
    )
    offers = len(
        [item for item in store.list_offers(limit=200) if item.get("status") not in {"declined", "closed"}]
    )

    return {
        "found": int(metrics.get("jobs", 0)),
        "reviewed": evaluated,
        "worth_pursuing": strong,
        "applications": applications,
        "submitted": submitted,
        "interviews": interviews,
        "offers": offers,
        "blocked": int(pipeline.get("blocked", 0)),
    }


def build_source_performance(store: JobsterStore, limit: int = 500) -> list[dict]:
    jobs = store.list_job_summaries(limit=limit)
    grouped: dict[str, dict] = defaultdict(
        lambda: {
            "source": "",
            "jobs": 0,
            "strong": 0,
            "saved": 0,
            "submitted": 0,
            "scores": [],
        }
    )
    for job in jobs:
        source = job.get("source") or "unknown"
        item = grouped[source]
        item["source"] = source
        item["jobs"] += 1
        if job.get("decision") in _PRIORITY_DECISIONS:
            item["strong"] += 1
        if job.get("saved"):
            item["saved"] += 1
        if job.get("application_state") == "submitted":
            item["submitted"] += 1
        if isinstance(job.get("interest_score"), int):
            item["scores"].append(job["interest_score"])

    output = []
    for item in grouped.values():
        jobs_count = item["jobs"]
        output.append(
            {
                "source": item["source"],
                "jobs": jobs_count,
                "strong": item["strong"],
                "saved": item["saved"],
                "submitted": item["submitted"],
                "strong_rate": round((item["strong"] / jobs_count) * 100, 1) if jobs_count else 0,
                "average_match": round(sum(item["scores"]) / len(item["scores"]), 1)
                if item["scores"]
                else None,
            }
        )
    output.sort(key=lambda item: (item["strong"], item["strong_rate"], item["jobs"]), reverse=True)
    return output


def _role_family(title: str) -> str:
    low = title.lower()
    if "ux architect" in low or "user experience architect" in low:
        return "UX Architecture"
    if "ux engineer" in low or "ui engineer" in low or "design engineer" in low:
        return "Design Engineering"
    if "ai product designer" in low or ("product designer" in low and "ai" in low):
        return "AI Product Design"
    if "product designer" in low or "product design" in low:
        return "Product Design"
    if "ux designer" in low or "ui/ux" in low or "ux/ui" in low:
        return "UX / UI Design"
    if "interaction designer" in low:
        return "Interaction Design"
    if "game ux" in low or "technical ui" in low or "game ui" in low:
        return "Game / Technical UI"
    return "Adjacent Design"


def build_role_trends(store: JobsterStore, limit: int = 500) -> list[dict]:
    jobs = [job for job in store.list_job_summaries(limit=limit) if not job.get("dismissed")]
    grouped: dict[str, dict] = defaultdict(lambda: {"count": 0, "strong": 0, "scores": []})
    for job in jobs:
        family = _role_family(job.get("title") or "")
        item = grouped[family]
        item["count"] += 1
        if job.get("decision") in _PRIORITY_DECISIONS:
            item["strong"] += 1
        if isinstance(job.get("interest_score"), int):
            item["scores"].append(job["interest_score"])

    output = []
    for family, item in grouped.items():
        output.append(
            {
                "family": family,
                "jobs": item["count"],
                "strong": item["strong"],
                "average_match": round(sum(item["scores"]) / len(item["scores"]), 1)
                if item["scores"]
                else None,
            }
        )
    output.sort(key=lambda item: (item["strong"], item["jobs"]), reverse=True)
    return output


def build_salary_intelligence(
    profile: CareerProfile,
    store: JobsterStore,
    limit: int = 500,
) -> dict:
    currency = profile.compensation.currency or "USD"
    jobs = store.list_job_summaries(limit=limit)
    values: list[float] = []
    strong_values: list[float] = []
    for job in jobs:
        if (job.get("currency") or currency) != currency:
            continue
        low = job.get("salary_min_monthly")
        high = job.get("salary_max_monthly")
        if low is None and high is None:
            continue
        midpoint = (
            (float(low) + float(high)) / 2
            if low is not None and high is not None
            else float(low if low is not None else high)
        )
        values.append(midpoint)
        if job.get("decision") in _PRIORITY_DECISIONS:
            strong_values.append(midpoint)

    def summary(data: list[float]) -> dict:
        if not data:
            return {"count": 0, "median": None, "low": None, "high": None}
        ordered = sorted(data)
        low_index = max(0, round((len(ordered) - 1) * 0.2))
        high_index = min(len(ordered) - 1, round((len(ordered) - 1) * 0.8))
        return {
            "count": len(ordered),
            "median": round(median(ordered), 2),
            "low": round(ordered[low_index], 2),
            "high": round(ordered[high_index], 2),
        }

    all_summary = summary(values)
    strong_summary = summary(strong_values)
    target = profile.compensation.target_monthly
    minimum = profile.compensation.minimum_monthly

    return {
        "currency": currency,
        "all_matching_jobs": all_summary,
        "strong_jobs": strong_summary,
        "target_monthly": target,
        "minimum_monthly": minimum,
        "note": "Salary figures only use jobs already stored with the same currency. No currency conversion is guessed.",
    }


def build_gap_signals(store: JobsterStore, limit: int = 200) -> list[dict]:
    jobs = store.list_job_summaries(limit=limit)
    gaps: Counter[str] = Counter()
    examples: dict[str, set[str]] = defaultdict(set)

    for job in jobs:
        if job.get("decision") not in _PRIORITY_DECISIONS:
            continue
        bundle = store.get_job_bundle(job["id"])
        evaluation = (bundle or {}).get("evaluation") or {}
        values = _clean_items(
            list(evaluation.get("learnable_gaps") or [])
            + list(evaluation.get("unknowns") or [])
        )
        for value in values:
            normalized = value.strip()
            if len(normalized) < 3:
                continue
            gaps[normalized] += 1
            examples[normalized].add(job.get("title") or "Job")

    output = [
        {
            "gap": gap,
            "jobs": count,
            "examples": sorted(examples[gap])[:3],
        }
        for gap, count in gaps.most_common(12)
    ]
    return output


def build_evidence_snapshot(profile: CareerProfile) -> dict:
    by_class = Counter(item.evidence_class.value for item in profile.evidence if item.status == "active")
    capabilities = Counter(capability.level.value for capability in profile.capabilities)
    evidence_linked = sum(1 for capability in profile.capabilities if capability.evidence_ids)
    unknown_capabilities = [
        capability.name
        for capability in profile.capabilities
        if capability.confidence.value == "unknown"
        or capability.level.value == "not_claimed"
    ]
    return {
        "evidence_total": len([item for item in profile.evidence if item.status == "active"]),
        "evidence_by_class": dict(by_class),
        "capabilities_total": len(profile.capabilities),
        "capabilities_by_level": dict(capabilities),
        "capabilities_with_evidence": evidence_linked,
        "unknown_capabilities": unknown_capabilities[:20],
        "experience_entries": len(profile.experiences),
        "portfolio_connected": bool(profile.portfolio_url),
        "linkedin_connected": bool(profile.linkedin_url),
    }


def build_company_signals(store: JobsterStore, limit: int = 200) -> list[dict]:
    companies = store.list_company_summaries(limit=limit)
    output = []
    for company in companies:
        strength = "quiet"
        if company["strong_jobs"] >= 3:
            strength = "active"
        elif company["strong_jobs"] >= 1:
            strength = "interesting"
        output.append({**company, "signal": strength})
    return output


def build_daily_missions(profile: CareerProfile, store: JobsterStore) -> list[dict]:
    missions: list[dict] = []
    attention = store.list_needs_attention(limit=50)
    jobs = store.list_job_summaries(limit=300)
    applications = store.list_application_summaries(limit=200)
    interviews = store.list_interviews(limit=50)
    offers = store.list_offers(limit=50)

    if attention:
        missions.append(
            {
                "kind": "needs_you",
                "priority": 1,
                "title": f"Review {len(attention)} item{'s' if len(attention) != 1 else ''} that need you",
                "detail": "Jobster stopped instead of guessing. Clear these decisions first.",
                "action": "attention",
            }
        )

    strong_unprepared = [
        job
        for job in jobs
        if not job.get("dismissed")
        and job.get("decision") in _PRIORITY_DECISIONS
        and not job.get("application_state")
    ]
    if strong_unprepared:
        top = sorted(
            strong_unprepared,
            key=lambda item: int(item.get("interest_score") or 0),
            reverse=True,
        )[0]
        missions.append(
            {
                "kind": "opportunity",
                "priority": 2,
                "title": f"Review {top['title']} at {top['company']}",
                "detail": f"This is one of the strongest current matches ({top.get('interest_score') or '—'}/100).",
                "action": "job",
                "job_id": top["id"],
            }
        )

    ready = [item for item in applications if item.get("state") == "ready"]
    if ready:
        missions.append(
            {
                "kind": "ready",
                "priority": 3,
                "title": f"{len(ready)} application{'s are' if len(ready) != 1 else ' is'} ready",
                "detail": "Review the prepared application before the final action.",
                "action": "applications",
            }
        )

    upcoming = [
        item
        for item in interviews
        if item.get("status") in {"planned", "confirmed"}
    ]
    if upcoming:
        missions.append(
            {
                "kind": "interview",
                "priority": 4,
                "title": f"Prepare for {upcoming[0]['company']}",
                "detail": "An interview is on your active list. Keep the role evidence and stories ready.",
                "action": "interviews",
                "interview_id": upcoming[0]["id"],
            }
        )

    open_offers = [item for item in offers if item.get("status") in {"reviewing", "negotiating"}]
    if open_offers:
        missions.append(
            {
                "kind": "offer",
                "priority": 5,
                "title": f"Review the {open_offers[0]['company']} offer",
                "detail": "Compare the offer against your target, trade-offs, and negotiation room.",
                "action": "offers",
                "offer_id": open_offers[0]["id"],
            }
        )

    if not missions:
        missions.append(
            {
                "kind": "search",
                "priority": 9,
                "title": "Run a fresh job search",
                "detail": "Nothing urgent is waiting. Look for new roles that fit your direction.",
                "action": "find_jobs",
            }
        )

    missions.sort(key=lambda item: item["priority"])
    return missions[:5]




def diagnose_bottleneck(funnel: dict) -> dict:
    reviewed = int(funnel.get("reviewed", 0))
    strong = int(funnel.get("worth_pursuing", 0))
    applications = int(funnel.get("applications", 0))
    submitted = int(funnel.get("submitted", 0))
    interviews = int(funnel.get("interviews", 0))
    offers = int(funnel.get("offers", 0))

    if reviewed >= 10 and strong == 0:
        return {
            "stage": "search_quality",
            "title": "The search is finding jobs, but not enough are worth pursuing.",
            "detail": "Tighten sources and role targeting before increasing application volume.",
        }
    if strong >= 3 and applications == 0:
        return {
            "stage": "execution",
            "title": "Strong opportunities exist, but they are not becoming applications.",
            "detail": "Review blockers, application readiness, and the Needs-you queue.",
        }
    if submitted >= 5 and interviews == 0:
        return {
            "stage": "response",
            "title": "Applications are going out, but recruiter response is the weak point.",
            "detail": "Review positioning, evidence, source quality, and whether outreach would add value.",
        }
    if interviews >= 3 and offers == 0:
        return {
            "stage": "interview",
            "title": "The process is reaching interviews, but not yet converting to offers.",
            "detail": "Use the STAR story bank and interview debriefs to improve preparation.",
        }
    if offers > 0:
        return {
            "stage": "offer",
            "title": "The search has reached offer stage.",
            "detail": "Focus on the quality of the move, trade-offs, and negotiation — not application volume.",
        }
    return {
        "stage": "building",
        "title": "The funnel is still building.",
        "detail": "Keep collecting enough high-quality evidence before drawing strong conclusions.",
    }


def build_insights(profile: CareerProfile, store: JobsterStore) -> dict:
    funnel = build_funnel(store)
    return {
        "funnel": funnel,
        "bottleneck": diagnose_bottleneck(funnel),
        "sources": build_source_performance(store),
        "roles": build_role_trends(store),
        "salary": build_salary_intelligence(profile, store),
        "gaps": build_gap_signals(store),
        "evidence": build_evidence_snapshot(profile),
        "companies": build_company_signals(store),
        "feedback": store.list_feedback(limit=50),
    }
