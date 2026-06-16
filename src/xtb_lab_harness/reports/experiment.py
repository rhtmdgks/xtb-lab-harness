from __future__ import annotations

from xtb_lab_harness.agents.schemas import (
    CandidateDebate,
    CandidateEvaluation,
    ExperimentManifest,
    TaskPlan,
)
from xtb_lab_harness.agents.safety import SafetyAgent
from xtb_lab_harness.agents.scoring import WEIGHTS


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
    """Build the 14-section experiment design report from Research Plan."""
    ranked = [e for e in evaluations if e.rank is not None]
    excluded = [e for e in evaluations if e.excluded]
    top = ranked[0] if ranked else None
    debate_list = debates or []

    sections: list[str] = [
        "# xTB Lab Harness — 실험 설계 보고서",
        "",
    ]
    if task_plan:
        sections.extend(
            [
                "## 0. 오케스트레이터 작업 할당",
                f"- **사용자 명령:** {task_plan.user_command}",
                f"- **판단 근거:** {task_plan.orchestrator_reasoning}",
                f"- **할당 에이전트:** {', '.join(task_plan.assigned_agents)}",
                f"- **토론 라운드:** {task_plan.debate_rounds}",
                f"- **집중 포인트:** {', '.join(task_plan.focus_points) or '—'}",
                "",
            ]
        )

    sections.extend(
        [
        "## 1. 실험 목적",
        experiment_objective,
        "",
        "## 2. 연구 가설",
        hypothesis,
        "",
        "## 3. 후보 물질 목록",
        _candidate_list(manifest),
        "",
        "## 4. xTB Tool 계산 조건",
        _xtb_conditions(manifest),
        "",
        "## 5. 후보 물질별 xTB 계산 결과",
        _xtb_results_section(evaluations),
        "",
        "## 6. 전문 에이전트별 검토 결과 (병렬 수행)",
        _agent_reviews_section(evaluations),
        "",
        "## 6.5 에이전트 토론 (Harness Debate)",
        _debate_section(debate_list),
        "",
        "## 7. 최종 후보 물질 랭킹",
        _ranking_section(ranked),
        "",
        "## 8. 추천 물질 선정 근거",
        _recommendation_rationale(top, ranked[:3]),
        "",
        "## 9. 제외 물질 사유",
        _exclusion_section(excluded),
        "",
        "## 10. 실험 설계안",
        _experiment_design(experiment_objective, top),
        "",
        "## 11. 대조군 및 반복 실험 설계",
        _controls_and_replicates(),
        "",
        "## 12. 예상 실패 요인",
        _failure_modes(),
        "",
        "## 13. 연구의 한계",
        _limitations(),
        "",
        "## 14. 후속 연구",
        _follow_up(),
        "",
        "---",
        "",
        "### 부록: xTB Evidence Table",
        "",
        evidence_table_markdown,
        "",
        f"_{SafetyAgent.disclaimer}_",
    ]
    )
    return "\n".join(sections)


def _debate_section(debates: list[CandidateDebate]) -> str:
    if not debates:
        return "_토론 미실행 (xTB 성공 후보 없음)._"
    parts: list[str] = []
    for debate in debates:
        parts.append(f"### {debate.candidate_id}")
        parts.append(f"- **합의:** {debate.consensus_summary}")
        parts.append(f"- **수정 권고:** {debate.revised_recommendation} (score adj {debate.score_adjustment:+.2f})")
        for rnd in debate.rounds:
            parts.append(f"#### Round {rnd.round_number}")
            for msg in rnd.messages:
                target = f" → @{msg.responds_to}" if msg.responds_to else ""
                parts.append(f"- **{msg.agent_name}** [{msg.stance}]{target}: {msg.message}")
            parts.append(f"- _라운드 요약:_ {rnd.round_synthesis}")
        parts.append("")
    return "\n".join(parts)


def _candidate_list(manifest: ExperimentManifest) -> str:
    lines = ["| ID | xyz | charge | notes |", "| --- | --- | ---: | --- |"]
    for c in manifest.candidates:
        lines.append(
            f"| {c.candidate_id} | `{c.xyz_path}` | {c.charge if c.charge is not None else '—'} | {c.notes or '—'} |"
        )
    return "\n".join(lines)


def _xtb_conditions(manifest: ExperimentManifest) -> str:
    gfn = manifest.xtb_settings.get("gfn", 2)
    return "\n".join(
        [
            f"- Method: GFN{gfn} (`--gfn {gfn}`)",
            "- Geometry optimization: `--opt`",
            "- Input: pre-built `.xyz` structures",
            "- Parser fields: total energy, dipole, partial charges, optimization status",
        ]
    )


def _xtb_results_section(evaluations: list[CandidateEvaluation]) -> str:
    parts: list[str] = []
    for ev in evaluations:
        r = ev.xtb_result
        parts.append(f"### {r.candidate_id}")
        parts.append(f"- **5-1. 구조 최적화:** {'성공' if r.geometry_optimized else '미확인/실패'}")
        energy = f"{r.total_energy_hartree:.6f} Eh" if r.total_energy_hartree is not None else "N/A"
        parts.append(f"- **5-2. 총 에너지:** {energy}")
        cs = r.charge_summary
        parts.append(
            f"- **5-3. 전하 분포:** q+ max={cs.max_positive_charge}, q- min={cs.max_negative_charge}, "
            f"note={cs.charge_distribution_note}"
        )
        dipole = f"{r.dipole_moment_debye:.2f} D" if r.dipole_moment_debye is not None else "N/A"
        parts.append(f"- **5-4. 쌍극자 모멘트:** {dipole}")
        parts.append(f"- **5-5. 계산 상태:** {r.calculation_status.value}")
        if r.error_message:
            parts.append(f"- **오류:** {r.error_message}")
        parts.append("")
    return "\n".join(parts)


