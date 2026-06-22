"""Report section builders — docs/report-format.md (report-harness-v1.2, no duplication)."""

from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.agents.schemas import (
    AgentReview,
    CandidateDebate,
    CandidateEvaluation,
    CandidateSpec,
    ExperimentManifest,
    TaskPlan,
)
from xtb_lab_harness.agents.scoring import WEIGHTS
from xtb_lab_harness.reports.failure_diagnosis import collect_failure_records
from xtb_lab_harness.reports.labels import (
    calculation_status_ko,
    geometry_optimized_ko,
    recommendation_ko,
)
from xtb_lab_harness.xtb.schemas import CalculationStatus

REPORT_FORMAT_VERSION = "report-harness-v1.3"
FILTRATION_DISCLAIMER = (
    "xTB 결과는 분자 proxy 수준의 상호작용 **경향** 비교용이며, "
    "**실제 필터 여과 효율·포집률을 예측하거나 주장하지 않는다.**"
)

_AGENT_ORDER = [
    "Electrostatic Interaction Agent",
    "van der Waals / Dispersion Interpretation Agent",
    "Structural Stability Agent",
    "Safety Reasoning Agent",
    "Variable Control Agent",
    "Critic Agent",
]


def sorted_by_rank(evaluations: list[CandidateEvaluation]) -> list[CandidateEvaluation]:
    ranked = [e for e in evaluations if e.rank is not None]
    return sorted(ranked, key=lambda e: e.rank or 999)


def is_control_spec(spec: CandidateSpec | None, candidate_id: str) -> bool:
    if spec is None:
        return "_ctrl" in candidate_id.lower()
    text = f"{candidate_id} {spec.notes or ''}".lower()
    return "대조" in text or "control" in text or "_ctrl" in candidate_id.lower()


def candidate_role(spec: CandidateSpec) -> str:
    return "대조군" if is_control_spec(spec, spec.candidate_id) else "실험군"


def spec_for(manifest: ExperimentManifest, candidate_id: str) -> CandidateSpec | None:
    return next((c for c in manifest.candidates if c.candidate_id == candidate_id), None)


def pick_recommendation(
    ranked: list[CandidateEvaluation],
    manifest: ExperimentManifest,
) -> tuple[CandidateEvaluation | None, list[CandidateEvaluation]]:
    active = [e for e in ranked if not is_control_spec(spec_for(manifest, e.candidate_id), e.candidate_id)]
    if active:
        return active[0], active[:3]
    return (ranked[0] if ranked else None), ranked[:3]


def display_rank_groups(ranked: list[CandidateEvaluation]) -> list[tuple[CandidateEvaluation, int, bool]]:
    if not ranked:
        return []
    groups: list[tuple[CandidateEvaluation, int, bool]] = []
    i = 0
    while i < len(ranked):
        score = round(ranked[i].final_score, 4)
        tie_group = [ranked[i]]
        j = i + 1
        while j < len(ranked) and round(ranked[j].final_score, 4) == score:
            tie_group.append(ranked[j])
            j += 1
        display_rank = min(ev.rank or (i + 1) for ev in tie_group)
        tied = len(tie_group) > 1
        for ev in tie_group:
            groups.append((ev, display_rank, tied))
        i = j
    return groups


def _display_xyz(xyz_path: str) -> str:
    """Prefer short relative-style paths in the report table."""
    p = Path(xyz_path)
    parts = p.parts
    if "examples" in parts:
        idx = parts.index("examples")
        return str(Path(*parts[idx:]))
    return p.name


def section_0_orchestrator(task_plan: TaskPlan) -> list[str]:
    return [
        "## 0. 오케스트레이터 작업 할당",
        f"- **사용자 명령:** {task_plan.user_command}",
        f"- **판단 근거:** {task_plan.orchestrator_reasoning}",
        f"- **할당 에이전트:** {', '.join(task_plan.assigned_agents)}",
        f"- **토론 라운드:** {task_plan.debate_rounds}",
        "",
    ]


def section_3_xtb_scope(evaluations: list[CandidateEvaluation]) -> str:
    total = len(evaluations)
    success = sum(1 for e in evaluations if e.xtb_result.calculation_status == CalculationStatus.SUCCESS)
    failed = total - success
    optimized = sum(1 for e in evaluations if e.xtb_result.geometry_optimized)
    return "\n".join(
        [
            "| 항목 | 값 |",
            "| --- | ---: |",
            f"| 후보 수 | {total} |",
            f"| xTB 성공 / 실패 | {success} / {failed} |",
            f"| 구조 최적화 수렴 | {optimized} |",
            "| 상호작용 에너지 proxy | 복합체 `.xyz` 없으면 미산출 |",
            "",
            f"> {FILTRATION_DISCLAIMER}",
            "",
            "- 고분자·막 공극·표면적·유속·이온강도·fouling 미반영",
            "- 서로 다른 형식 전하·화학식 간 절대 에너지 직접 비교 부적절",
            "- `.xyz` 사전 준비 필요; vdW는 경향성 해석",
        ]
    )


