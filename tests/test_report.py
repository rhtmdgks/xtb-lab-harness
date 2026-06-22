from __future__ import annotations

from xtb_lab_harness.agents.schemas import (
    AgentReview,
    CandidateEvaluation,
    CandidateSpec,
    DimensionScores,
    ExperimentManifest,
)
from xtb_lab_harness.reports.experiment import generate_experiment_report
from xtb_lab_harness.reports.sections import pick_recommendation, sorted_by_rank
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult, ChargeSummary

REQUIRED_SECTIONS = [
    "## 1. 실험 목적",
    "## 2. 핵심 가설",
    "## 3. xTB 계산 범위와 한계",
    "## 4. 후보 물질 목록",
    "## 5. xTB Tool 계산 조건",
    "## 6. xTB 계산 결과 요약",
    "## 7. 에이전트 검토",
    "## 8. 에이전트 토론",
    "## 9. 최종 후보 물질 랭킹",
    "## 10. 차원별 평가 요약",
    "## 11. 최종 추천 조합 Top 3",
    "## 12. 제외·감점·추천 제외 사유",
    "## 13. 실험 설계안",
    "## 14. 변인 통제 계획",
    "## 15. 실패 요인",
    "### 15-1. 본 실행 실패 원인",
    "### 15-2. 예상 실패 요인",
    "## 16. 연구의 한계",
    "## 17. 후속 연구",
    "### 부록 B: 점수 가중치 및 랭킹 규칙",
]


def _evaluation(
    candidate_id: str,
    *,
    rank: int,
    score: float,
    agent_reviews: list[AgentReview] | None = None,
) -> CandidateEvaluation:
    return CandidateEvaluation(
        candidate_id=candidate_id,
        xtb_result=CandidateResult(
            candidate_id=candidate_id,
            calculation_status=CalculationStatus.SUCCESS,
            geometry_optimized=True,
            total_energy_hartree=-1.0,
            dipole_moment_debye=1.0,
            charge_summary=ChargeSummary(),
        ),
        agent_reviews=agent_reviews or [],
        dimension_scores=DimensionScores(),
        final_score=score,
        rank=rank,
    )


def test_sorted_by_rank_orders_by_rank_not_manifest_order() -> None:
    evaluations = [
        _evaluation("combo_cell_chitosan", rank=2, score=0.934),
        _evaluation("combo_cell_ctrl", rank=1, score=0.959),
    ]
    ranked = sorted_by_rank(evaluations)
    assert [e.candidate_id for e in ranked] == ["combo_cell_ctrl", "combo_cell_chitosan"]


def test_pick_recommendation_skips_control_candidates() -> None:
    manifest = ExperimentManifest(
        experiment_objective="test",
        candidates=[
            CandidateSpec(candidate_id="combo_cell_ctrl", xyz_path="a.xyz", notes="대조군"),
            CandidateSpec(candidate_id="combo_cell_chitosan", xyz_path="b.xyz"),
        ],
    )
    ranked = [
        _evaluation("combo_cell_ctrl", rank=1, score=0.959),
        _evaluation("combo_cell_chitosan", rank=2, score=0.934),
    ]
    top, top_three = pick_recommendation(ranked, manifest)
    assert top is not None
    assert top.candidate_id == "combo_cell_chitosan"


def test_report_includes_required_sections_without_duplicate_disclaimer() -> None:
    manifest = ExperimentManifest(
        experiment_objective="objective",
        candidates=[
            CandidateSpec(candidate_id="combo_cell_chitosan", xyz_path="examples/b.xyz", charge=1),
            CandidateSpec(candidate_id="combo_cell_ctrl", xyz_path="examples/a.xyz", charge=0, notes="대조군"),
        ],
    )
    evaluations = [
        _evaluation("combo_cell_chitosan", rank=2, score=0.934),
        _evaluation("combo_cell_ctrl", rank=1, score=0.959),
    ]
    report = generate_experiment_report(
        experiment_objective="objective",
        hypothesis="hypothesis",
        manifest=manifest,
        evaluations=evaluations,
        evidence_table_markdown="| evidence |",
    )
    for heading in REQUIRED_SECTIONS:
        assert heading in report
    assert report.count("여과 효율·포집률을 예측하거나 주장하지 않는다") == 1


