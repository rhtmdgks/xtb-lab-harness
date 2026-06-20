from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from xtb_lab_harness.agents.candidate_material import screen_candidates
from xtb_lab_harness.agents.critic import CriticAgent
from xtb_lab_harness.agents.debate import DebateEngine
from xtb_lab_harness.agents.hypothesis import generate_hypothesis
from xtb_lab_harness.agents.parallel import run_specialists_parallel
from xtb_lab_harness.agents.registry import ALL_SPECIALIST_AGENTS, CRITIC
from xtb_lab_harness.agents.schemas import (
    CandidateDebate,
    CandidateEvaluation,
    ExperimentManifest,
    ExperimentRunResult,
    TaskPlan,
)
from xtb_lab_harness.agents.scoring import compute_final_score, score_from_reviews
from xtb_lab_harness.client.llm_orchestrator import plan_from_user_command
from xtb_lab_harness.client.report_synthesis import synthesize_orchestrator_report
from xtb_lab_harness.config.paths import resolve_xyz_path
from xtb_lab_harness.reports.experiment import generate_experiment_report
from xtb_lab_harness.tools.analyze import calculate_candidate_batch
from xtb_lab_harness.tools.compare import generate_evidence_table
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


def _llm_enabled() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


class Orchestrator:
    """LLM MAS pipeline: plan → parallel xTB → parallel agents → debate → report."""

    def __init__(self) -> None:
        self._critic = CriticAgent()
        self._debate = DebateEngine()

    def run(
        self,
        manifest: ExperimentManifest,
        *,
        user_command: str | None = None,
        use_llm: bool = False,
        report_output_path: str | Path | None = None,
        reference_candidate_id: str | None = None,
        parallel_xtb: bool = True,
    ) -> ExperimentRunResult:
        command = user_command or manifest.experiment_objective
        task_plan: TaskPlan | None = None
        objective = manifest.experiment_objective
        hypothesis = generate_hypothesis(objective)

        if user_command or use_llm:
            task_plan = plan_from_user_command(command, manifest, use_llm=_llm_enabled())
            objective = task_plan.experiment_objective
            hypothesis = task_plan.hypothesis
            manifest = manifest.model_copy(update={"experiment_objective": objective})

        assigned = task_plan.assigned_agents if task_plan else list(ALL_SPECIALIST_AGENTS)
        debate_rounds = task_plan.debate_rounds if task_plan else 2

        accepted, pre_rejected = screen_candidates(manifest.candidates, experiment_objective=objective)

        batch_payload = [
            {
                "candidate_id": c.candidate_id,
                "xyz_path": c.xyz_path,
                "gfn": c.gfn,
                "charge": c.charge,
                "uhf": c.uhf,
            }
            for c in accepted
        ]
        batch = calculate_candidate_batch(batch_payload, parallel=parallel_xtb)
        xtb_results: list[CandidateResult] = list(batch.results)
        spec_by_id = {c.candidate_id: c for c in accepted}

        evaluations: list[CandidateEvaluation] = []
        all_debates: list[CandidateDebate] = []

        for result in xtb_results:
            spec = spec_by_id[result.candidate_id]
            reviews = run_specialists_parallel(
                spec,
                result,
                objective,
                assigned_agents=assigned,
            )

            debate: CandidateDebate | None = None
            if result.calculation_status == CalculationStatus.SUCCESS:
                debate = self._debate.conduct(
                    result.candidate_id,
                    reviews,
                    result,
                    experiment_objective=objective,
                    rounds=debate_rounds,
                    use_llm=_llm_enabled(),
                )
                all_debates.append(debate)

            dimensions = score_from_reviews(reviews)
            evaluation = CandidateEvaluation(
                candidate_id=result.candidate_id,
                xtb_result=result,
                agent_reviews=reviews,
                dimension_scores=dimensions,
                final_score=compute_final_score(dimensions),
                debate=debate,
            )

            critic_review = self._critic.review_evaluation(evaluation)
            evaluation.agent_reviews.append(critic_review)
            evaluation.dimension_scores = self._critic.adjust_dimension_scores(
                evaluation.dimension_scores,
                critic_review.score,
            )
            evaluation.final_score = compute_final_score(evaluation.dimension_scores)
            if debate:
                evaluation.final_score = max(
                    0.0,
                    min(1.0, evaluation.final_score + debate.score_adjustment),
                )
                if debate.revised_recommendation == "exclude":
                    evaluation.excluded = True
                    evaluation.exclusion_reason = f"토론 합의 제외: {debate.consensus_summary}"

            if any(
                r.recommendation == "exclude"
                for r in evaluation.agent_reviews
                if r.agent_name in ("Structural Stability Agent", "Safety Reasoning Agent", CRITIC)
            ):
                evaluation.excluded = True
                evaluation.exclusion_reason = evaluation.exclusion_reason or _exclusion_reason(
                    evaluation.agent_reviews,
                )

            evaluations.append(evaluation)

        for spec, reason in pre_rejected:
            evaluations.append(
                CandidateEvaluation(
                    candidate_id=spec.candidate_id,
                    xtb_result=CandidateResult(
                        candidate_id=spec.candidate_id,
                        calculation_status=CalculationStatus.FAILED,
                        error_message=reason,
                    ),
                    agent_reviews=[],
                    dimension_scores=score_from_reviews([]),
                    final_score=0.0,
                    excluded=True,
                    exclusion_reason=reason,
                ),
            )

        ranked = sorted(
            [e for e in evaluations if not e.excluded],
            key=lambda e: e.final_score,
            reverse=True,
        )
        for rank, evaluation in enumerate(ranked, start=1):
            evaluation.rank = rank

        evidence = generate_evidence_table(
            [e.xtb_result for e in evaluations],
            reference_candidate_id=reference_candidate_id,
        )

        base_report = generate_experiment_report(
            experiment_objective=objective,
            hypothesis=hypothesis,
            manifest=manifest,
            evaluations=evaluations,
            evidence_table_markdown=evidence.markdown,
            task_plan=task_plan,
            debates=all_debates,
        )

        orchestrator_synthesis: str | None = None
        report_md = base_report
        if _llm_enabled():
            orchestrator_synthesis = synthesize_orchestrator_report(
                user_command=command,
                task_plan=task_plan,
                evaluations=evaluations,
                debates=all_debates,
                evidence_markdown=evidence.markdown,
                base_report=base_report,
            )
            if orchestrator_synthesis:
                report_md = orchestrator_synthesis

        report_path: str | None = None
        if report_output_path:
            path = Path(report_output_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report_md, encoding="utf-8")
            report_path = str(path)
            _write_run_artifacts(path.parent, manifest, evaluations, xtb_results, all_debates, task_plan)

        return ExperimentRunResult(
            user_command=user_command,
            task_plan=task_plan,
            experiment_objective=objective,
            hypothesis=hypothesis,
            candidate_specs=manifest.candidates,
            xtb_results=xtb_results,
            evaluations=evaluations,
            debates=all_debates,
            orchestrator_synthesis=orchestrator_synthesis,
            evidence_table_markdown=evidence.markdown,
            report_markdown=report_md,
            report_path=report_path,
        )

    def evaluate_from_xtb_results(
        self,
        manifest: ExperimentManifest,
        xtb_results: list[CandidateResult],
        *,
        use_llm: bool = False,
        debate_rounds: int = 2,
    ) -> list[CandidateEvaluation]:
        assigned = list(ALL_SPECIALIST_AGENTS)
        evaluations: list[CandidateEvaluation] = []
        spec_by_id = {c.candidate_id: c for c in manifest.candidates}

        for result in xtb_results:
            spec = spec_by_id.get(result.candidate_id)
            if spec is None:
                continue
            reviews = run_specialists_parallel(
                spec,
                result,
                manifest.experiment_objective,
                assigned_agents=assigned,
            )
            debate = None
            if result.calculation_status == CalculationStatus.SUCCESS:
                debate = self._debate.conduct(
                    result.candidate_id,
                    reviews,
                    result,
                    experiment_objective=manifest.experiment_objective,
                    rounds=debate_rounds,
                    use_llm=_llm_enabled(),
                )
            dimensions = score_from_reviews(reviews)
            evaluation = CandidateEvaluation(
                candidate_id=result.candidate_id,
                xtb_result=result,
                agent_reviews=reviews,
                dimension_scores=dimensions,
                final_score=compute_final_score(dimensions),
                debate=debate,
            )
            critic_review = self._critic.review_evaluation(evaluation)
            evaluation.agent_reviews.append(critic_review)
            evaluation.dimension_scores = self._critic.adjust_dimension_scores(
                evaluation.dimension_scores,
                critic_review.score,
            )
            evaluation.final_score = compute_final_score(evaluation.dimension_scores)
            evaluations.append(evaluation)

        ranked = sorted(evaluations, key=lambda e: e.final_score, reverse=True)
        for rank, ev in enumerate(ranked, start=1):
            ev.rank = rank
        return evaluations


