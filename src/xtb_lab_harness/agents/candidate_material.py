from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


def screen_candidates(
    candidates: list[CandidateSpec],
    *,
    experiment_objective: str,
) -> tuple[list[CandidateSpec], list[tuple[CandidateSpec, str]]]:
    """First-pass screening before xTB: xyz exists and basic suitability."""
    accepted: list[CandidateSpec] = []
    rejected: list[tuple[CandidateSpec, str]] = []

    for candidate in candidates:
        xyz = Path(candidate.xyz_path).expanduser()
        if not xyz.exists():
            rejected.append((candidate, f"구조 파일 없음: {candidate.xyz_path}"))
            continue
        if candidate.safety_flags:
            rejected.append(
                (candidate, f"사전 안전 플래그: {', '.join(candidate.safety_flags)}"),
            )
            continue
        accepted.append(candidate)

    return accepted, rejected


def review_candidate_material(
    candidate: CandidateSpec,
    result: CandidateResult,
    *,
    experiment_objective: str,
) -> AgentReview:
    xyz = Path(candidate.xyz_path)
    atom_count = _count_atoms(xyz) if xyz.exists() else None
    evidence: list[str] = []
    concerns: list[str] = []

    if candidate.notes:
        evidence.append(f"후보 메모: {candidate.notes}")
    if atom_count is not None:
        evidence.append(f"입력 구조 원자 수: {atom_count}")

    if result.calculation_status != CalculationStatus.SUCCESS:
        return AgentReview(
            agent_name="Candidate Material Agent",
            candidate_id=candidate.candidate_id,
            score=0.0,
            summary="xTB 계산 실패로 후보 적합성을 확인할 수 없음.",
            evidence_points=evidence,
            concerns=[result.error_message or "xTB 계산 실패"],
            recommendation="exclude",
        )

    score = 0.7
    if candidate.notes and any(
        keyword in experiment_objective.lower() + candidate.notes.lower()
        for keyword in ("polar", "극성", "solvent", "용매", "interaction", "상호작용")
    ):
        score += 0.15
        evidence.append("실험 목적·후보 설명 간 키워드 정합성 있음")
    if atom_count and atom_count <= 20:
        score += 0.15
        evidence.append("소형 분자로 R&E 실험 후보로 다루기 용이")

    return AgentReview(
        agent_name="Candidate Material Agent",
        candidate_id=candidate.candidate_id,
        score=min(score, 1.0),
        summary="사전 준비된 .xyz 구조가 존재하며 xTB 계산이 완료되어 1차 후보로 유지 가능.",
        evidence_points=evidence,
        concerns=concerns,
        recommendation="include",
    )


def _count_atoms(xyz_path: Path) -> int:
    lines = xyz_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0
    try:
        return int(lines[0].strip())
    except ValueError:
        return max(len(lines) - 2, 0)
