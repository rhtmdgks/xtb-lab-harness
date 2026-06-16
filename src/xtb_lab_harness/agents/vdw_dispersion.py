from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.agents.base import SpecialistAgent
from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


class VdwDispersionAgent(SpecialistAgent):
    name = "van der Waals / Dispersion Interpretation Agent"

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
                summary="xTB 결과 없음 — 비공유 상호작용 해석 불가.",
                recommendation="exclude",
            )

        atom_count = _count_atoms(Path(candidate.xyz_path))
        dipole = result.dipole_moment_debye or 0.0
        optimized = result.geometry_optimized

        evidence = [
            f"원자 수(입력 .xyz): {atom_count}",
            f"구조 최적화: {'성공' if optimized else '미확인/실패'}",
            f"쌍극자 모멘트: {dipole:.2f} D",
        ]
        if result.total_energy_hartree is not None:
            evidence.append(f"총 에너지: {result.total_energy_hartree:.6f} Eh")

        score = 0.35
        if atom_count >= 5:
            score += 0.2
        if atom_count >= 9:
            score += 0.15
        if optimized:
            score += 0.2
        if dipole < 2.0:
            score += 0.1

        summary = (
            "xTB 계산 결과를 바탕으로 분산력/반데르발스 상호작용 가능성의 "
            "**경향성**을 해석함 (정밀 분해 계산 아님)."
        )

        return AgentReview(
            agent_name=self.name,
            candidate_id=candidate.candidate_id,
            score=min(score, 1.0),
            summary=summary,
            evidence_points=evidence,
            concerns=[],
            recommendation="include",
        )


def _count_atoms(xyz_path: Path) -> int:
    if not xyz_path.exists():
        return 0
    lines = xyz_path.read_text(encoding="utf-8").splitlines()
    try:
        return int(lines[0].strip())
    except (ValueError, IndexError):
        return 0
