from __future__ import annotations

import pytest

from xtb_lab_harness.agents.schemas import AgentReview, DimensionScores


def test_weights_sum_to_one() -> None:
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_compute_final_score() -> None:
    dimensions = DimensionScores(
        electrostatic=1.0,
        structural_stability=1.0,
        experimental_feasibility=1.0,
        safety=1.0,
        variable_control=1.0,
        critic_reliability=1.0,
    )
    assert compute_final_score(dimensions) == pytest.approx(1.0)


def test_score_from_reviews_maps_agents() -> None:
    reviews = [
        AgentReview(
            agent_name="Electrostatic Interaction Agent",
            candidate_id="water",
            score=0.8,
            summary="test",
        ),
        AgentReview(
            agent_name="Structural Stability Agent",
            candidate_id="water",
            score=0.9,
            summary="test",
        ),
        AgentReview(
            agent_name="Candidate Material Agent",
            candidate_id="water",
            score=0.85,
            summary="test",
        ),
        AgentReview(
            agent_name="van der Waals / Dispersion Interpretation Agent",
            candidate_id="water",
            score=0.7,
            summary="test",
        ),
    ]
    dims = score_from_reviews(reviews)
    assert dims.electrostatic == 0.8
    assert dims.structural_stability == 0.9
    assert dims.experimental_feasibility == pytest.approx(0.55 * 0.85 + 0.45 * 0.7)

from xtb_lab_harness.agents.scoring import WEIGHTS, compute_final_score, score_from_reviews