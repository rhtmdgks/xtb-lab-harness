from __future__ import annotations

from xtb_lab_harness.agents.base import SpecialistAgent
from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


class ElectrostaticAgent(SpecialistAgent):
    name = "Electrostatic Interaction Agent"

    def review(
        self,
        candidate: CandidateSpec,
        result: CandidateResult,
        *,
        experiment_objective: str,
    ) -> AgentReview:
        if result.calculation_status != CalculationStatus.SUCCESS:
            return AgentReview(
                agent_name=self.name,
                candidate_id=candidate.candidate_id,
                score=0.0,
                summary="xTB 결과 없음 — 정전기적 해석 불가.",
                recommendation="exclude",
            )

        dipole = result.dipole_moment_debye or 0.0
        q_pos = result.charge_summary.max_positive_charge or 0.0
        q_neg = result.charge_summary.max_negative_charge or 0.0
        spread = q_pos - q_neg

        evidence = [
            f"쌍극자 모멘트: {dipole:.2f} D",
            f"부분전하 범위: {q_neg:.3f} ~ {q_pos:.3f} e",
            f"전하 요약: {result.charge_summary.charge_distribution_note or 'N/A'}",
        ]

        score = 0.3
        if dipole >= 1.0:
            score += 0.25
        if dipole >= 2.5:
            score += 0.15
        if spread >= 0.8:
            score += 0.2
        if spread >= 1.2:
            score += 0.1

        polarity_note = "극성 분자" if dipole >= 1.5 else "약극성~비극성 경향"
        summary = (
            f"{polarity_note}로 분류됨. xTB 부분전하·쌍극자 지표를 바탕으로 "
            "정전기적 상호작용 가능성을 정성 평가함."
        )

        concerns: list[str] = []
        if dipole < 0.5:
            concerns.append("쌍극자 모멘트가 매우 작아 극성 기반 효과 관찰은 제한적일 수 있음.")

        return AgentReview(
            agent_name=self.name,
            candidate_id=candidate.candidate_id,
            score=min(score, 1.0),
            summary=summary,
            evidence_points=evidence,
            concerns=concerns,
            recommendation="include" if score >= 0.4 else "caution",
        )
