from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class CalculationStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ChargeSummary(BaseModel):
    max_positive_charge: float | None = None
    max_negative_charge: float | None = None
    mean_absolute_charge: float | None = None
    charge_distribution_note: str | None = None


class RawEvidence(BaseModel):
    stdout_log: str
    stderr_log: str
    optimized_xyz: str | None = None
    input_xyz: str
    run_directory: str


class CandidateResult(BaseModel):
    candidate_id: str
    calculation_status: CalculationStatus
    geometry_optimized: bool = False
    total_energy_hartree: float | None = None
    dipole_moment_debye: float | None = None
    charge_summary: ChargeSummary = Field(default_factory=ChargeSummary)
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None
    raw_evidence: RawEvidence | None = None


class BatchCalculationResult(BaseModel):
    results: list[CandidateResult]
    succeeded: int
    failed: int


class EvidenceTableRow(BaseModel):
    candidate_id: str
    calculation_status: CalculationStatus
    geometry_optimized: bool
    total_energy_hartree: float | None
    dipole_moment_debye: float | None
    max_positive_charge: float | None
    max_negative_charge: float | None
    relative_energy_kcal_mol: float | None = None
    rank: int | None = None


class EvidenceTable(BaseModel):
    rows: list[EvidenceTableRow]
    markdown: str
    reference_candidate_id: str | None = None
    format: Literal["markdown"] = "markdown"
