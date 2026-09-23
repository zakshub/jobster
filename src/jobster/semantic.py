from __future__ import annotations

import json
import os

import httpx

from .models import CareerProfile, Job, JobEvaluation, PursuitDecision


SEMANTIC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "summary", "eligible", "role_interpretation", "requirement_assessments",
        "strong_matches", "learnable_gaps", "hard_blockers", "unknowns",
        "interest_score", "career_value", "pursuit_decision", "positioning",
        "confidence", "reasons", "next_action"
    ],
    "properties": {
        "summary": {"type": "string"},
        "eligible": {"type": "boolean"},
        "role_interpretation": {"type": "string"},
        "requirement_assessments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["requirement", "fit", "reason", "evidence_ids"],
                "properties": {
                    "requirement": {"type": "string"},
                    "fit": {"type": "string", "enum": [
                        "strong_evidence", "supported", "adjacent", "learnable",
                        "weak_evidence", "not_claimed", "hard_blocker", "unknown"
                    ]},
                    "reason": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "strong_matches": {"type": "array", "items": {"type": "string"}},
        "learnable_gaps": {"type": "array", "items": {"type": "string"}},
        "hard_blockers": {"type": "array", "items": {"type": "string"}},
        "unknowns": {"type": "array", "items": {"type": "string"}},
        "interest_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "career_value": {
            "type": "object",
            "additionalProperties": False,
            "required": ["compensation", "growth", "interesting_work", "global_exposure", "future_positioning"],
            "properties": {
                "compensation": {"type": "string", "enum": ["poor", "weak", "unknown", "acceptable", "good", "strong"]},
                "growth": {"type": "string", "enum": ["low", "unknown", "medium", "high"]},
                "interesting_work": {"type": "string", "enum": ["low", "unknown", "medium", "high"]},
                "global_exposure": {"type": "string", "enum": ["low", "unknown", "medium", "high"]},
                "future_positioning": {"type": "string", "enum": ["low", "unknown", "medium", "high"]}
            }
        },
        "pursuit_decision": {"type": "string", "enum": [
            "ignore", "watch", "low_priority", "apply", "high_priority", "aggressive_pursuit"
        ]},
        "positioning": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "next_action": {"type": "string"}
    }
}


class SemanticCareerBrain:
    """LLM reasoning layer with deterministic hard-rule preservation."""

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 90.0):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("JOBSTER_OPENAI_MODEL", "gpt-5.6-sol")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def evaluate(self, profile: CareerProfile, job: Job, baseline: JobEvaluation) -> JobEvaluation:
        if not self.api_key:
            return baseline

        developer = (
            "You are Jobster CareerBrain. Evaluate one job for one candidate. "
            "Use only facts contained in the supplied profile and job. Never invent experience, "
            "education, authorization, salary history, achievements, metrics, or capabilities. "
            "Distinguish fundamental gaps from learnable gaps. Treat unknown as valid. "
            "Reason about actual role content, likely interest, stretch potential, career value, "
            "and truthful positioning. The deterministic baseline contains hard policy signals. "
            "Do not override a deterministic hard blocker."
        )
        user = json.dumps(
            {
                "profile": profile.model_dump(mode="json"),
                "job": job.model_dump(mode="json"),
                "deterministic_baseline": baseline.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "store": False,
                "reasoning": {"effort": "high"},
                "input": [
                    {"role": "developer", "content": [{"type": "input_text", "text": developer}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user}]},
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "jobster_job_evaluation",
                        "strict": True,
                        "schema": SEMANTIC_SCHEMA,
                    }
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        text = _output_text(payload)
        data = json.loads(text)
        data["job_id"] = job.id

        semantic = JobEvaluation.model_validate(data)

        merged_blockers = list(dict.fromkeys([*baseline.hard_blockers, *semantic.hard_blockers]))
        merged_unknowns = list(dict.fromkeys([*baseline.unknowns, *semantic.unknowns]))
        if baseline.hard_blockers:
            semantic.eligible = False
            semantic.pursuit_decision = PursuitDecision.IGNORE
            semantic.next_action = "Do not apply unless Zak explicitly overrides the hard blocker"
        semantic.hard_blockers = merged_blockers
        semantic.unknowns = merged_unknowns
        return semantic


def _output_text(payload: dict) -> str:
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    raise RuntimeError("Semantic provider returned no output text")
