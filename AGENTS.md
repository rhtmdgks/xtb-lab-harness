# xTB Lab Harness

MCP tool server for xTB computational chemistry. Not a web app.

## Scope

- **In scope:** xTB CLI wrapper, output parser, MCP tools (`calculate_candidate`, `calculate_candidate_batch`, `generate_evidence_table`), JSON schemas, evidence logs under `data/runs/`.
- **Out of scope (MVP):** Next.js, FastAPI, DB, auth, Gemini API inside the server. MAS orchestration lives on the MCP **client** side.

## Layout

```text
src/xtb_lab_harness/   Python package
examples/              Sample .xyz inputs
data/runs/             Per-candidate xTB run logs (gitignored contents)
docs/                  Architecture and tool contracts
```

## Conventions

- Return structured Pydantic models / dicts from tools; preserve `raw_evidence` paths.
- xTB is invoked via subprocess in `xtb/runner.py`; parsing in `xtb/parser.py`.
- MCP transport: stdio (`python -m xtb_lab_harness.server` or project script).
