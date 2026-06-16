"""MAS prompt templates for MCP clients."""

ORCHESTRATOR_SYSTEM = """You are the Orchestrator for xTB Lab Harness.
1. Parse the experiment objective.
2. Ensure each candidate has a valid .xyz path.
3. Call MCP tools: calculate_candidate_batch → evaluate_candidates → generate_experiment_report.
4. Collect specialist agent reviews and produce a ranked recommendation.
5. Never claim xTB numbers that are not in tool JSON output.
"""

HYPOTHESIS_TEMPLATE = """실험 목적: {objective}
가설: 후보 물질의 xTB 전하 분포·쌍극자·상대 에너지 차이는 {objective}에서 관찰 가능한 효과 차이와 연관될 것이다.
"""

ELECTROSTATIC_PROMPT = """Interpret xTB partial charges and dipole for candidate {candidate_id}.
Use only: dipole_moment_debye, charge_summary fields from JSON.
"""

VDW_PROMPT = """Interpret non-covalent interaction *tendencies* from xTB results for {candidate_id}.
Do NOT claim high-precision dispersion decomposition.
"""

SAFETY_DISCLAIMER = (
    "본 시스템의 안전성 검토는 1차 필터링이며, "
    "실제 실험 전에는 공식 SDS/MSDS 확인이 필요하다."
)

CRITIC_CHECKLIST = """Before finalizing the report, verify:
1. Every recommendation cites xTB calculation evidence.
2. Interpretations match parsed numeric values.
3. The experiment design is feasible for a school lab.
4. Control variables are explicit.
5. Safety limitations are stated (SDS/MSDS still required).
6. Conclusions are not overstated beyond xTB semi-empirical accuracy.
"""

MCP_TOOL_SEQUENCE = """
Recommended MCP call order:
1. run_experiment_pipeline(manifest_path) — full pipeline
OR stepwise:
2. calculate_candidate_batch(candidates)
3. evaluate_candidates(objective, specs, results)
4. generate_experiment_report(objective, hypothesis, specs, evaluations)
"""
