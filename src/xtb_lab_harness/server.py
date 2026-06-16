from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from xtb_lab_harness.tools.analyze import calculate_candidate_batch
from xtb_lab_harness.tools.compare import generate_evidence_table
from xtb_lab_harness.tools.evaluate import evaluate_candidates, run_experiment_pipeline
from xtb_lab_harness.tools.optimize import calculate_candidate
from xtb_lab_harness.tools.report import generate_full_experiment_report
from xtb_lab_harness.xtb.schemas import CandidateResult

mcp = FastMCP(
    "xtb-lab-harness",
    instructions=(
        "MCP tool server for xTB computational chemistry and rule-based MAS evaluation. "
        "Use run_experiment_pipeline for end-to-end manifest-driven workflows."
    ),
)


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model


@mcp.tool(name="calculate_candidate")
def calculate_candidate_tool(
    candidate_id: str,
    xyz_path: str,
    gfn: int = 2,
    charge: int | None = None,
    uhf: int | None = None,
) -> dict[str, Any]:
    """Run xTB geometry optimization and parse energy, charges, and dipole for one .xyz file."""
    result = calculate_candidate(
        candidate_id=candidate_id,
        xyz_path=xyz_path,
        gfn=gfn,
        charge=charge,
        uhf=uhf,
    )
    return _dump_model(result)


@mcp.tool(name="calculate_candidate_batch")
def calculate_candidate_batch_tool(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run xTB for multiple candidates. Each item needs candidate_id and xyz_path."""
    batch = calculate_candidate_batch(candidates)
    return _dump_model(batch)


@mcp.tool(name="generate_evidence_table")
def generate_evidence_table_tool(
    results: list[dict[str, Any]],
    reference_candidate_id: str | None = None,
    save_report_path: str | None = None,
) -> dict[str, Any]:
    """Rank candidates and return a markdown evidence table from xTB JSON results."""
    parsed = [CandidateResult.model_validate(item) for item in results]
    table = generate_evidence_table(parsed, reference_candidate_id=reference_candidate_id)

    if save_report_path:
        from xtb_lab_harness.reports.markdown import save_report_markdown

        save_report_markdown(table, save_report_path)

    return _dump_model(table)


@mcp.tool(name="evaluate_candidates")
def evaluate_candidates_tool(
    experiment_objective: str,
    candidate_specs: list[dict[str, Any]],
    xtb_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run specialist MAS agents on parsed xTB results and return scored evaluations."""
    return evaluate_candidates(experiment_objective, candidate_specs, xtb_results)


@mcp.tool(name="run_experiment_pipeline")
def run_experiment_pipeline_tool(
    manifest_path: str,
    report_output_path: str | None = None,
    reference_candidate_id: str | None = None,
) -> dict[str, Any]:
    """End-to-end: manifest JSON → xTB batch → MAS evaluation → 14-section report."""
    return run_experiment_pipeline(
        manifest_path,
        report_output_path=report_output_path,
        reference_candidate_id=reference_candidate_id,
    )


@mcp.tool(name="generate_experiment_report")
def generate_experiment_report_tool(
    experiment_objective: str,
    hypothesis: str,
    candidate_specs: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
    reference_candidate_id: str | None = None,
    save_path: str | None = None,
) -> dict[str, Any]:
    """Build the full 14-section experiment design report from evaluation JSON."""
    return generate_full_experiment_report(
        experiment_objective,
        hypothesis,
        candidate_specs,
        evaluations,
        reference_candidate_id=reference_candidate_id,
        save_path=save_path,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
