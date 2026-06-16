from __future__ import annotations

from xtb_lab_harness.agents.base import SpecialistAgent
from xtb_lab_harness.agents.evaluator import score_structural_stability
from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


class StructuralStabilityAgent(SpecialistAgent):
    name = "Structural Stability Agent"

    def review(
        self,
        candidate: CandidateSpec,
        result: CandidateResult,
        *,
        experiment_objective: str,
    ) -> AgentReview:
        score = score_structural_stability(result)
        evidence: list[str] = []
        concerns: list[str] = []

        if result.calculation_status != CalculationStatus.SUCCESS:
            return AgentReview(
                agent_name=self.name,
                candidate_id=candidate.candidate_id,
                score=0.0,
                summary="계산 실패 — 구조 안정성 평가 불가.",
                concerns=[result.error_message or "xTB 실패"],
                recommendation="exclude",
            )

        evidence.append(f"geometry_optimized={result.geometry_optimized}")
        if result.total_energy_hartree is not None:
            evidence.append(f"total_energy_hartree={result.total_energy_hartree:.6f}")
        if result.warnings:
            concerns.extend(result.warnings[:3])

        if not result.geometry_optimized:
            concerns.append("구조 최적화 수렴이 확인되지 않음")
            recommendation = "caution"
        else:
            recommendation = "include"

        summary = (
            "구조 최적화 수렴 여부와 총 에너지 파싱 결과를 기준으로 "
            "구조적 안정성을 평가함."
        )

        return AgentReview(
            agent_name=self.name,
            candidate_id=candidate.candidate_id,
            score=score,
            summary=summary,
            evidence_points=evidence,
            concerns=concerns,
            recommendation=recommendation,
        )
