from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.agents.orchestrator import Orchestrator, load_manifest
from xtb_lab_harness.agents.schemas import ExperimentRunResult
from xtb_lab_harness.config.env import load_project_env


def _gemini_available() -> bool:
    import os

    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def run_mas_pipeline(
    manifest_path: str,
    *,
    user_command: str | None = None,
    output_path: str,
    reference_candidate_id: str | None = None,
    use_llm: bool = True,
) -> ExperimentRunResult:
    load_project_env()
    manifest = load_manifest(manifest_path)
    command = user_command or manifest.experiment_objective
    return Orchestrator().run(
        manifest,
        user_command=command,
        use_llm=use_llm and _gemini_available(),
        report_output_path=output_path,
        reference_candidate_id=reference_candidate_id,
    )


def run_with_optional_gemini(
    manifest_path: str,
    *,
    output_path: str,
    reference_candidate_id: str | None = None,
    use_gemini: bool = False,
    user_command: str | None = None,
    model: str | None = None,
) -> ExperimentRunResult:
    import os

    load_project_env()
    if model:
        os.environ["GEMINI_MODEL"] = model
    return run_mas_pipeline(
        manifest_path,
        user_command=user_command,
        output_path=output_path,
        reference_candidate_id=reference_candidate_id,
        use_llm=use_gemini,
    )
