from __future__ import annotations

from xtb_lab_harness.xtb.schemas import CandidateResult


def score_structural_stability(result: CandidateResult) -> float:
    """Local heuristic score (0–1) for structural stability from xTB output."""
    if result.calculation_status.value != "success":
        return 0.0
    score = 0.5
    if result.geometry_optimized:
        score += 0.35
    if result.total_energy_hartree is not None:
        score += 0.15
    return min(score, 1.0)
