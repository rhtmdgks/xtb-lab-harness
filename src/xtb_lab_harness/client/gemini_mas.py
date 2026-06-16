from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from xtb_lab_harness.agents.orchestrator import Orchestrator, load_manifest
from xtb_lab_harness.agents.schemas import ExperimentRunResult


def _gemini_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _load_genai_client():
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai not installed. Run: uv sync --extra llm"
        ) from exc

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY")
    return genai.Client(api_key=api_key)


def enrich_report_with_gemini(
    base_result: ExperimentRunResult,
    *,
    model: str | None = None,
) -> str:
    """Use Gemini to rewrite sections 10–14 with richer narrative (client-side MAS)."""
    if not _gemini_available():
        return base_result.report_markdown

    client = _load_genai_client()
    model_name = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    payload = {
        "experiment_objective": base_result.experiment_objective,
        "hypothesis": base_result.hypothesis,
        "top_candidates": [
            {
                "candidate_id": e.candidate_id,
                "final_score": e.final_score,
                "xtb": e.xtb_result.model_dump(mode="json"),
                "reviews": [r.model_dump(mode="json") for r in e.agent_reviews],
            }
            for e in sorted(
                [x for x in base_result.evaluations if x.rank is not None],
                key=lambda x: x.rank or 999,
            )[:5]
        ],
    }

    prompt = f"""You are the Orchestrator for xTB Lab Harness.
Given the JSON evidence below, rewrite ONLY sections 10–14 of the experiment report in Korean.
Do not invent xTB numbers not present in the JSON. State limitations clearly.

JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output markdown with headings:
## 10. 실험 설계안
## 11. 대조군 및 반복 실험 설계
## 12. 예상 실패 요인
## 13. 연구의 한계
## 14. 후속 연구
"""

    response = client.models.generate_content(model=model_name, contents=prompt)
    gemini_sections = response.text or ""

    marker = "## 10. 실험 설계안"
    if marker in base_result.report_markdown:
        head = base_result.report_markdown.split(marker)[0].rstrip()
        return f"{head}\n\n{gemini_sections.strip()}\n"
    return f"{base_result.report_markdown}\n\n{gemini_sections.strip()}\n"


def run_with_optional_gemini(
    manifest_path: str,
    *,
    output_path: str,
    reference_candidate_id: str | None = None,
    use_gemini: bool = False,
    model: str | None = None,
) -> ExperimentRunResult:
    manifest = load_manifest(manifest_path)
    result = Orchestrator().run(
        manifest,
        report_output_path=output_path,
        reference_candidate_id=reference_candidate_id,
    )

    if use_gemini and _gemini_available():
        enriched = enrich_report_with_gemini(result, model=model)
        result.report_markdown = enriched
        if result.report_path:
            Path(result.report_path).write_text(enriched, encoding="utf-8")

    return result
