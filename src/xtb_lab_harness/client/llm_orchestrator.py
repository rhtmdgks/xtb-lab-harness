from __future__ import annotations

import json
import os
import re

from xtb_lab_harness.agents.hypothesis import generate_hypothesis
from xtb_lab_harness.agents.registry import ALL_SPECIALIST_AGENTS
from xtb_lab_harness.agents.schemas import CandidateSpec, ExperimentManifest, TaskPlan


def _gemini_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _load_client():
    from google import genai

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=key)


def plan_from_user_command(
    user_command: str,
    manifest: ExperimentManifest,
    *,
    use_llm: bool = True,
) -> TaskPlan:
    """LLM Orchestrator: parse user command → assign agents + refine objective."""
    if use_llm and _gemini_available():
        try:
            return _gemini_plan(user_command, manifest)
        except Exception:
            pass
    return _fallback_plan(user_command, manifest)


def _fallback_plan(user_command: str, manifest: ExperimentManifest) -> TaskPlan:
    objective = manifest.experiment_objective or user_command
    return TaskPlan(
        user_command=user_command,
        experiment_objective=objective,
        hypothesis=generate_hypothesis(objective),
        assigned_agents=list(ALL_SPECIALIST_AGENTS),
        debate_rounds=2,
        orchestrator_reasoning="규칙 기반: 전문 에이전트 전원 투입, 2라운드 토론.",
        focus_points=["xTB 근거", "변인통제", "안전성"],
    )


def _gemini_plan(user_command: str, manifest: ExperimentManifest) -> TaskPlan:
    client = _load_client()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    candidates = [c.model_dump(mode="json") for c in manifest.candidates]
    prompt = f"""You are the Orchestrator Agent for xTB Lab Harness.
Parse the user command, decide which specialist agents to assign, and refine the experiment objective.
Available agents: {ALL_SPECIALIST_AGENTS}
User command: {user_command}
Manifest objective: {manifest.experiment_objective}
Candidates: {json.dumps(candidates, ensure_ascii=False)}

Return JSON only:
{{
  "experiment_objective": "...",
  "hypothesis": "...",
  "assigned_agents": ["..."],
  "debate_rounds": 2,
  "orchestrator_reasoning": "why these agents",
  "focus_points": ["..."]
}}
Assign ALL relevant specialists unless user scope is very narrow. debate_rounds: 2-3.
"""
    response = client.models.generate_content(model=model, contents=prompt)
    text = (response.text or "").strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    assigned = [a for a in data.get("assigned_agents", ALL_SPECIALIST_AGENTS) if a in ALL_SPECIALIST_AGENTS]
    if not assigned:
        assigned = list(ALL_SPECIALIST_AGENTS)
    return TaskPlan(
        user_command=user_command,
        experiment_objective=data.get("experiment_objective", manifest.experiment_objective),
        hypothesis=data.get("hypothesis", generate_hypothesis(manifest.experiment_objective)),
        assigned_agents=assigned,
        debate_rounds=int(data.get("debate_rounds", 2)),
        orchestrator_reasoning=data.get("orchestrator_reasoning", ""),
        focus_points=data.get("focus_points", []),
    )
