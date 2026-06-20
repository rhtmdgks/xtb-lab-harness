"""Report display labels — docs/report-format.md (report-harness-v1.2)."""

from __future__ import annotations

from xtb_lab_harness.xtb.schemas import CalculationStatus

RECOMMENDATION_KO: dict[str, str] = {
    "include": "포함",
    "caution": "주의",
    "exclude": "제외",
}


def calculation_status_ko(status: CalculationStatus) -> str:
    return {
        CalculationStatus.SUCCESS: "성공",
        CalculationStatus.FAILED: "실패",
    }[status]


def geometry_optimized_ko(optimized: bool) -> str:
    return "✓" if optimized else "✗"


def recommendation_ko(recommendation: str) -> str:
    return RECOMMENDATION_KO.get(recommendation, recommendation)
