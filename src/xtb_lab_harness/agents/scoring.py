from __future__ import annotations

from xtb_lab_harness.agents.schemas import AgentReview, DimensionScores

WEIGHTS = {
    "electrostatic": 0.25,
    "structural_stability": 0.20,
    "experimental_feasibility": 0.20,
    "safety": 0.15,
    "variable_control": 0.10,
    "critic_reliability": 0.10,
}


def score_from_reviews(reviews: list[AgentReview]) -> DimensionScores:
    """Map specialist agent reviews into dimension scores."""
    by_agent = {review.agent_name: review.score for review in reviews}

    return DimensionScores(
        electrostatic=by_agent.get("Electrostatic Interaction Agent", 0.0),
        structural_stability=by_agent.get("Structural Stability Agent", 0.0),
        experimental_feasibility=_experimental_feasibility_score(by_agent),
        safety=by_agent.get("Safety Reasoning Agent", 0.0),
        variable_control=by_agent.get("Variable Control Agent", 0.0),
        critic_reliability=by_agent.get("Critic Agent", 0.0),
    )


def _experimental_feasibility_score(by_agent: dict[str, float]) -> float:
    material = by_agent.get("Candidate Material Agent", 0.0)
    vdw = by_agent.get("van der Waals / Dispersion Interpretation Agent", 0.0)
    return min(1.0, 0.55 * material + 0.45 * vdw)


def compute_final_score(dimensions: DimensionScores) -> float:
    return (
        WEIGHTS["electrostatic"] * dimensions.electrostatic
        + WEIGHTS["structural_stability"] * dimensions.structural_stability
        + WEIGHTS["experimental_feasibility"] * dimensions.experimental_feasibility
        + WEIGHTS["safety"] * dimensions.safety
        + WEIGHTS["variable_control"] * dimensions.variable_control
        + WEIGHTS["critic_reliability"] * dimensions.critic_reliability
    )
