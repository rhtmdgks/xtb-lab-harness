from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from xtb_lab_harness.tools.analyze import calculate_candidate_batch
from xtb_lab_harness.tools.compare import generate_evidence_table
from xtb_lab_harness.tools.optimize import calculate_candidate
from xtb_lab_harness.xtb.schemas import CandidateResult

mcp = FastMCP(
    "xtb-lab-harness",
    instructions=(
        "MCP tool server for xTB computational chemistry. "
        "Exposes geometry optimization and property extraction for .xyz candidates. "
        "MAS orchestration belongs on the MCP client side."
    ),
)


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model


@mcp.tool()
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


@mcp.tool()
def calculate_candidate_batch_tool(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run xTB for multiple candidates. Each item needs candidate_id and xyz_path."""
    batch = calculate_candidate_batch(candidates)
    return _dump_model(batch)


@mcp.tool()
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
