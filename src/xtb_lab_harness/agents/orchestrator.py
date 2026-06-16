from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from xtb_lab_harness.agents.candidate_material import (
    review_candidate_material,
    screen_candidates,
)
from xtb_lab_harness.agents.critic import CriticAgent
from xtb_lab_harness.agents.electrostatic import ElectrostaticAgent
from xtb_lab_harness.agents.hypothesis import generate_hypothesis
from xtb_lab_harness.agents.safety import SafetyAgent
from xtb_lab_harness.agents.schemas import (
    CandidateEvaluation,
    CandidateSpec,
    ExperimentManifest,
    ExperimentRunResult,
)
from xtb_lab_harness.agents.scoring import compute_final_score, score_from_reviews
from xtb_lab_harness.agents.structural_stability import StructuralStabilityAgent
from xtb_lab_harness.agents.variable_control import VariableControlAgent
from xtb_lab_harness.agents.vdw_dispersion import VdwDispersionAgent
from xtb_lab_harness.reports.experiment import generate_experiment_report
from xtb_lab_harness.tools.analyze import calculate_candidate_batch
from xtb_lab_harness.tools.compare import generate_evidence_table
from xtb_lab_harness.xtb.schemas import CalculationStatus, CandidateResult


class Orchestrator:
    """Run the full xTB + MAS evaluation pipeline."""

    def __init__(self) -> None:
        self._electrostatic = ElectrostaticAgent()
        self._vdw = VdwDispersionAgent()
        self._stability = StructuralStabilityAgent()
        self._safety = SafetyAgent()
        self._variable = VariableControlAgent()
        self._critic = CriticAgent()

    def run(
        self,
        manifest: ExperimentManifest,
        *,
        report_output_path: str | Path | None = None,
        reference_candidate_id: str | None = None,
    ) -> ExperimentRunResult:
        objective = manifest.experiment_objective
        hypothesis = generate_hypothesis(objective)

        accepted, pre_rejected = screen_candidates(
            manifest.candidates,
            experiment_objective=objective,
        )

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
        batch = calculate_candidate_batch(batch_payload)
        xtb_results: list[CandidateResult] = list(batch.results)

        spec_by_id = {c.candidate_id: c for c in accepted}
        evaluations: list[CandidateEvaluation] = []

        for result in xtb_results:
            spec = spec_by_id[result.candidate_id]
            reviews = self._run_specialist_reviews(spec, result, objective)
            dimensions = score_from_reviews(reviews)

            evaluation = CandidateEvaluation(
                candidate_id=result.candidate_id,
                xtb_result=result,
                agent_reviews=reviews,
                dimension_scores=dimensions,
                final_score=compute_final_score(dimensions),
            )
            critic_review = self._critic.review_evaluation(evaluation)
            evaluation.agent_reviews.append(critic_review)
            evaluation.dimension_scores = self._critic.adjust_dimension_scores(
                evaluation.dimension_scores,
                critic_review.score,
            )
            evaluation.final_score = compute_final_score(evaluation.dimension_scores)

            if any(
                r.recommendation == "exclude"
                for r in evaluation.agent_reviews
                if r.agent_name in ("Structural Stability Agent", "Safety Reasoning Agent", "Critic Agent")
            ):
                evaluation.excluded = True
                evaluation.exclusion_reason = _first_exclusion_reason(evaluation.agent_reviews)

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

        report_md = generate_experiment_report(
            experiment_objective=objective,
            hypothesis=hypothesis,
            manifest=manifest,
            evaluations=evaluations,
            evidence_table_markdown=evidence.markdown,
        )

        report_path: str | None = None
        if report_output_path:
            path = Path(report_output_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report_md, encoding="utf-8")
            report_path = str(path)
            _write_run_artifacts(path.parent, manifest, evaluations, xtb_results)

        return ExperimentRunResult(
            experiment_objective=objective,
            hypothesis=hypothesis,
            candidate_specs=manifest.candidates,
            xtb_results=xtb_results,
            evaluations=evaluations,
            evidence_table_markdown=evidence.markdown,
            report_markdown=report_md,
            report_path=report_path,
        )

    def _run_specialist_reviews(
        self,
        spec: CandidateSpec,
        result: CandidateResult,
        objective: str,
    ):
        reviews = [
            review_candidate_material(spec, result, experiment_objective=objective),
            self._electrostatic.review(spec, result, experiment_objective=objective),
            self._vdw.review(spec, result, experiment_objective=objective),
            self._stability.review(spec, result, experiment_objective=objective),
            self._safety.review(
                spec.candidate_id,
                notes=spec.notes,
                safety_flags=spec.safety_flags,
            ),
            self._variable.review_for_experiment(spec, experiment_objective=objective),
        ]
        return reviews

    def evaluate_from_xtb_results(
        self,
        manifest: ExperimentManifest,
        xtb_results: list[CandidateResult],
    ) -> list[CandidateEvaluation]:
        """Run specialist + critic agents on existing xTB results."""
        spec_by_id = {c.candidate_id: c for c in manifest.candidates}
        evaluations: list[CandidateEvaluation] = []

        for result in xtb_results:
            spec = spec_by_id.get(result.candidate_id)
            if spec is None:
                continue
            reviews = self._run_specialist_reviews(
                spec,
                result,
                manifest.experiment_objective,
            )
            dimensions = score_from_reviews(reviews)
            evaluation = CandidateEvaluation(
                candidate_id=result.candidate_id,
                xtb_result=result,
                agent_reviews=reviews,
                dimension_scores=dimensions,
                final_score=compute_final_score(dimensions),
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


def _first_exclusion_reason(reviews) -> str:
    for review in reviews:
        if review.recommendation == "exclude":
            return f"{review.agent_name}: {review.summary}"
    return "에이전트 제외 권고"


def _write_run_artifacts(
    directory: Path,
    manifest: ExperimentManifest,
    evaluations: list[CandidateEvaluation],
    xtb_results: list[CandidateResult],
) -> None:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    bundle = directory / f"run_{timestamp}"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "manifest.json").write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (bundle / "xtb_results.json").write_text(
        json.dumps([r.model_dump(mode="json") for r in xtb_results], indent=2),
        encoding="utf-8",
    )
    (bundle / "evaluations.json").write_text(
        json.dumps([e.model_dump(mode="json") for e in evaluations], indent=2),
        encoding="utf-8",
    )


def load_manifest(path: str | Path) -> ExperimentManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ExperimentManifest.model_validate(data)
