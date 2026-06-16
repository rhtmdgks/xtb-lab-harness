from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from xtb_lab_harness.xtb.schemas import CandidateResult


class CandidateSpec(BaseModel):
    candidate_id: str
    xyz_path: str
    charge: int | None = None
    uhf: int | None = None
    gfn: int = 2
    notes: str | None = None
    safety_flags: list[str] = Field(default_factory=list)


class ExperimentManifest(BaseModel):
    experiment_objective: str
    xtb_settings: dict[str, Any] = Field(default_factory=lambda: {"gfn": 2})
    candidates: list[CandidateSpec]


class AgentReview(BaseModel):
    agent_name: str
    candidate_id: str
    score: float = Field(ge=0.0, le=1.0)
    summary: str
    evidence_points: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    recommendation: Literal["include", "exclude", "caution"] = "include"


class DimensionScores(BaseModel):
    electrostatic: float = 0.0
    structural_stability: float = 0.0
    experimental_feasibility: float = 0.0
    safety: float = 0.0
    variable_control: float = 0.0
    critic_reliability: float = 0.0


class CandidateEvaluation(BaseModel):
    candidate_id: str
    xtb_result: CandidateResult
    agent_reviews: list[AgentReview]
    dimension_scores: DimensionScores
    final_score: float
    rank: int | None = None
    excluded: bool = False
    exclusion_reason: str | None = None


class ExperimentRunResult(BaseModel):
    experiment_objective: str
    hypothesis: str
    candidate_specs: list[CandidateSpec]
    xtb_results: list[CandidateResult]
    evaluations: list[CandidateEvaluation]
    evidence_table_markdown: str
    report_markdown: str
    report_path: str | None = None
