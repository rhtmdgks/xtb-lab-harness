from __future__ import annotations

import shutil

import pytest

from xtb_lab_harness.agents.electrostatic import ElectrostaticAgent
from xtb_lab_harness.agents.orchestrator import Orchestrator, load_manifest
from xtb_lab_harness.agents.schemas import CandidateSpec
from xtb_lab_harness.tools.optimize import calculate_candidate
from xtb_lab_harness.xtb.schemas import CalculationStatus, ChargeSummary, CandidateResult


pytestmark = pytest.mark.skipif(
    shutil.which("xtb") is None,
    reason="xTB binary not available on PATH",
)


def test_water_parses_dipole_and_charges() -> None:
    result = calculate_candidate("water", "examples/water.xyz", gfn=2, charge=0)
    assert result.calculation_status == CalculationStatus.SUCCESS
    assert result.geometry_optimized is True
    assert result.total_energy_hartree is not None
    assert result.total_energy_hartree < -5.0
    assert result.dipole_moment_debye is not None
    assert result.dipole_moment_debye > 1.5
    assert result.charge_summary.max_positive_charge is not None
    assert result.charge_summary.max_negative_charge is not None


def test_polar_vs_nonpolar_electrostatic_scores_differ() -> None:
    water = calculate_candidate("water", "examples/water.xyz")
    methane = calculate_candidate("methane", "examples/methane.xyz")
    agent = ElectrostaticAgent()
    objective = "극성 용매와 비극성 용매의 상호작용 차이 비교"

    water_review = agent.review(
        CandidateSpec(candidate_id="water", xyz_path="examples/water.xyz"),
        water,
        experiment_objective=objective,
    )
    methane_review = agent.review(
        CandidateSpec(candidate_id="methane", xyz_path="examples/methane.xyz"),
        methane,
        experiment_objective=objective,
    )
    assert water_review.score > methane_review.score


def test_manifest_pipeline_produces_distinct_rankings() -> None:
    manifest = load_manifest("examples/candidates.json")
    manifest.candidates = [
        c for c in manifest.candidates if c.candidate_id in ("water", "methane", "ethanol")
    ]
    result = Orchestrator().run(
        manifest,
        report_output_path=None,
        reference_candidate_id="water",
        parallel_xtb=False,
    )
    scores = {e.candidate_id: e.final_score for e in result.evaluations if not e.excluded}
    assert len(scores) == 3
    assert len(set(scores.values())) > 1
    assert "17. 후속 연구" in result.report_markdown
    assert "후보 ID | 최적화" in result.report_markdown


def test_failed_candidate_handling() -> None:
    result = CandidateResult(
        candidate_id="missing",
        calculation_status=CalculationStatus.FAILED,
        error_message="Input .xyz not found",
    )
    agent = ElectrostaticAgent()
    review = agent.review(
        CandidateSpec(candidate_id="missing", xyz_path="does/not/exist.xyz"),
        result,
        experiment_objective="test",
    )
    assert review.score == 0.0
    assert review.recommendation == "exclude"
