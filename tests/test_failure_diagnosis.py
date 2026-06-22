from __future__ import annotations

from xtb_lab_harness.agents.schemas import CandidateEvaluation, DimensionScores
from xtb_lab_harness.reports.failure_diagnosis import collect_failure_records, diagnose_evaluation
from xtb_lab_harness.reports.sections import section_15_1_run_failures
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult, ChargeSummary


def _eval(
    candidate_id: str,
    *,
    status: CalculationStatus = CalculationStatus.SUCCESS,
    error_message: str | None = None,
    geometry_optimized: bool = True,
    warnings: list[str] | None = None,
    excluded: bool = False,
    exclusion_reason: str | None = None,
) -> CandidateEvaluation:
    return CandidateEvaluation(
        candidate_id=candidate_id,
        xtb_result=CandidateResult(
            candidate_id=candidate_id,
            calculation_status=status,
            geometry_optimized=geometry_optimized,
            error_message=error_message,
            warnings=warnings or [],
            charge_summary=ChargeSummary(),
        ),
        agent_reviews=[],
        dimension_scores=DimensionScores(),
        final_score=0.0,
        excluded=excluded,
        exclusion_reason=exclusion_reason,
    )


def test_diagnose_missing_xyz() -> None:
    ev = _eval(
        "filter_iron",
        status=CalculationStatus.FAILED,
        error_message="구조 파일 없음: examples/missing.xyz",
        excluded=True,
    )
    records = diagnose_evaluation(ev)
    assert len(records) == 1
    assert records[0].failure_type == "구조 파일 없음"
    assert records[0].severity == "실패"
    assert "examples/missing.xyz" in records[0].cause


def test_diagnose_xtb_exit_code() -> None:
    ev = _eval(
        "bad_mol",
        status=CalculationStatus.FAILED,
        error_message="xTB exited with code 1",
    )
    records = diagnose_evaluation(ev)
    assert records[0].failure_type == "xTB 실행 오류"
    assert "exit code 1" in records[0].cause


def test_diagnose_optimization_not_converged() -> None:
    ev = _eval("wobbly", geometry_optimized=False)
    records = diagnose_evaluation(ev)
    assert any(r.failure_type == "최적화 미수렴" for r in records)
    assert any(r.severity == "주의" for r in records)


def test_diagnose_agent_exclusion_after_success() -> None:
    ev = _eval(
        "risky",
        excluded=True,
        exclusion_reason="Safety Reasoning Agent: 고위험",
    )
    records = diagnose_evaluation(ev)
    assert any(r.failure_type == "안전성 제외" for r in records)


def test_section_15_1_renders_table() -> None:
    evaluations = [
        _eval(
            "filter_iron",
            status=CalculationStatus.FAILED,
            error_message="구조 파일 없음: a.xyz",
            excluded=True,
        ),
        _eval("ok", geometry_optimized=True),
    ]
    text = section_15_1_run_failures(evaluations)
    assert "| 후보 ID | 심각도 | 실패 유형 | 원인 | 권장 조치 |" in text
    assert "filter_iron" in text
    assert "구조 파일 없음" in text
    assert "ok" not in text.split("| 후보 ID")[1].split("filter_iron")[0]
