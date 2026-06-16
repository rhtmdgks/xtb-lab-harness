from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.tools.compare import generate_evidence_table
from xtb_lab_harness.xtb.schemas import CandidateResult, EvidenceTable


def save_report_markdown(table: EvidenceTable, output_path: str | Path) -> str:
    """Persist an evidence table markdown report and return the file path."""
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(table.markdown, encoding="utf-8")
    return str(path)


def build_report_from_results(
    results: list[CandidateResult],
    *,
    reference_candidate_id: str | None = None,
    output_path: str | None = None,
) -> EvidenceTable:
    table = generate_evidence_table(results, reference_candidate_id=reference_candidate_id)
    if output_path:
        save_report_markdown(table, output_path)
    return table
