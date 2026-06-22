"""Classify per-candidate failures for report §15-1 — docs/report-format.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from xtb_lab_harness.agents.schemas import CandidateEvaluation
from xtb_lab_harness.xtb.schemas import CalculationStatus

Severity = Literal["실패", "주의"]


@dataclass(frozen=True)
class FailureRecord:
    candidate_id: str
    severity: Severity
    failure_type: str
    cause: str
    remediation: str


_XTB_EXIT_RE = re.compile(r"xTB exited with code (\d+)", re.IGNORECASE)


def _missing_xyz_record(candidate_id: str, message: str) -> FailureRecord:
    path_hint = message.split(":", 1)[-1].strip() if ":" in message else message
    return FailureRecord(
        candidate_id=candidate_id,
        severity="실패",
        failure_type="구조 파일 없음",
        cause=f"manifest에 지정된 `.xyz`가 존재하지 않음 ({path_hint}).",
        remediation="구조 파일을 준비하고 manifest `xyz_path`를 확인한 뒤 재실행.",
    )


def _classify_xtb_error(candidate_id: str, message: str) -> FailureRecord:
    lower = message.lower()

    if "구조 파일 없음" in message or "input .xyz not found" in lower or ".xyz not found" in lower:
        return _missing_xyz_record(candidate_id, message)

    if "xTB executable not found" in message or "xtb executable not found" in lower:
        return FailureRecord(
            candidate_id=candidate_id,
            severity="실패",
            failure_type="xTB 미설치",
            cause="PATH 또는 `XTB_BIN`에서 xTB 실행 파일을 찾지 못함.",
            remediation="xTB 설치 후 PATH 등록 또는 환경변수 `XTB_BIN` 설정.",
        )

    exit_match = _XTB_EXIT_RE.search(message)
    if exit_match:
        code = exit_match.group(1)
        return FailureRecord(
            candidate_id=candidate_id,
            severity="실패",
            failure_type="xTB 실행 오류",
            cause=f"xTB가 비정상 종료(exit code {code}). 입력 구조·전하·스핀 또는 수치 불안정 가능.",
            remediation=f"`data/runs/{candidate_id}/stdout.log`, `stderr.log` 확인 후 구조·charge·uhf 재검토.",
        )

    if "could not parse total energy" in lower:
        return FailureRecord(
            candidate_id=candidate_id,
            severity="실패",
            failure_type="출력 파싱 실패",
            cause="xTB는 실행됐으나 stdout/stderr에서 total energy를 추출하지 못함.",
            remediation=f"`data/runs/{candidate_id}/stdout.log`에서 xTB 정상 완료 여부 확인.",
        )

    if "사전 안전 플래그" in message:
        return FailureRecord(
            candidate_id=candidate_id,
            severity="실패",
            failure_type="사전 안전 제외",
            cause=message,
            remediation="SDS/MSDS·지도교사 검토 후 `safety_flags` 조정 또는 후보 교체.",
        )

    if "xTB run failed" in message or "xtb run failed" in lower:
        return FailureRecord(
            candidate_id=candidate_id,
            severity="실패",
            failure_type="xTB 실행 예외",
            cause=message,
            remediation=f"`data/runs/{candidate_id}` 로그 확인 및 입력 조건 재검토.",
        )

    return FailureRecord(
        candidate_id=candidate_id,
        severity="실패",
        failure_type="xTB 계산 실패",
        cause=message or "원인 메시지 없음.",
        remediation=f"`data/runs/{candidate_id}` 증거 로그 확인.",
    )


def diagnose_evaluation(ev: CandidateEvaluation) -> list[FailureRecord]:
    """Return failure/caution records for one candidate (empty if none)."""
    result = ev.xtb_result
    records: list[FailureRecord] = []

    if result.calculation_status == CalculationStatus.FAILED:
        records.append(_classify_xtb_error(ev.candidate_id, result.error_message or ""))
        return records

    if result.calculation_status == CalculationStatus.SUCCESS and not result.geometry_optimized:
        records.append(
            FailureRecord(
                candidate_id=ev.candidate_id,
                severity="주의",
                failure_type="최적화 미수렴",
                cause="xTB 출력에 `GEOMETRY OPTIMIZATION CONVERGED`가 없거나 최적화 실패 플래그가 감지됨.",
                remediation="초기 `.xyz` 품질·전하 설정을 재검토하고 `xtbopt.log` 확인.",
            )
        )

    if result.warnings:
        warning_preview = "; ".join(result.warnings[:2])
        if len(result.warnings) > 2:
            warning_preview += f" 외 {len(result.warnings) - 2}건"
        records.append(
            FailureRecord(
                candidate_id=ev.candidate_id,
                severity="주의",
                failure_type="xTB 경고",
                cause=warning_preview,
                remediation="경고 내용이 수렴·에너지 해석에 영향을 주는지 로그에서 확인.",
            )
        )

    if ev.excluded and result.calculation_status == CalculationStatus.SUCCESS:
        reason = ev.exclusion_reason or "에이전트 제외"
        if "토론" in reason:
            failure_type = "토론 합의 제외"
        elif "Structural Stability" in reason or "구조" in reason:
            failure_type = "구조 안정성 제외"
        elif "Safety" in reason or "안전" in reason:
            failure_type = "안전성 제외"
        else:
            failure_type = "에이전트 제외"
        records.append(
            FailureRecord(
                candidate_id=ev.candidate_id,
                severity="실패",
                failure_type=failure_type,
                cause=reason,
                remediation="§7 에이전트 검토·§10 차원 점수를 확인하고 제외 근거 재평가.",
            )
        )

    return records


def collect_failure_records(evaluations: list[CandidateEvaluation]) -> list[FailureRecord]:
    """All failure/caution records for a run, manifest order preserved."""
    order = {ev.candidate_id: i for i, ev in enumerate(evaluations)}
    records: list[FailureRecord] = []
    for ev in evaluations:
        records.extend(diagnose_evaluation(ev))
    records.sort(key=lambda r: order.get(r.candidate_id, 999))
    return records
