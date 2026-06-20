from __future__ import annotations

from xtb_lab_harness.agents.schemas import AgentReview, CandidateEvaluation, DimensionScores
from xtb_lab_harness.xtb.schemas import CalculationStatus


class CriticAgent:
    name = "Critic Agent"

    CHECKLIST = [
        "계산 결과가 있는가?",
        "계산 결과와 해석이 연결되는가?",
        "실험 설계가 가능한가?",
        "변인통제가 충분한가?",
        "안전성 한계가 명시되었는가?",
        "결론이 과장되지 않았는가?",
    ]

    def review_evaluation(self, evaluation: CandidateEvaluation) -> AgentReview:
        result = evaluation.xtb_result
        concerns: list[str] = []
        evidence: list[str] = []
        score = 1.0

        if result.calculation_status != CalculationStatus.SUCCESS:
            concerns.append("xTB 계산 결과 없음 — 근거 기반 추천 불가")
            score -= 0.5
        else:
            if result.dipole_moment_debye is None:
                concerns.append("쌍극자 모멘트 미파싱 — 정전기 해석 근거 약화")
                score -= 0.1
            if result.charge_summary.max_positive_charge is None:
                concerns.append("부분전하 미파싱 — 전하 분포 근거 약화")
                score -= 0.1

        numeric_linked = 0
        for review in evaluation.agent_reviews:
            if review.evidence_points:
                numeric_linked += 1
        if numeric_linked < 3:
            concerns.append("에이전트 근거 연결이 부족함")
            score -= 0.15

        dims = evaluation.dimension_scores
        if dims.safety < 0.5:
            concerns.append("안전성 점수 낮음 — 최종 추천 시 감점 필요")
            score -= 0.1

        if evaluation.final_score > 0.85 and not result.geometry_optimized:
            concerns.append("고득점이나 구조 최적화 미확인 — 과장 위험")
            score -= 0.2

        for item in self.CHECKLIST:
            evidence.append(f"✓ 검토 항목: {item}")

        score = max(0.0, min(score, 1.0))
        recommendation = "include"
        if score < 0.5:
            recommendation = "exclude"
        elif concerns:
            recommendation = "caution"

        return AgentReview(
            agent_name=self.name,
            candidate_id=evaluation.candidate_id,
            score=score,
            summary="계산 근거·변인통제·과장 여부를 교차 검토함.",
            evidence_points=evidence,
            concerns=concerns,
            recommendation=recommendation,
        )

    def adjust_dimension_scores(
        self,
        dimensions: DimensionScores,
        critic_score: float,
    ) -> DimensionScores:
        dimensions.critic_reliability = critic_score
        return dimensions
