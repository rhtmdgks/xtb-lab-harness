# xTB Lab Harness

MCP server for xTB-based molecular calculation and LLM multi-agent experiment design.

> An MCP server that exposes xTB computational chemistry operations to LLM agents.

## What this is

```text
LLM / MAS Runtime (client)
        ↓ MCP stdio
xTB Lab Harness MCP Server
        ↓ subprocess
xTB CLI → JSON + evidence logs
```

The server also includes a **rule-based MAS layer** (specialist agents, scoring, 14-section report) runnable via CLI without any LLM.

## Quick start

```bash
cp .env.example .env
uv sync

# Full pipeline from manifest (xTB required on PATH)
uv run xtb-lab-run -m examples/candidates.json -o data/reports/latest_report.md

# MCP stdio server
uv run xtb-lab-harness
```

## MCP Tools

| Tool | Description |
| --- | --- |
| `calculate_candidate` | One `.xyz` → xTB `--opt` → JSON |
| `calculate_candidate_batch` | Batch xTB calculations |
| `generate_evidence_table` | Rank by energy + markdown table |
| `evaluate_candidates` | MAS agent reviews on xTB JSON |
| `run_experiment_pipeline` | Manifest → xTB → MAS → full report |
| `generate_experiment_report` | Build 14-section report from evaluations |

Details: [docs/mcp-tools.md](docs/mcp-tools.md)

## MAS Agents

| Agent | Role |
| --- | --- |
| Orchestrator | Pipeline coordination |
| Hypothesis | Objective → testable hypothesis |
| Candidate Material | `.xyz` screening + suitability |
| Electrostatic | Charges + dipole interpretation |
| vdW / Dispersion | Non-covalent tendency (not high-precision) |
| Structural Stability | Optimization + energy |
| Safety | 1st-pass safety filter (not SDS) |
| Variable Control | IV/DV/CV draft |
| Critic | Evidence + overclaim check |

Scoring weights match [Research Plan.md](Research%20Plan.md) section 13.

## Examples

- `examples/candidates.json` — 7 molecules, polar/nonpolar solvent comparison
- `examples/*.xyz` — water, ethanol, methanol, acetone, ammonia, methane, urea

## Optional Gemini client

MAS narrative enrichment (orchestrator plan, LLM debate, report synthesis):

```bash
uv sync --extra llm
# .env.local 에 GEMINI_API_KEY 설정
uv run xtb-lab-check-gemini
# 또는
uv run xtb-lab-run --check-gemini

uv run xtb-lab-run -m examples/candidates.json --gemini
```

## Prerequisites

- Python 3.11+
- [xTB](https://github.com/grimme-lab/xtb) on `PATH` (or `XTB_BIN`)
- [uv](https://docs.astral.sh/uv/) recommended

## Project layout

```text
src/xtb_lab_harness/
  server.py          MCP entrypoint
  cli.py             xtb-lab-run pipeline CLI
  xtb/               runner, parser, schemas
  tools/             xTB + evaluate + report tools
  agents/            MAS specialists + orchestrator
  reports/           evidence + experiment report
  client/            optional Gemini enrichment
examples/            xyz + candidates.json manifest
data/runs/           xTB logs (gitignored contents)
data/reports/        generated reports
docs/
```

## Out of scope (MVP)

- Next.js / web UI
- FastAPI / DB / auth
- Gemini API inside MCP server (client-only)
- SMILES → 3D conversion

## Research context

[Research Plan.md](Research%20Plan.md)

## License

MIT
