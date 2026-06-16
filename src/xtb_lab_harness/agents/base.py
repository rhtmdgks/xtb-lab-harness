from __future__ import annotations

from abc import ABC, abstractmethod

from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CandidateResult


class SpecialistAgent(ABC):
    name: str

    @abstractmethod
    def review(
        self,
        candidate: CandidateSpec,
        result: CandidateResult,
        *,
        experiment_objective: str,
    ) -> AgentReview:
        """Evaluate one candidate from this agent's perspective."""
