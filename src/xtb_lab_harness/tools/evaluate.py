from __future__ import annotations

from xtb_lab_harness.agents.orchestrator import Orchestrator, load_manifest
from xtb_lab_harness.agents.schemas import ExperimentManifest
from xtb_lab_harness.xtb.schemas import CandidateResult


def evaluate_candidates(
    experiment_objective: str,
    candidate_specs: list[dict],
    xtb_results: list[dict],
) -> list[dict]:
    """Run MAS specialist agents on existing xTB JSON results."""
    manifest = ExperimentManifest(
        experiment_objective=experiment_objective,
        candidates=candidate_specs,  # type: ignore[arg-type]
    )
    parsed_results = [CandidateResult.model_validate(r) for r in xtb_results]
    evaluations = Orchestrator().evaluate_from_xtb_results(manifest, parsed_results)
    return [e.model_dump(mode="json") for e in evaluations]


def run_experiment_pipeline(
    manifest_path: str,
    *,
    report_output_path: str | None = None,
    reference_candidate_id: str | None = None,
) -> dict:
    manifest = load_manifest(manifest_path)
    result = Orchestrator().run(
        manifest,
        report_output_path=report_output_path or "data/reports/latest_report.md",
        reference_candidate_id=reference_candidate_id,
    )
    return result.model_dump(mode="json")
