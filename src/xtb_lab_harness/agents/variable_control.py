from __future__ import annotations

from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CandidateResult


class VariableControlAgent:
    name = "Variable Control Agent"

    def review(
        self,
        candidate: CandidateSpec,
        result: CandidateResult | None = None,
        *,
        experiment_objective: str,
    ) -> AgentReview:
        return self.review_for_experiment(candidate, experiment_objective=experiment_objective)

    def review_for_experiment(
        self,
        candidate: CandidateSpec,
        *,
        experiment_objective: str,
    ) -> AgentReview:
        objective = experiment_objective.lower()
        independent: list[str] = ["후보 물질 종류"]
        dependent: list[str] = ["관찰 지표(흡광, pH 변화, 혼탁도 등 — 목적에 따라 조정)"]
        controlled: list[str] = ["온도", "농도", "용매", "반응 시간", "교반 속도"]

        if any(k in objective for k in ("polar", "극성", "dipole", "쌍극자")):
            dependent.append("극성/쌍극자 관련 관찰량")
        if any(k in objective for k in ("solvent", "용매", "dissolv", "용해")):
            independent.append("용매 극성")
            controlled.append("용질 농도")

        evidence = [
            f"독립변인: {', '.join(independent)}",
            f"종속변인: {', '.join(dependent)}",
            f"통제변인: {', '.join(controlled)}",
            "대조군: 용매만/blank 또는 기준 물질(water 등) 권장",
            "반복: 최소 3회 기술적 반복 제안",
        ]

        score = 0.8 if len(controlled) >= 4 else 0.6

        return AgentReview(
            agent_name=self.name,
            candidate_id=candidate.candidate_id,
            score=score,
            summary="실험 목적을 바탕으로 변인 분류 및 통제 조건 초안을 제시함.",
            evidence_points=evidence,
            concerns=[],
            recommendation="include",
        )
