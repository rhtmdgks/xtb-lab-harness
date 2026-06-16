from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from xtb_lab_harness.agents.registry import (
    SAFETY,
    build_specialist_agents,
)
from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.xtb.schemas import CandidateResult


def run_specialists_parallel(
    spec: CandidateSpec,
    result: CandidateResult,
    objective: str,
    *,
    assigned_agents: list[str] | None = None,
    max_workers: int | None = None,
) -> list[AgentReview]:
    """Run specialist agents concurrently for one candidate."""
    agents = build_specialist_agents()
    names = assigned_agents or list(agents.keys())
    active = [name for name in names if name in agents]

    reviews: list[AgentReview] = []

    def _run_one(agent_name: str) -> AgentReview:
        agent = agents[agent_name]
        if agent_name == SAFETY:
            return agent.review(  # type: ignore[union-attr]
                spec.candidate_id,
                notes=spec.notes,
                safety_flags=spec.safety_flags,
            )
        return agent.review(spec, result, experiment_objective=objective)  # type: ignore[union-attr]

    workers = max_workers or len(active)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one, name): name for name in active}
        for future in as_completed(futures):
            reviews.append(future.result())

    order = {name: idx for idx, name in enumerate(active)}
    reviews.sort(key=lambda r: order.get(r.agent_name, 999))
    return reviews
