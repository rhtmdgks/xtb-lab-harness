from __future__ import annotations

from xtb_lab_harness.agents.schemas import CandidateEvaluation, ExperimentManifest
from xtb_lab_harness.reports.experiment import generate_experiment_report
from xtb_lab_harness.tools.compare import generate_evidence_table
from xtb_lab_harness.xtb.schemas import CandidateResult


def generate_full_experiment_report(
    experiment_objective: str,
    hypothesis: str,
    candidate_specs: list[dict],
    evaluations: list[dict],
    *,
    reference_candidate_id: str | None = None,
    save_path: str | None = None,
) -> dict:
    manifest = ExperimentManifest(
        experiment_objective=experiment_objective,
        candidates=candidate_specs,  # type: ignore[arg-type]
    )
    parsed_evals = [CandidateEvaluation.model_validate(e) for e in evaluations]
    evidence = generate_evidence_table(
        [CandidateResult.model_validate(e["xtb_result"]) for e in evaluations],
        reference_candidate_id=reference_candidate_id,
    )
    markdown = generate_experiment_report(
        experiment_objective=experiment_objective,
        hypothesis=hypothesis,
        manifest=manifest,
        evaluations=parsed_evals,
        evidence_table_markdown=evidence.markdown,
    )
    if save_path:
        from pathlib import Path

        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")

    return {"markdown": markdown, "report_path": save_path}