def _exclusion_reason(reviews) -> str:
    for review in reviews:
        if review.recommendation == "exclude":
            return f"{review.agent_name}: {review.summary}"
    return "에이전트 제외 권고"


def _write_run_artifacts(
    directory: Path,
    manifest: ExperimentManifest,
    evaluations: list[CandidateEvaluation],
    xtb_results: list[CandidateResult],
    debates: list[CandidateDebate],
    task_plan: TaskPlan | None,
) -> None:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    bundle = directory / f"run_{timestamp}"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    if task_plan:
        (bundle / "task_plan.json").write_text(task_plan.model_dump_json(indent=2), encoding="utf-8")
    (bundle / "xtb_results.json").write_text(
        json.dumps([r.model_dump(mode="json") for r in xtb_results], indent=2),
        encoding="utf-8",
    )
    (bundle / "evaluations.json").write_text(
        json.dumps([e.model_dump(mode="json") for e in evaluations], indent=2),
        encoding="utf-8",
    )
    (bundle / "debates.json").write_text(
        json.dumps([d.model_dump(mode="json") for d in debates], indent=2),
        encoding="utf-8",
    )


def load_manifest(path: str | Path) -> ExperimentManifest:
    manifest_path = Path(path).expanduser().resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = ExperimentManifest.model_validate(data)
    resolved_candidates = [
        candidate.model_copy(
            update={"xyz_path": resolve_xyz_path(candidate.xyz_path, manifest_path)},
        )
        for candidate in manifest.candidates
    ]
    return manifest.model_copy(update={"candidates": resolved_candidates})
