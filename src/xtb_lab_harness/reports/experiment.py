from __future__ import annotations

from xtb_lab_harness.agents.schemas import (
    CandidateDebate,
    CandidateEvaluation,
    ExperimentManifest,
    TaskPlan,
)
from xtb_lab_harness.agents.safety import SafetyAgent
from xtb_lab_harness.reports.sections import (
    REPORT_FORMAT_VERSION,
    appendix_b_ranking_rules,
    pick_recommendation,
    section_0_orchestrator,
    section_11_top3,
    section_12_exclusions,
    section_13_experiment_design,
    section_14_variable_control,
    section_15_failures,
    section_16_limitations,
    section_17_follow_up,
    section_3_xtb_scope,
    section_4_candidates,
    section_5_xtb_conditions,
    section_6_xtb_results,
    section_7_agent_reviews,
    section_8_debates,
    section_9_ranking,
    section_10_dimension_summary,
    sorted_by_rank,
)

# Backward-compatible aliases for tests and callers
_sorted_by_rank = sorted_by_rank
_pick_recommendation = pick_recommendation


def generate_experiment_report(
    *,
    experiment_objective: str,
    hypothesis: str,
    manifest: ExperimentManifest,
    evaluations: list[CandidateEvaluation],
    evidence_table_markdown: str,
    task_plan: TaskPlan | None = None,
    debates: list[CandidateDebate] | None = None,
) -> str:
    """Build the report-harness-v1.3 experiment design report (docs/report-format.md)."""
    ranked = sorted_by_rank(evaluations)
    excluded = [e for e in evaluations if e.excluded]
    top, recommend_three = pick_recommendation(ranked, manifest)
    debate_list = debates or []

    sections: list[str] = [
        "# xTB Lab Harness — 실험 설계 보고서",
        "",
        f"_보고서 형식: `{REPORT_FORMAT_VERSION}` — `docs/report-format.md`_",
        "",
    ]
    if task_plan:
        sections.extend(section_0_orchestrator(task_plan))

    sections.extend(
        [
            "## 1. 실험 목적",
            experiment_objective,
            "",
            "## 2. 핵심 가설",
            hypothesis,
            "",
            "## 3. xTB 계산 범위와 한계",
            section_3_xtb_scope(evaluations),
            "",
            "## 4. 후보 물질 목록",
            section_4_candidates(manifest),
            "",
            "## 5. xTB Tool 계산 조건",
            section_5_xtb_conditions(manifest),
            "",
            "## 6. xTB 계산 결과 요약",
            section_6_xtb_results(evaluations),
            "",
            "## 7. 에이전트 검토 (이탈만)",
            section_7_agent_reviews(evaluations),
            "",
            "## 8. 에이전트 토론 요약",
            section_8_debates(debate_list),
            "",
            "## 9. 최종 후보 물질 랭킹",
            section_9_ranking(ranked),
            "",
            "## 10. 차원별 평가 요약",
            section_10_dimension_summary(ranked),
            "",
            "## 11. 최종 추천 조합 Top 3",
            section_11_top3(recommend_three, manifest),
            "",
            "## 12. 제외·감점·추천 제외 사유",
            section_12_exclusions(
                excluded=excluded,
                ranked=ranked,
                recommend_three=recommend_three,
                manifest=manifest,
            ),
            "",
            "## 13. 실험 설계안",
            section_13_experiment_design(top),
            "",
            "## 14. 변인 통제 계획",
            section_14_variable_control(top, manifest),
            "",
            "## 15. 실패 요인",
            section_15_failures(evaluations),
            "",
            "## 16. 연구의 한계",
            section_16_limitations(),
            "",
            "## 17. 후속 연구 방향",
            section_17_follow_up(),
            "",
            "---",
            "",
            "### 부록 A: xTB 증거 표",
            "",
            evidence_table_markdown,
            "",
            "### 부록 B: 점수 가중치 및 랭킹 규칙",
            "",
            appendix_b_ranking_rules(),
            "",
            f"_{SafetyAgent.disclaimer}_",
        ]
    )
    return "\n".join(sections)


# Legacy helpers kept for tests importing from experiment module
def _recommendation_rationale(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("Use section_11_top3 / section_12_exclusions (report-harness-v1)")
