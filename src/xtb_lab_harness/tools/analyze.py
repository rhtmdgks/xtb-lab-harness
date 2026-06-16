from __future__ import annotations

from xtb_lab_harness.tools.optimize import calculate_candidate
from xtb_lab_harness.xtb.schemas import BatchCalculationResult, CandidateResult


def calculate_candidate_batch(
    candidates: list[dict[str, str | int | None]],
) -> BatchCalculationResult:
    """Run xTB for multiple candidates.

    Each item: ``{"candidate_id": "water", "xyz_path": "examples/water.xyz", "charge": 0}``
  """
    results: list[CandidateResult] = []

    for item in candidates:
        candidate_id = str(item["candidate_id"])
        xyz_path = str(item["xyz_path"])
        gfn = int(item.get("gfn", 2))
        charge = item.get("charge")
        uhf = item.get("uhf")

        charge_int = int(charge) if charge is not None else None
        uhf_int = int(uhf) if uhf is not None else None

        try:
            result = calculate_candidate(
                candidate_id,
                xyz_path,
                gfn=gfn,
                charge=charge_int,
                uhf=uhf_int,
            )
        except Exception as exc:  # noqa: BLE001
            from xtb_lab_harness.xtb.schemas import CalculationStatus

            result = CandidateResult(
                candidate_id=candidate_id,
                calculation_status=CalculationStatus.FAILED,
                error_message=str(exc),
            )
        results.append(result)

    succeeded = sum(1 for r in results if r.calculation_status.value == "success")
    return BatchCalculationResult(
        results=results,
        succeeded=succeeded,
        failed=len(results) - succeeded,
    )
