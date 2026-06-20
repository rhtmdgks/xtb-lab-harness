from __future__ import annotations

from xtb_lab_harness.reports.labels import calculation_status_ko, geometry_optimized_ko
from xtb_lab_harness.xtb.schemas import (
    CalculationStatus,
    CandidateResult,
    EvidenceTable,
    EvidenceTableRow,
)

HARTREE_TO_KCAL_MOL = 627.5094740631


def _relative_energy_kcal_mol(
    energy: float | None,
    reference: float | None,
) -> float | None:
    if energy is None or reference is None:
        return None
    return (energy - reference) * HARTREE_TO_KCAL_MOL


def generate_evidence_table(
    results: list[CandidateResult],
    *,
    reference_candidate_id: str | None = None,
) -> EvidenceTable:
    """Build a ranked evidence table from candidate calculation results."""
    successful = [
        r for r in results if r.calculation_status == CalculationStatus.SUCCESS and r.total_energy_hartree is not None
    ]

    reference_energy: float | None = None
    if reference_candidate_id:
        for result in successful:
            if result.candidate_id == reference_candidate_id:
                reference_energy = result.total_energy_hartree
                break
    elif successful:
        reference_energy = min(r.total_energy_hartree for r in successful if r.total_energy_hartree is not None)

    ranked = sorted(
        successful,
        key=lambda r: r.total_energy_hartree if r.total_energy_hartree is not None else float("inf"),
    )

    rows: list[EvidenceTableRow] = []
    for rank, result in enumerate(ranked, start=1):
        rows.append(
            EvidenceTableRow(
                candidate_id=result.candidate_id,
                calculation_status=result.calculation_status,
                geometry_optimized=result.geometry_optimized,
                total_energy_hartree=result.total_energy_hartree,
                dipole_moment_debye=result.dipole_moment_debye,
                max_positive_charge=result.charge_summary.max_positive_charge,
                max_negative_charge=result.charge_summary.max_negative_charge,
                relative_energy_kcal_mol=_relative_energy_kcal_mol(
                    result.total_energy_hartree,
                    reference_energy,
                ),
                rank=rank,
            )
        )

    for result in results:
        if result.calculation_status != CalculationStatus.SUCCESS:
            rows.append(
                EvidenceTableRow(
                    candidate_id=result.candidate_id,
                    calculation_status=result.calculation_status,
                    geometry_optimized=result.geometry_optimized,
                    total_energy_hartree=result.total_energy_hartree,
                    dipole_moment_debye=result.dipole_moment_debye,
                    max_positive_charge=result.charge_summary.max_positive_charge,
                    max_negative_charge=result.charge_summary.max_negative_charge,
                )
            )

    markdown = _render_markdown(rows, reference_candidate_id)
    return EvidenceTable(
        rows=rows,
        markdown=markdown,
        reference_candidate_id=reference_candidate_id,
    )


def _render_markdown(
    rows: list[EvidenceTableRow],
    reference_candidate_id: str | None,
) -> str:
    header = (
        "| 순위 | 후보 ID | 계산 상태 | E (Eh) | ΔE (kcal/mol) | μ (D) | q⁺ max | q⁻ min | 최적화 |"
    )
    separator = "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |"

    lines = [
        "# xTB 후보 증거 표",
        "",
    ]
    if reference_candidate_id:
        lines.append(f"기준 후보: `{reference_candidate_id}`")
        lines.append("")

    lines.extend([header, separator])

    for row in rows:
        rank = str(row.rank) if row.rank is not None else "—"
        energy = f"{row.total_energy_hartree:.6f}" if row.total_energy_hartree is not None else "—"
        delta = (
            f"{row.relative_energy_kcal_mol:+.2f}"
            if row.relative_energy_kcal_mol is not None
            else "—"
        )
        dipole = f"{row.dipole_moment_debye:.2f}" if row.dipole_moment_debye is not None else "—"
        q_pos = f"{row.max_positive_charge:.3f}" if row.max_positive_charge is not None else "—"
        q_neg = f"{row.max_negative_charge:.3f}" if row.max_negative_charge is not None else "—"
        opt = geometry_optimized_ko(row.geometry_optimized)

        lines.append(
            f"| {rank} | {row.candidate_id} | {calculation_status_ko(row.calculation_status)} | "
            f"{energy} | {delta} | {dipole} | {q_pos} | {q_neg} | {opt} |"
        )

    return "\n".join(lines)
