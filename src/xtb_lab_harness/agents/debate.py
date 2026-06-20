from __future__ import annotations

import json
import os
import re
from typing import Literal

from xtb_lab_harness.agents.schemas import (
    AgentReview,
    CandidateDebate,
    DebateMessage,
    DebateRound,
)
from xtb_lab_harness.xtb.schemas import CandidateResult


def _gemini_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _load_client():
    from google import genai

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=key)


class DebateEngine:
    """Multi-agent debate after parallel specialist reviews."""

    def conduct(
        self,
        candidate_id: str,
        reviews: list[AgentReview],
        result: CandidateResult,
        *,
        experiment_objective: str,
        rounds: int = 2,
        use_llm: bool = True,
    ) -> CandidateDebate:
        if use_llm and _gemini_available():
            try:
                return self._gemini_debate(
                    candidate_id,
                    reviews,
                    result,
                    experiment_objective=experiment_objective,
                    rounds=rounds,
                )
            except Exception:
                pass
        return self._rule_debate(candidate_id, reviews, rounds=rounds)

    def _rule_debate(
        self,
        candidate_id: str,
        reviews: list[AgentReview],
        *,
        rounds: int,
    ) -> CandidateDebate:
        debate_rounds: list[DebateRound] = []
        by_name = {r.agent_name: r for r in reviews}

        for round_num in range(1, rounds + 1):
            messages: list[DebateMessage] = []
            for review in reviews:
                target = _find_challenge_target(review, reviews)
                if target:
                    messages.append(
                        DebateMessage(
                            agent_name=review.agent_name,
                            round_number=round_num,
                            message=(
                                f"{target.agent_name}의 우려('{target.concerns[0] if target.concerns else target.summary}')에 대해 "
                                f"xTB 근거({'; '.join(review.evidence_points[:2]) or 'see review'})로 재검토함."
                            ),
                            responds_to=target.agent_name,
                            stance="challenge" if review.recommendation != target.recommendation else "support",
                        )
                    )
                else:
                    messages.append(
                        DebateMessage(
                            agent_name=review.agent_name,
                            round_number=round_num,
                            message=review.summary,
                            stance="support",
                        )
                    )

            synthesis = _synthesize_round(messages, by_name)
            debate_rounds.append(
                DebateRound(round_number=round_num, messages=messages, round_synthesis=synthesis)
            )

        consensus, rec, adj = _final_consensus(reviews, debate_rounds)
        return CandidateDebate(
            candidate_id=candidate_id,
            rounds=debate_rounds,
            consensus_summary=consensus,
            revised_recommendation=rec,
            score_adjustment=adj,
        )

    def _gemini_debate(
        self,
        candidate_id: str,
        reviews: list[AgentReview],
        result: CandidateResult,
        *,
        experiment_objective: str,
        rounds: int,
    ) -> CandidateDebate:
        client = _load_client()
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        payload = {
            "candidate_id": candidate_id,
            "experiment_objective": experiment_objective,
            "xtb_result": result.model_dump(mode="json"),
            "agent_reviews": [r.model_dump(mode="json") for r in reviews],
            "debate_rounds": rounds,
        }
        prompt = f"""You simulate a multi-agent scientific debate for xTB Lab Harness.
Agents must challenge each other using ONLY xTB evidence in the JSON.
Output valid JSON only:
{{
  "rounds": [
    {{
      "round_number": 1,
      "messages": [
        {{
          "agent_name": "...",
          "round_number": 1,
          "message": "...",
          "responds_to": "other agent or null",
          "stance": "support|challenge|revise|concede|synthesize"
        }}
      ],
      "round_synthesis": "..."
    }}
  ],
  "consensus_summary": "...",
  "revised_recommendation": "include|exclude|caution",
  "score_adjustment": -0.1 to 0.1
}}

JSON input:
{json.dumps(payload, ensure_ascii=False)}
"""
        response = client.models.generate_content(model=model, contents=prompt)
        text = (response.text or "").strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        return CandidateDebate(
            candidate_id=candidate_id,
            rounds=[DebateRound.model_validate(r) for r in data["rounds"]],
            consensus_summary=data["consensus_summary"],
            revised_recommendation=data["revised_recommendation"],
            score_adjustment=float(data.get("score_adjustment", 0.0)),
        )


def _find_challenge_target(review: AgentReview, all_reviews: list[AgentReview]) -> AgentReview | None:
    for other in all_reviews:
        if other.agent_name == review.agent_name:
            continue
        if other.recommendation != review.recommendation or other.concerns:
            return other
    return None


def _synthesize_round(messages: list[DebateMessage], by_name: dict[str, AgentReview]) -> str:
    challenges = [m for m in messages if m.stance == "challenge"]
    if not challenges:
        return "에이전트 간 큰 이견 없음. 초기 검토 유지."
    agents = ", ".join({m.agent_name for m in challenges})
    return f"{agents} 간 근거 대조 완료. xTB 수치 기준으로 입장 조정 검토."


def _final_consensus(
    reviews: list[AgentReview],
    rounds: list[DebateRound],
) -> tuple[str, Literal["include", "exclude", "caution"], float]:
    excludes = sum(1 for r in reviews if r.recommendation == "exclude")
    cautions = sum(1 for r in reviews if r.recommendation == "caution")
    last = rounds[-1].round_synthesis if rounds else ""

    if excludes >= 2:
        return f"다수 exclude 권고. 토론 결론: 제외. {last}", "exclude", -0.1
    if cautions >= 2:
        return f"주의 필요. 조건부 포함. {last}", "caution", -0.03
    return f"포함 합의. {last}", "include", 0.05
