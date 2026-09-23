from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceClass(str, Enum):
    OBSERVATION = "observation"
    EXPLICIT_CORRECTION = "explicit_correction"
    ARTIFACT = "artifact"
    PROCESS_EVIDENCE = "process_evidence"
    PROFESSIONAL_RECORD = "professional_record"
    SELF_DESCRIPTION = "self_description"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class CapabilityLevel(str, Enum):
    CORE = "core"
    STRONG = "strong"
    WORKING = "working"
    HISTORICAL = "historical"
    EMERGING = "emerging"
    EXPLORATORY = "exploratory"
    NOT_CLAIMED = "not_claimed"


class RequirementFit(str, Enum):
    STRONG_EVIDENCE = "strong_evidence"
    SUPPORTED = "supported"
    ADJACENT = "adjacent"
    LEARNABLE = "learnable"
    WEAK_EVIDENCE = "weak_evidence"
    NOT_CLAIMED = "not_claimed"
    HARD_BLOCKER = "hard_blocker"
    UNKNOWN = "unknown"


class PursuitDecision(str, Enum):
    IGNORE = "ignore"
    WATCH = "watch"
    LOW_PRIORITY = "low_priority"
    APPLY = "apply"
    HIGH_PRIORITY = "high_priority"
    AGGRESSIVE_PURSUIT = "aggressive_pursuit"


class EvidenceItem(BaseModel):
    id: str
    statement: str
    evidence_class: EvidenceClass
    source: str
    domain: str
    sensitivity: Literal["public", "work", "private", "restricted", "root"] = "work"
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: Literal["active", "superseded", "rejected", "unresolved"] = "active"


class Capability(BaseModel):
    name: str
    level: CapabilityLevel
    confidence: Confidence
    aliases: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class CareerPreference(BaseModel):
    name: str
    weight: int = Field(default=0, ge=-5, le=5)
    keywords: list[str] = Field(default_factory=list)
    notes: str | None = None


class CompensationPolicy(BaseModel):
    currency: str = "USD"
    minimum_monthly: float | None = None
    target_monthly: float | None = None
    anchor_monthly: float | None = None


class ExperienceEntry(BaseModel):
    company: str
    title: str
    start: str | None = None
    end: str | None = None
    domain: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str
    qualification: str
    period: str | None = None


class CareerProfile(BaseModel):
    profile_id: str
    display_name: str
    headline: str | None = None
    location: str | None = None
    years_experience: float | None = None
    target_titles: list[str] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    preferences: list[CareerPreference] = Field(default_factory=list)
    experiences: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    remote_only: bool = True
    allowed_regions: list[str] = Field(default_factory=lambda: ["worldwide", "remote"])
    compensation: CompensationPolicy = Field(default_factory=CompensationPolicy)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class Job(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str | None = None
    remote: bool | None = None
    source: str = "manual"
    url: str | None = None
    salary_min_monthly: float | None = None
    salary_max_monthly: float | None = None
    currency: str | None = None


class RequirementAssessment(BaseModel):
    requirement: str
    fit: RequirementFit
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)


class CareerValue(BaseModel):
    compensation: Literal["poor", "weak", "unknown", "acceptable", "good", "strong"] = "unknown"
    growth: Literal["low", "unknown", "medium", "high"] = "unknown"
    interesting_work: Literal["low", "unknown", "medium", "high"] = "unknown"
    global_exposure: Literal["low", "unknown", "medium", "high"] = "unknown"
    future_positioning: Literal["low", "unknown", "medium", "high"] = "unknown"


class JobEvaluation(BaseModel):
    job_id: str
    summary: str
    eligible: bool
    role_interpretation: str
    requirement_assessments: list[RequirementAssessment] = Field(default_factory=list)
    strong_matches: list[str] = Field(default_factory=list)
    learnable_gaps: list[str] = Field(default_factory=list)
    hard_blockers: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    interest_score: int = Field(ge=0, le=100)
    career_value: CareerValue
    pursuit_decision: PursuitDecision
    positioning: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    next_action: str


class FeedbackEvent(BaseModel):
    id: str
    job_id: str | None = None
    evaluation_id: str | None = None
    feedback_type: str
    statement: str
    created_at: str


class ModelUpdateProposal(BaseModel):
    id: str
    model_path: str
    previous: object | None = None
    proposed: object | None = None
    reason: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    previous_confidence: float | None = Field(default=None, ge=0, le=1)
    proposed_confidence: float | None = Field(default=None, ge=0, le=1)
    alternative_explanations: list[str] = Field(default_factory=list)
    status: Literal["draft", "pending_review", "approved", "rejected", "merged"] = "draft"


class ApplicationState(str, Enum):
    DISCOVERED = "discovered"
    NORMALIZED = "normalized"
    EVALUATED = "evaluated"
    REJECTED = "rejected"
    SHORTLISTED = "shortlisted"
    PREPARING = "preparing"
    BLOCKED = "blocked"
    READY = "ready"
    SUBMITTED = "submitted"
    FAILED = "failed"
    RECRUITER_CONTACTED = "recruiter_contacted"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    NEGOTIATING = "negotiating"
    CLOSED = "closed"


class ApplicationAnswer(BaseModel):
    key: str
    value: str
    aliases: list[str] = Field(default_factory=list)
    verified: bool = False
    sensitivity: Literal["normal", "sensitive", "restricted"] = "normal"
    allow_automatic_use: bool = False


class ApplicationQuestion(BaseModel):
    key: str
    label: str
    required: bool = False
    input_type: str = "text"
    options: list[str] = Field(default_factory=list)
    selector: str | None = None


class ApplicationPlan(BaseModel):
    job_id: str
    ats: str
    state: ApplicationState
    known_answers: dict[str, str] = Field(default_factory=dict)
    blocked_questions: list[ApplicationQuestion] = Field(default_factory=list)
    unknown_questions: list[ApplicationQuestion] = Field(default_factory=list)
    can_submit_automatically: bool = False
    reasons: list[str] = Field(default_factory=list)


class ResumeExperience(BaseModel):
    company: str
    title: str
    period: str | None = None
    highlights: list[str] = Field(default_factory=list)


class ResumePacket(BaseModel):
    job_id: str
    headline: str
    summary: str
    selected_skills: list[str] = Field(default_factory=list)
    experiences: list[ResumeExperience] = Field(default_factory=list)
    omitted_claims: list[str] = Field(default_factory=list)
    markdown: str


class RecruiterAdvice(BaseModel):
    stage: Literal["unknown", "screening", "interview", "compensation", "offer", "follow_up"]
    intent: str
    leverage_signals: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommended_action: str
    draft_reply: str


class NegotiationContext(BaseModel):
    current_offer_monthly: float | None = None
    currency: str = "USD"
    company_initiated: bool = False
    interview_rounds: int = 0
    urgency_signals: int = 0
    strong_positive_signals: int = 0
    competing_processes: int = 0
    published_max_monthly: float | None = None
    non_salary_priorities: list[str] = Field(default_factory=list)


class NegotiationAdvice(BaseModel):
    leverage: Literal["weak", "limited", "balanced", "strong", "very_strong"]
    recommended_counter_monthly: float | None = None
    walk_away_below_monthly: float | None = None
    strategy: list[str] = Field(default_factory=list)
    non_salary_levers: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    requires_approval: bool = True
