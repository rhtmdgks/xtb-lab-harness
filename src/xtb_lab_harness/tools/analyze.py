from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from xtb_lab_harness.tools.optimize import calculate_candidate
from xtb_lab_harness.xtb.schemas import BatchCalculationResult, CandidateResult


def calculate_candidate_batch(
    candidates: list[dict[str, str | int | None]],
    *,
    parallel: bool = True,
    max_workers: int | None = None,
) -> BatchCalculationResult:
    """Run xTB for multiple candidates (parallel when parallel=True)."""
    if not parallel or len(candidates) <= 1:
        return _sequential_batch(candidates)

    results: list[CandidateResult] = []
    workers = max_workers or min(len(candidates), 4)

    def _one(item: dict) -> CandidateResult:
        candidate_id = str(item["candidate_id"])
        xyz_path = str(item["xyz_path"])
        gfn = int(item.get("gfn", 2))
        charge = item.get("charge")
        uhf = item.get("uhf")
        charge_int = int(charge) if charge is not None else None
        uhf_int = int(uhf) if uhf is not None else None
        try:
            return calculate_candidate(
                candidate_id,
                xyz_path,
                gfn=gfn,
                charge=charge_int,
                uhf=uhf_int,
            )
        except Exception as exc:  # noqa: BLE001
            from xtb_lab_harness.xtb.schemas import CalculationStatus

            return CandidateResult(
                candidate_id=candidate_id,
                calculation_status=CalculationStatus.FAILED,
                error_message=str(exc),
            )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one, item) for item in candidates]
        for future in as_completed(futures):
            results.append(future.result())

    order = {str(c["candidate_id"]): i for i, c in enumerate(candidates)}
    results.sort(key=lambda r: order.get(r.candidate_id, 999))
    succeeded = sum(1 for r in results if r.calculation_status.value == "success")
    return BatchCalculationResult(results=results, succeeded=succeeded, failed=len(results) - succeeded)


def _sequential_batch(candidates: list[dict]) -> BatchCalculationResult:
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
    return BatchCalculationResult(results=results, succeeded=succeeded, failed=len(results) - succeeded)
