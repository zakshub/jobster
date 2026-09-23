from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .models import CareerProfile, Job


@dataclass(frozen=True)
class RelevanceResult:
    relevant: bool
    score: int
    reason: str
    matched_terms: tuple[str, ...] = ()


_BLOCKED_TITLE_TERMS = (
    "course ",
    "course director",
    "course writer",
    "curriculum",
    "education designer",
    "instructional designer",
    "teacher",
    "trainer",
    "data annotation",
    "data annotator",
    "response analyst",
    "sales ",
    "sales manager",
    "customer success",
    "customer support",
    "people operations",
    "human resources",
    "hr ",
    "payroll",
    "communications officer",
    "marketing ",
    "campaign operations",
    "business development",
    "crypto analyst",
    "trader",
    "deployment engineer",
    "backend engineer",
    "backend software",
    ".net",
    "oracle fusion",
    "security analytics",
    "principal engineer",
    "engineering manager",
    "software engineer",
    "software developer",
    "shopify developer",
    "golang",
    "kubernetes engineer",
)

_ROLE_PATTERNS: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (re.compile(r"\b(?:senior|sr\.?|staff|lead|principal)?\s*product designer\b"), 98, "product design"),
    (re.compile(r"\bproduct design(?:er| lead| manager| director| head)?\b"), 94, "product design"),
    (re.compile(r"\b(?:senior|sr\.?|lead|staff)?\s*ux designer\b"), 94, "ux design"),
    (re.compile(r"\bui\s*[/&-]\s*ux designer\b|\bux\s*[/&-]\s*ui designer\b"), 92, "ux/ui design"),
    (re.compile(r"\bux architect\b|\buser experience architect\b"), 98, "ux architecture"),
    (re.compile(r"\bux engineer\b"), 96, "ux engineering"),
    (re.compile(r"\bdesign engineer\b"), 86, "design engineering"),
    (re.compile(r"\bai product designer\b|\bproduct designer.*\bai\b|\bai.*\bproduct designer\b"), 98, "ai product design"),
    (re.compile(r"\bdesign systems? designer\b|\bdesign systems? lead\b"), 88, "design systems"),
    (re.compile(r"\binteraction designer\b"), 82, "interaction design"),
    (re.compile(r"\bexperience designer\b"), 80, "experience design"),
    (re.compile(r"\bgame ux\b|\bgame ui\b|\btechnical ui\b"), 76, "game/technical ui"),
    (re.compile(r"\bui engineer\b"), 76, "ui engineering"),
)

_DESIGN_CONTEXT = ("product", "ux", "user experience", "ui", "interaction", "design system", "ai")
_ROLE_NOUNS = ("designer", "architect", "engineer", "design lead", "design manager", "head of design")


def _norm(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9+#/. -]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def score_job_relevance(profile: CareerProfile, job: Job) -> RelevanceResult:
    title = _norm(job.title)
    if not title:
        return RelevanceResult(False, 0, "missing title")

    for term in _BLOCKED_TITLE_TERMS:
        if term.strip() in title:
            return RelevanceResult(False, 0, f"non-target role family: {term.strip()}")

    target_titles = [_norm(value) for value in profile.target_titles if value.strip()]
    for target in target_titles:
        if title == target:
            return RelevanceResult(True, 100, "exact target title", (target,))
        ratio = SequenceMatcher(None, title, target).ratio()
        if ratio >= 0.86:
            return RelevanceResult(True, 96, "close target title", (target,))
        if target in title or title in target:
            return RelevanceResult(True, 92, "target title variant", (target,))

    for pattern, score, label in _ROLE_PATTERNS:
        if pattern.search(title):
            return RelevanceResult(True, score, label, (label,))

    has_context = any(term in title for term in _DESIGN_CONTEXT)
    has_role = any(term in title for term in _ROLE_NOUNS)
    if has_context and has_role:
        return RelevanceResult(True, 72, "adjacent design role")

    return RelevanceResult(False, 20, "title is outside configured career lanes")


def select_relevant_jobs(
    profile: CareerProfile,
    jobs: list[Job],
    *,
    min_score: int = 70,
    max_per_source: int = 12,
    max_total: int = 60,
) -> tuple[list[Job], list[tuple[Job, RelevanceResult]]]:
    scored = [(job, score_job_relevance(profile, job)) for job in jobs]
    admitted = [
        (job, result)
        for job, result in scored
        if result.relevant and result.score >= min_score
    ]

    admitted.sort(key=lambda pair: pair[1].score, reverse=True)

    per_source: dict[str, int] = {}
    selected: list[Job] = []
    for job, _ in admitted:
        count = per_source.get(job.source, 0)
        if count >= max_per_source:
            continue
        selected.append(job)
        per_source[job.source] = count + 1
        if len(selected) >= max_total:
            break

    rejected = [(job, result) for job, result in scored if job not in selected]
    return selected, rejected