def _agent_reviews_section(evaluations: list[CandidateEvaluation]) -> str:
    agent_order = [
        "Electrostatic Interaction Agent",
        "van der Waals / Dispersion Interpretation Agent",
        "Structural Stability Agent",
        "Safety Reasoning Agent",
        "Variable Control Agent",
        "Critic Agent",
    ]
    parts: list[str] = []
    for agent_name in agent_order:
        parts.append(f"### 6-{agent_order.index(agent_name) + 1}. {agent_name}")
        for ev in evaluations:
            for review in ev.agent_reviews:
                if review.agent_name == agent_name:
                    parts.append(
                        f"- **{ev.candidate_id}** (score={review.score:.2f}, {review.recommendation}): "
                        f"{review.summary}"
                    )
        parts.append("")
    return "\n".join(parts)


def _ranking_section(ranked: list[CandidateEvaluation]) -> str:
    if not ranked:
        return "_랭킹 가능한 후보 없음 (모두 제외 또는 계산 실패)._"
    lines = [
        "| Rank | Candidate | Final Score | E (Eh) | μ (D) |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    for ev in ranked:
        r = ev.xtb_result
        e = f"{r.total_energy_hartree:.4f}" if r.total_energy_hartree is not None else "—"
        mu = f"{r.dipole_moment_debye:.2f}" if r.dipole_moment_debye is not None else "—"
        lines.append(f"| {ev.rank} | {ev.candidate_id} | {ev.final_score:.3f} | {e} | {mu} |")
    lines.append("")
    lines.append("**가중치:** " + ", ".join(f"{k}={v}" for k, v in WEIGHTS.items()))
    return "\n".join(lines)


def _recommendation_rationale(
    top: CandidateEvaluation | None,
    top_three: list[CandidateEvaluation],
) -> str:
    if not top:
        return "추천 가능한 후보가 없습니다. xTB 설치·입력 구조·계산 조건을 확인하세요."
    lines = [
        f"1순위 **{top.candidate_id}** (final score {top.final_score:.3f}) 추천.",
        "",
        "근거 요약:",
    ]
    for review in top.agent_reviews:
        if review.evidence_points:
            lines.append(f"- {review.agent_name}: {review.evidence_points[0]}")
    if len(top_three) > 1:
        lines.append("")
        lines.append("차순위 후보:")
        for ev in top_three[1:]:
            lines.append(f"- {ev.candidate_id} (score {ev.final_score:.3f})")
    return "\n".join(lines)


def _exclusion_section(excluded: list[CandidateEvaluation]) -> str:
    if not excluded:
        return "_제외된 후보 없음._"
    lines: list[str] = []
    for ev in excluded:
        lines.append(f"- **{ev.candidate_id}:** {ev.exclusion_reason or '제외'}")
    return "\n".join(lines)


def _experiment_design(objective: str, top: CandidateEvaluation | None) -> str:
    candidate = top.candidate_id if top else "(미정)"
    return "\n".join(
        [
            f"- **목적 연계:** {objective}",
            f"- **주 후보:** {candidate}",
            "- **절차 초안:**",
            "  1. 통제된 농도/온도에서 후보 물질 용액 준비",
            "  2. 동일 조건에서 관찰 지표 측정(목적에 맞게 선택)",
            "  3. blank/대조군과 비교",
            "  4. xTB 예측 지표(극성, 전하, 상대 에너지)와 관찰 경향 대조",
        ]
    )


def _controls_and_replicates() -> str:
    return "\n".join(
        [
            "- **대조군:** 용매만(blank), 또는 water 등 기준 물질",
            "- **반복:** 기술적 반복 n≥3",
            "- **통제:** 온도, 농도, pH(해당 시), 시간, 교반 조건 고정",
        ]
    )


def _failure_modes() -> str:
    return "\n".join(
        [
            "- xTB semi-empirical 한계로 실험 효과와 정량 불일치",
            "- 용매 효과·농도 의존성 미반영",
            "- 안전성 1차 필터만 적용 — 실제 취급 제한",
            "- 구조 최적화 미수렴 후보의 해석 오류",
        ]
    )


def _limitations() -> str:
    return "\n".join(
        [
            "- 본 시스템은 **xTB Tool + 규칙 기반 MAS**이며 고정밀 양자화학이 아님",
            "- SMILES→3D 자동 생성 없음 — `.xyz` 사전 준비 필요",
            "- 분산력/vdW는 경향성 해석이며 분해 계산 아님",
            "- Safety Agent는 SDS/MSDS 대체 불가",
        ]
    )


def _follow_up() -> str:
    return "\n".join(
        [
            "- Critic Agent 고도화 및 근거-문장 일치성 검사",
            "- 동일 조건 반복 실행 후 추천 일관성 비교",
            "- 일반 LLM 단독 추천 vs xTB+MAS 비교 실험",
            "- 필요 시 웹 UI(Next.js) 데모 추가",
        ]
    )
