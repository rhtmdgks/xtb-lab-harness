# Architecture

```text
[LLM / MAS Runtime — MCP CLIENT]
  Gemini / Cursor / Claude / custom runner
  Optional: client/gemini_mas.py for narrative enrichment
        |
        |  stdio MCP
        v
[xTB Lab Harness MCP SERVER]
  calculate_candidate
  calculate_candidate_batch
  generate_evidence_table
  evaluate_candidates
  run_experiment_pipeline
  generate_experiment_report
        |
        +--> [agents/orchestrator.py]  rule-based MAS (also via xtb-lab-run CLI)
        |
        |  subprocess
        v
[xTB CLI]  --gfn 2 --opt
        |
        v
[data/runs/<candidate_id>/]
```

## Layers

| Layer | Location | Responsibility |
| --- | --- | --- |
| MCP transport | `server.py` | Tool registration, stdio |
| xTB execution | `xtb/runner.py` | subprocess, logs |
| Parsing | `xtb/parser.py` | energy, dipole, charges |
| MAS agents | `agents/*.py` | specialist reviews |
| Scoring | `agents/scoring.py` | weighted final score |
| Reports | `reports/experiment.py` | 14-section markdown |
| Client LLM | `client/gemini_mas.py` | optional narrative (not in server) |

## Design principles

1. MCP server = calculation + rule-based evaluation tools.
2. LLM orchestration stays on the client unless using optional Gemini enrichment script.
3. Every result includes `raw_evidence` paths under `data/runs/`.
4. MVP input = pre-built `.xyz` only.

## Manifest format

```json
{
  "experiment_objective": "...",
  "xtb_settings": {"gfn": 2},
  "candidates": [
    {
      "candidate_id": "water",
      "xyz_path": "examples/water.xyz",
      "charge": 0,
      "notes": "optional",
      "safety_flags": []
    }
  ]
}
```

See `examples/candidates.json`.
