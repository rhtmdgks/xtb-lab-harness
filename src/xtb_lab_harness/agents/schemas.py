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


class DebateMessage(BaseModel):
    agent_name: str
    round_number: int
    message: str
    responds_to: str | None = None
    stance: Literal["support", "challenge", "revise", "concede", "synthesize"] = "support"


class DebateRound(BaseModel):
    round_number: int
    messages: list[DebateMessage]
    round_synthesis: str


class CandidateDebate(BaseModel):
    candidate_id: str
    rounds: list[DebateRound]
    consensus_summary: str
    revised_recommendation: Literal["include", "exclude", "caution"]
    score_adjustment: float = Field(default=0.0, ge=-0.2, le=0.2)


class TaskPlan(BaseModel):
    user_command: str
    experiment_objective: str
    hypothesis: str
    assigned_agents: list[str]
    debate_rounds: int = 2
    orchestrator_reasoning: str
    focus_points: list[str] = Field(default_factory=list)


class CandidateEvaluation(BaseModel):
    candidate_id: str
    xtb_result: CandidateResult
    agent_reviews: list[AgentReview]
    dimension_scores: DimensionScores
    final_score: float
    rank: int | None = None
    excluded: bool = False
    exclusion_reason: str | None = None
    debate: CandidateDebate | None = None


class ExperimentRunResult(BaseModel):
    user_command: str | None = None
    task_plan: TaskPlan | None = None
    experiment_objective: str
    hypothesis: str
    candidate_specs: list[CandidateSpec]
    xtb_results: list[CandidateResult]
    evaluations: list[CandidateEvaluation]
    debates: list[CandidateDebate] = Field(default_factory=list)
    orchestrator_synthesis: str | None = None
    evidence_table_markdown: str
    report_markdown: str
    report_path: str | None = None
