from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.xtb.parser import parse_xtb_artifacts
from xtb_lab_harness.xtb.runner import (
    XtbNotFoundError,
    copy_input_xyz,
    prepare_run_directory,
    run_xtb_optimization,
)
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


def resolve_project_paths() -> tuple[Path, Path]:
    data_dir = Path(
        __import__("os").environ.get("XTB_DATA_DIR", Path.cwd() / "data")
    ).resolve()
    runs_dir = data_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return data_dir, runs_dir


def calculate_candidate(
    candidate_id: str,
    xyz_path: str,
    *,
    gfn: int = 2,
    charge: int | None = None,
    uhf: int | None = None,
) -> CandidateResult:
    """Run geometry optimization + property extraction for one .xyz candidate."""
    source = Path(xyz_path).expanduser().resolve()
    if not source.exists():
        return CandidateResult(
            candidate_id=candidate_id,
            calculation_status=CalculationStatus.FAILED,
            error_message=f"Input .xyz not found: {source}",
        )

    _, runs_dir = resolve_project_paths()
    run_dir = prepare_run_directory(runs_dir, candidate_id)
    input_xyz = copy_input_xyz(source, run_dir, candidate_id)

    try:
        artifacts = run_xtb_optimization(
            input_xyz,
            run_dir,
            gfn=gfn,
            charge=charge,
            uhf=uhf,
            opt=True,
        )
    except XtbNotFoundError as exc:
        return CandidateResult(
            candidate_id=candidate_id,
            calculation_status=CalculationStatus.FAILED,
            error_message=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 — surface subprocess failures to MCP client
        return CandidateResult(
            candidate_id=candidate_id,
            calculation_status=CalculationStatus.FAILED,
            error_message=f"xTB run failed: {exc}",
        )

    return parse_xtb_artifacts(candidate_id, artifacts)
