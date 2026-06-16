from __future__ import annotations

HIGH_RISK_KEYWORDS = (
    "cyanide",
    "peroxide",
    "azide",
    "fluorine",
    "chlorine_gas",
    "benzene_high_conc",
    "explosive",
    "toxic",
    "발암",
    "폭발",
    "강산",
    "강염기",
)

COMMON_LAB_SAFE = ("water", "ethanol", "methanol", "acetone", "ammonia", "methane", "urea")


class SafetyAgent:
    name = "Safety Reasoning Agent"
    disclaimer = (
        "본 시스템의 안전성 검토는 1차 필터링이며, "
        "실제 실험 전에는 공식 SDS/MSDS 확인이 필요하다."
    )

    def review(
        self,
        candidate_id: str,
        *,
        notes: str | None = None,
        safety_flags: list[str] | None = None,
    ):
        from xtb_lab_harness.agents.schemas import AgentReview

        flags = list(safety_flags or [])
        text = f"{candidate_id} {notes or ''}".lower()
        concerns: list[str] = []

        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in text:
                flags.append(keyword)
                concerns.append(f"고위험 키워드 감지: {keyword}")

        score = 0.75
        if candidate_id.lower() in COMMON_LAB_SAFE:
            score = 0.9
        if flags:
            score = max(0.1, 0.75 - 0.25 * len(flags))

        recommendation = "include"
        if score < 0.4:
            recommendation = "exclude"
        elif score < 0.65:
            recommendation = "caution"

        return AgentReview(
            agent_name=self.name,
            candidate_id=candidate_id,
            score=score,
            summary=(
                "LLM 일반 지식·후보 메타데이터 기반 1차 안전성 검토. "
                + self.disclaimer
            ),
            evidence_points=[f"후보 ID: {candidate_id}", f"안전 플래그: {flags or '없음'}"],
            concerns=concerns,
            recommendation=recommendation,
        )
