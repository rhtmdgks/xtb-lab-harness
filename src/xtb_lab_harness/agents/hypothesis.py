from __future__ import annotations


def generate_hypothesis(experiment_objective: str) -> str:
    """Convert a natural-language experiment objective into a testable hypothesis."""
    objective = experiment_objective.strip()
    if not objective:
        return (
            "후보 물질의 xTB 계산 지표(전하 분포, 쌍극자 모멘트, 상대 에너지) 차이는 "
            "실험 조건에서 관찰 가능한 상호작용 또는 효과 차이와 연관될 것이다."
        )
    return (
        f"실험 목적「{objective}」에 대해, 후보 물질 간 xTB 기반 전하 분포·쌍극자 모멘트·"
        "구조 안정성(상대 에너지) 차이는 관찰 가능한 실험 효과 차이를 설명하는 "
        "정량적 근거를 제공할 것이다."
    )