def test_section_7_only_lists_deviations() -> None:
    manifest = ExperimentManifest(
        experiment_objective="objective",
        candidates=[CandidateSpec(candidate_id="a", xyz_path="a.xyz")],
    )
    reviews = [
        AgentReview(agent_name="Electrostatic Interaction Agent", candidate_id="a", score=0.8, summary="ok"),
        AgentReview(
            agent_name="Safety Reasoning Agent",
            candidate_id="a",
            score=0.4,
            summary="caution",
            recommendation="caution",
            concerns=["고위험 키워드"],
        ),
    ]
    evaluations = [_evaluation("a", rank=1, score=0.5, agent_reviews=reviews)]
    report = generate_experiment_report(
        experiment_objective="objective",
        hypothesis="hypothesis",
        manifest=manifest,
        evaluations=evaluations,
        evidence_table_markdown="| evidence |",
    )
    s7 = report.split("## 8.")[0].split("## 7.")[-1]
    assert "Safety Reasoning Agent" in s7
    assert "Electrostatic Interaction Agent" not in s7


def test_section_9_uses_cross_refs_not_duplicate_xtb_columns() -> None:
    manifest = ExperimentManifest(
        experiment_objective="objective",
        candidates=[CandidateSpec(candidate_id="a", xyz_path="a.xyz")],
    )
    report = generate_experiment_report(
        experiment_objective="objective",
        hypothesis="hypothesis",
        manifest=manifest,
        evaluations=[_evaluation("a", rank=1, score=0.9)],
        evidence_table_markdown="| evidence |",
    )
    s9 = report.split("## 10.")[0].split("## 9.")[-1]
    assert "§6" in s9
    assert "μ (D)" not in s9
    assert "Candidate" not in s9
    assert "Final Score" not in s9
    assert "후보 ID" in s9
    assert "최종 점수" in s9


def test_report_section_12_references_section_15_for_excluded() -> None:
    manifest = ExperimentManifest(
        experiment_objective="objective",
        candidates=[
            CandidateSpec(candidate_id="missing", xyz_path="missing.xyz"),
            CandidateSpec(candidate_id="ok", xyz_path="ok.xyz"),
        ],
    )
    evaluations = [
        CandidateEvaluation(
            candidate_id="missing",
            xtb_result=CandidateResult(
                candidate_id="missing",
                calculation_status=CalculationStatus.FAILED,
                error_message="구조 파일 없음: missing.xyz",
            ),
            agent_reviews=[],
            dimension_scores=DimensionScores(),
            final_score=0.0,
            excluded=True,
            exclusion_reason="구조 파일 없음: missing.xyz",
        ),
        _evaluation("ok", rank=1, score=0.9),
    ]
    report = generate_experiment_report(
        experiment_objective="objective",
        hypothesis="hypothesis",
        manifest=manifest,
        evaluations=evaluations,
        evidence_table_markdown="| evidence |",
    )
    s12 = report.split("## 13.")[0].split("## 12.")[-1]
    s15 = report.split("## 16.")[0].split("## 15.")[-1]
    assert "§15-1 참조" in s12
    assert "구조 파일 없음" in s15
    assert "missing" in s15


def test_report_uses_korean_table_headers() -> None:
    manifest = ExperimentManifest(
        experiment_objective="objective",
        candidates=[CandidateSpec(candidate_id="a", xyz_path="a.xyz")],
    )
    report = generate_experiment_report(
        experiment_objective="objective",
        hypothesis="hypothesis",
        manifest=manifest,
        evaluations=[_evaluation("a", rank=1, score=0.9)],
        evidence_table_markdown="| evidence |",
    )
    assert "report-harness-v1.3" in report
    assert "| 후보 ID | 최적화 | E (Eh)" in report
    assert "| 실행 디렉터리 |" in report
    assert "| 후보 ID | 순위 | 정전기 | 구조 |" in report
    assert "Candidate | Opt" not in report
    assert "run_directory" not in report
    assert "계산 상태" in report
    assert "success" not in report.split("## 6.")[1].split("## 7.")[0]
