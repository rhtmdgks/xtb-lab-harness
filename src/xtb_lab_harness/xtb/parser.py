from __future__ import annotations

import re
from pathlib import Path

from xtb_lab_harness.xtb.runner import XtbRunArtifacts, extract_warnings
from xtb_lab_harness.xtb.schemas import (
    CalculationStatus,
    CandidateResult,
    ChargeSummary,
    RawEvidence,
)

TOTAL_ENERGY_RE = re.compile(
    r"TOTAL\s+ENERGY\s+(-?\d+\.\d+)",
    re.IGNORECASE,
)
FINAL_SINGLE_POINT_ENERGY_RE = re.compile(
    r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)",
    re.IGNORECASE,
)
DIPOLE_TOTAL_RE = re.compile(
    r"total\s+(-?\d+\.\d+)\s*\(",
    re.IGNORECASE,
)
OPTIMIZATION_CONVERGED_RE = re.compile(
    r"GEOMETRY OPTIMIZATION CONVERGED",
    re.IGNORECASE,
)
OPTIMIZATION_FAILED_RE = re.compile(
    r"GEOMETRY OPTIMIZATION FAILED",
    re.IGNORECASE,
)


def _parse_total_energy_hartree(text: str) -> float | None:
    for pattern in (TOTAL_ENERGY_RE, FINAL_SINGLE_POINT_ENERGY_RE):
        match = pattern.search(text)
        if match:
            return float(match.group(1))
    return None


def _parse_dipole_debye(text: str) -> float | None:
    in_dipole_block = False
    for line in text.splitlines():
        if "molecular dipole" in line.lower():
            in_dipole_block = True
            continue
        if in_dipole_block:
            match = DIPOLE_TOTAL_RE.search(line)
            if match:
                return float(match.group(1))
    match = DIPOLE_TOTAL_RE.search(text)
    return float(match.group(1)) if match else None


def parse_charges_file(charges_path: Path) -> list[float]:
    if not charges_path.exists():
        return []

    charges: list[float] = []
    for line in charges_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 4:
            continue
        try:
            charges.append(float(parts[3]))
        except ValueError:
            continue
    return charges


def summarize_charges(charges: list[float]) -> ChargeSummary:
    if not charges:
        return ChargeSummary(
            charge_distribution_note="No partial charges parsed from xTB output.",
        )

    positives = [value for value in charges if value > 0]
    negatives = [value for value in charges if value < 0]
    mean_abs = sum(abs(value) for value in charges) / len(charges)

    note = "polarized structure" if max(charges) - min(charges) > 0.5 else "moderate charge separation"

    return ChargeSummary(
        max_positive_charge=max(positives) if positives else 0.0,
        max_negative_charge=min(negatives) if negatives else 0.0,
        mean_absolute_charge=mean_abs,
        charge_distribution_note=note,
    )


def parse_xtb_artifacts(
    candidate_id: str,
    artifacts: XtbRunArtifacts,
) -> CandidateResult:
    combined = artifacts.stdout_text + "\n" + artifacts.stderr_text
    warnings = extract_warnings(artifacts.stdout_text, artifacts.stderr_text)

    geometry_optimized = artifacts.optimized_xyz is not None and OPTIMIZATION_CONVERGED_RE.search(
        combined
    ) is not None
    if OPTIMIZATION_FAILED_RE.search(combined):
        geometry_optimized = False

    charges = parse_charges_file(artifacts.run_dir / "charges")
    charge_summary = summarize_charges(charges)

    total_energy = _parse_total_energy_hartree(combined)
    dipole = _parse_dipole_debye(combined)

    succeeded = artifacts.returncode == 0 and total_energy is not None
    status = CalculationStatus.SUCCESS if succeeded else CalculationStatus.FAILED

    error_message = None
    if not succeeded:
        if artifacts.returncode != 0:
            error_message = f"xTB exited with code {artifacts.returncode}"
        elif total_energy is None:
            error_message = "Could not parse total energy from xTB output"

    return CandidateResult(
        candidate_id=candidate_id,
        calculation_status=status,
        geometry_optimized=geometry_optimized,
        total_energy_hartree=total_energy,
        dipole_moment_debye=dipole,
        charge_summary=charge_summary,
        warnings=warnings,
        error_message=error_message,
        raw_evidence=RawEvidence(
            stdout_log=str(artifacts.stdout_log),
            stderr_log=str(artifacts.stderr_log),
            optimized_xyz=str(artifacts.optimized_xyz) if artifacts.optimized_xyz else None,
            input_xyz=str(artifacts.input_xyz),
            run_directory=str(artifacts.run_dir),
        ),
    )