def section_4_candidates(manifest: ExperimentManifest) -> str:
    lines = [
        "| ID | xyz | charge | 역할 | notes |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for c in manifest.candidates:
        lines.append(
            f"| {c.candidate_id} | `{_display_xyz(c.xyz_path)}` | "
            f"{c.charge if c.charge is not None else '—'} | "
            f"{candidate_role(c)} | {c.notes or '—'} |"
        )
    return "\n".join(lines)


def section_5_xtb_conditions(manifest: ExperimentManifest) -> str:
    gfn = manifest.xtb_settings.get("gfn", 2)
    return f"GFN{gfn} (`--gfn {gfn}`), 기하 최적화 (`--opt`), 입력: 사전 준비 `.xyz`."


def section_6_xtb_results(evaluations: list[CandidateEvaluation]) -> str:
    lines = [
        "| 후보 ID | 최적화 | E (Eh) | q⁺ max | q⁻ min | μ (D) | 계산 상태 |",
        "| --- | :---: | ---: | ---: | ---: | ---: | --- |",
    ]
    evidence_lines = ["", "**증거 경로:**", "| 후보 ID | 실행 디렉터리 |", "| --- | --- |"]
    for ev in evaluations:
        r = ev.xtb_result
        cs = r.charge_summary
        opt = geometry_optimized_ko(r.geometry_optimized)
        e = f"{r.total_energy_hartree:.4f}" if r.total_energy_hartree is not None else "—"
        qp = f"{cs.max_positive_charge:.3f}" if cs.max_positive_charge is not None else "—"
        qn = f"{cs.max_negative_charge:.3f}" if cs.max_negative_charge is not None else "—"
        mu = f"{r.dipole_moment_debye:.2f}" if r.dipole_moment_debye is not None else "—"
        lines.append(
            f"| {r.candidate_id} | {opt} | {e} | {qp} | {qn} | {mu} | "
            f"{calculation_status_ko(r.calculation_status)} |"
        )
        if r.raw_evidence:
            evidence_lines.append(f"| {r.candidate_id} | `{r.raw_evidence.run_directory}` |")
        elif r.error_message:
            evidence_lines.append(f"| {r.candidate_id} | _실패 — §15-1 참조_ |")
    return "\n".join(lines + evidence_lines)


def _is_deviation(review: AgentReview) -> bool:
    return review.recommendation != "include" or bool(review.concerns)


def section_7_agent_reviews(evaluations: list[CandidateEvaluation]) -> str:
    """Only caution / exclude / concerns — scores for all candidates are in §10."""
    rows: list[str] = []
    for ev in evaluations:
        for review in ev.agent_reviews:
            if not _is_deviation(review):
                continue
            concern = f" — {'; '.join(review.concerns[:2])}" if review.concerns else ""
            rows.append(
                f"- **{ev.candidate_id}** / {review.agent_name}: "
                f"{recommendation_ko(review.recommendation)} (점수 {review.score:.2f}){concern}"
            )
    if not rows:
        return "_에이전트 이탈(주의·제외·우려) 없음. 전체 차원 점수는 §10 참조._"
    header = "_정상 포함 항목은 §10에 집계. 아래는 주의·제외·우려만 기록._\n"
    return header + "\n".join(rows)


def _is_trivial_debate(debate: CandidateDebate) -> bool:
    return debate.revised_recommendation == "include" and "큰 이견 없음" in debate.consensus_summary


def section_8_debates(debates: list[CandidateDebate]) -> str:
    if not debates:
        return "_토론 미실행._"
    non_trivial = [d for d in debates if not _is_trivial_debate(d)]
    if not non_trivial:
        adj = debates[0].score_adjustment if debates else 0.0
        return (
            f"_전 {len(debates)}후보 포함 합의 (점수 조정 {adj:+.2f}). "
            "라운드 전문: run artifact `debates.json`._"
        )
    lines = ["_이견·조정이 있는 후보만 요약. 전문은 `debates.json`._", ""]
    for debate in non_trivial:
        lines.append(
            f"- **{debate.candidate_id}:** {debate.consensus_summary} "
            f"→ {recommendation_ko(debate.revised_recommendation)} "
            f"(조정 {debate.score_adjustment:+.2f})"
        )
    return "\n".join(lines)


def section_9_ranking(ranked: list[CandidateEvaluation]) -> str:
    if not ranked:
        return "_랭킹 가능한 후보 없음._"
    lines = [
        "| 순위 | 후보 ID | 최종 점수 | 동점 |",
        "| ---: | --- | ---: | :---: |",
    ]
    for ev, display_rank, tied in display_rank_groups(ranked):
        tie_mark = "✓" if tied else "—"
        lines.append(f"| {display_rank} | {ev.candidate_id} | {ev.final_score:.3f} | {tie_mark} |")
    lines.append("")
    lines.append("_xTB 수치(E, μ, 전하)는 §6, 차원 점수는 §10, 규칙·가중치는 부록 B._")
    lines.append("_순위 1 ≠ §11 추천 1위일 수 있음 → §12-2._")
    return "\n".join(lines)


def section_10_dimension_summary(ranked: list[CandidateEvaluation]) -> str:
    if not ranked:
        return "_평가 요약 없음._"
    lines = [
        "| 후보 ID | 순위 | 정전기 | 구조 | 실험 | 안전 | 변인 | 검증 | 최종 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for ev in ranked:
        d = ev.dimension_scores
        lines.append(
            f"| {ev.candidate_id} | {ev.rank} | {d.electrostatic:.2f} | {d.structural_stability:.2f} | "
            f"{d.experimental_feasibility:.2f} | {d.safety:.2f} | {d.variable_control:.2f} | "
            f"{d.critic_reliability:.2f} | {ev.final_score:.3f} |"
        )
    return "\n".join(lines)


def _feasibility_line(ev: CandidateEvaluation, manifest: ExperimentManifest) -> str:
    for review in ev.agent_reviews:
        if review.agent_name == "Candidate Material Agent" and review.evidence_points:
            note = review.evidence_points[0]
            if note.startswith("후보 메모:"):
                return note.removeprefix("후보 메모:").strip()
            return note
    spec = spec_for(manifest, ev.candidate_id)
    return spec.notes if spec and spec.notes else "—"


def section_11_top3(
    recommend_three: list[CandidateEvaluation],
    manifest: ExperimentManifest,
) -> str:
    if not recommend_three:
        return "추천 가능한 후보 없음."
    lines = [
        "_실제 포집/여과 성능은 실험 검증 필요 (§3)._",
        "",
    ]
    for i, ev in enumerate(recommend_three[:3], start=1):
        lines.append(f"### 11-{i}. {ev.candidate_id} (점수 {ev.final_score:.3f})")
        lines.append(f"- {_feasibility_line(ev, manifest)}")
        lines.append("- xTB 수치·차원 점수: §6, §10 참조")
        lines.append("")
    return "\n".join(lines).rstrip()


def section_12_exclusions(
    *,
    excluded: list[CandidateEvaluation],
    ranked: list[CandidateEvaluation],
    recommend_three: list[CandidateEvaluation],
    manifest: ExperimentManifest,
) -> str:
    parts = ["### 12-1. 완전 제외"]
    if excluded:
        for ev in excluded:
            parts.append(f"- **{ev.candidate_id}:** §15-1 참조")
    else:
        parts.append("_없음._")

    parts.append("")
    parts.append("### 12-2. 실험 추천 제외 (대조군)")
    controls = [
        ev for ev in ranked
        if is_control_spec(spec_for(manifest, ev.candidate_id), ev.candidate_id)
    ]
    if controls:
        for ev in controls:
            spec = spec_for(manifest, ev.candidate_id)
            notes = (spec.notes if spec else None) or "—"
            parts.append(
                f"- **{ev.candidate_id}** (순위 {ev.rank}, 점수 {ev.final_score:.3f}): "
                f"대조군 — {notes} §11 추천 제외, §13 실험 대조 포함 (§4 참조)."
            )
    else:
        parts.append("_없음._")

    parts.append("")
    parts.append("### 12-3. 감점 후보")
    recommend_ids = {e.candidate_id for e in recommend_three}
    demoted: list[str] = []
    for ev in ranked:
        if ev.candidate_id in recommend_ids:
            continue
        if is_control_spec(spec_for(manifest, ev.candidate_id), ev.candidate_id):
            continue
        cautions = sum(1 for r in ev.agent_reviews if r.recommendation == "caution")
        reason = f"상위 3 밖 (순위 {ev.rank})"
        if cautions:
            reason += f", 주의 {cautions}건 (§7)"
        demoted.append(f"- **{ev.candidate_id}** (점수 {ev.final_score:.3f}): {reason}")
    parts.extend(demoted if demoted else ["_없음._"])
    return "\n".join(parts)


def section_13_experiment_design(
    top: CandidateEvaluation | None,
) -> str:
    candidate = top.candidate_id if top else "(미정)"
    return "\n".join(
        [
            f"- **주 실험군:** {candidate} (§11 1순위)",
            "- **대조군:** §12-2 목록",
            "- **절차:**",
            "  1. 실험군·대조군 필터를 동일 스캐폴드·동일 조건으로 준비",
            "  2. §14 통제 변인 고정 하에 시료 통과",
            "  3. 종속변인 측정 후 §6 지표와 **경향** 비교 (정량 예측 아님)",
        ]
    )


def section_14_variable_control(top: CandidateEvaluation | None, manifest: ExperimentManifest) -> str:
    if top is None:
        return "_추천 후보 없음._"
    review: AgentReview | None = None
    for r in top.agent_reviews:
        if r.agent_name == "Variable Control Agent":
            review = r
            break
    lines: list[str] = []
    if review and review.evidence_points:
        lines.extend(f"- {point}" for point in review.evidence_points)
    else:
        lines.extend(
            [
                "- **독립변인:** 필터 활성층 조합",
                "- **종속변인:** 잔류 농도·탁도·포집률(실측)",
                "- **통제변인:** pH, 이온강도, 온도, 농도, 유속, 접촉 시간",
                "- **반복:** n≥3",
            ]
        )
    controls = [c.candidate_id for c in manifest.candidates if candidate_role(c) == "대조군"]
    if controls:
        lines.append(f"- **대조군:** {', '.join(controls)} (§12-2)")
    return "\n".join(lines)


def section_15_1_run_failures(evaluations: list[CandidateEvaluation]) -> str:
    """Per-candidate failure causes for this run (single source of truth)."""
    records = collect_failure_records(evaluations)
    if not records:
        return "_본 실행에서 기록된 xTB 실패·제외·주의 없음._"

    lines = [
        "_이번 manifest 실행에서 발생한 실패·주의만 기록. 상세 원인의 단일 출처._",
        "",
        "| 후보 ID | 심각도 | 실패 유형 | 원인 | 권장 조치 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for rec in records:
        lines.append(
            f"| {rec.candidate_id} | {rec.severity} | {rec.failure_type} | "
            f"{rec.cause} | {rec.remediation} |"
        )
    return "\n".join(lines)


def section_15_2_anticipated_failure_modes() -> str:
    """Experimental execution risks (not harness/xTB run failures)."""
    return "\n".join(
        [
            "- pH·이온강도 변화로 표면 전하·코팅 효과 변동",
            "- 입자 크기·공극·유속이 지배적이면 코팅 효과 미미",
            "- 막 fouling·경쟁 이온 흡착",
            "- 동점 후보는 manifest 순서 타이브레이크 — 화학적 우열 아님 (부록 B)",
        ]
    )


def section_15_failures(evaluations: list[CandidateEvaluation]) -> str:
    return "\n".join(
        [
            "### 15-1. 본 실행 실패 원인",
            section_15_1_run_failures(evaluations),
            "",
            "### 15-2. 예상 실패 요인 (실험 실행)",
            section_15_2_anticipated_failure_modes(),
        ]
    )


def section_15_failure_modes() -> str:
    """Backward-compatible alias — full §15 body."""
    return section_15_2_anticipated_failure_modes()


def section_16_limitations() -> str:
    return "\n".join(
        [
            "- xTB·방법 한계: **§3 참조** (여과 효율 비주장 포함)",
            "- xTB Tool + 규칙 기반 MAS; 정전기 에이전트는 `charge`/목적 보완성 미반영 가능",
            "- 안전성 에이전트는 SDS/MSDS 대체 불가 (말미 면책)",
        ]
    )


def section_17_follow_up() -> str:
    return "\n".join(
        [
            "- 복합체 `.xyz` → 상호작용 에너지 proxy",
            "- 정전기 에이전트·동점 2차 기준 개선",
            "- 검증(Critic) 근거-문장 일치성 자동 검사",
        ]
    )


def appendix_b_ranking_rules() -> str:
    return "\n".join(
        [
            f"- **형식:** `{REPORT_FORMAT_VERSION}`",
            "- **최종 점수:** " + ", ".join(f"{k}×{v}" for k, v in WEIGHTS.items()),
            "- **순위:** `final_score` 내림차순; 동점은 공동 순위, 2차 기준 manifest 순서",
            "- **§11 추천:** 대조군 제외 후 상위 3 실험군",
            "- **§12-2:** 대조군은 추천 제외, 실험 대조에는 포함",
            "- **중복 정책:** 수치 §6, 차원 §10, 한계 §3, 규칙 본 부록만 본문 상세",
        ]
    )
