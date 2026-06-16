from __future__ import annotations

import json
import os

from xtb_lab_harness.agents.schemas import (
    CandidateDebate,
    CandidateEvaluation,
    TaskPlan,
)


def _gemini_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _load_client():
    from google import genai

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=key)


def synthesize_orchestrator_report(
    *,
    user_command: str,
    task_plan: TaskPlan | None,
    evaluations: list[CandidateEvaluation],
    debates: list[CandidateDebate],
    evidence_markdown: str,
    base_report: str,
) -> str | None:
    """Orchestrator: compile complete report from all agent work + debates."""
    if not _gemini_available():
        return None

    client = _load_client()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    payload = {
        "user_command": user_command,
        "task_plan": task_plan.model_dump(mode="json") if task_plan else None,
        "evaluations": [e.model_dump(mode="json") for e in evaluations],
        "debates": [d.model_dump(mode="json") for d in debates],
        "evidence_table": evidence_markdown,
    }
    prompt = f"""You are the Orchestrator Agent for xTB Lab Harness.
Compile a COMPLETE experiment design report in Korean from ALL agent outputs and debates.
Rules:
- Include every section 1-14 from the base report structure.
- Add section "## 6.5 에이전트 토론 (Harness Debate)" with full debate transcripts summarized per candidate.
- Add section "## 오케스트레이터 종합" synthesizing task assignment, parallel reviews, debate outcomes, final ranking.
- NEVER invent xTB numbers not in JSON.
- State safety disclaimer and xTB limitations.

Base report (reference):
{base_report}

Full JSON evidence:
{json.dumps(payload, ensure_ascii=False)}

Output complete markdown report only.
"""
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return (response.text or "").strip() or None
    except Exception:
        return None
