# MAS Agents

Rule-based specialist agents in `src/xtb_lab_harness/agents/`.

## Pipeline

```text
manifest.json
  → screen_candidates (Candidate Material)
  → calculate_candidate_batch (xTB)
  → specialist reviews × N
  → Critic review
  → weighted final score
  → rank + 14-section report
```

## Scoring (Research Plan §13)

```text
Final =
  0.25 × Electrostatic
+ 0.20 × Structural Stability
+ 0.20 × Experimental Feasibility
+ 0.15 × Safety
+ 0.10 × Variable Control
+ 0.10 × Critic Reliability
```

## Agent files

| File | Agent |
| --- | --- |
| `hypothesis.py` | Hypothesis |
| `candidate_material.py` | Candidate Material |
| `electrostatic.py` | Electrostatic Interaction |
| `vdw_dispersion.py` | vdW / Dispersion Interpretation |
| `structural_stability.py` | Structural Stability |
| `safety.py` | Safety Reasoning |
| `variable_control.py` | Variable Control |
| `critic.py` | Critic |
| `orchestrator.py` | Orchestrator |
| `prompts.py` | Client-side prompt templates |

## Exclusion rules

Candidates are marked `excluded` when Structural Stability, Safety, or Critic agents recommend `exclude`.

## LLM integration

- **Default:** all agent logic is deterministic Python (no API key).
- **Optional:** `xtb-lab-run --gemini` rewrites report sections 10–14 via Gemini on the client.
