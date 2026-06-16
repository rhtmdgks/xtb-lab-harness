# xTB Lab Harness

MCP server for xTB-based molecular calculation and LLM multi-agent experiment design.

> An MCP server that exposes xTB computational chemistry operations to LLM agents.

This repository is **not a web app**. It is a stdio MCP tool server that wraps the [xTB](https://github.com/grimme-lab/xtb) CLI, parses calculation output, and returns structured JSON for downstream MAS clients (Cursor, Claude Desktop, Gemini, custom runners).

## Architecture

```text
LLM / MAS Runtime (client)
        ↓ MCP (stdio)
xTB Lab Harness MCP Server
        ↓ subprocess
xTB CLI
        ↓
JSON + raw evidence logs
```

See [docs/architecture.md](docs/architecture.md) for details.

## MCP Tools

| Tool | Description |
| --- | --- |
| `calculate_candidate` | Optimize one `.xyz` and return parsed JSON |
| `calculate_candidate_batch` | Run multiple candidates |
| `generate_evidence_table` | Rank results and build a markdown evidence table |

Tool contracts: [docs/mcp-tools.md](docs/mcp-tools.md)

## Prerequisites

- Python 3.11+
- [xTB](https://github.com/grimme-lab/xtb) installed and on `PATH` (or set `XTB_BIN`)
- [uv](https://docs.astral.sh/uv/) recommended

## Setup

```bash
cp .env.example .env
uv sync
```

## Run MCP server (stdio)

```bash
uv run xtb-lab-harness
```

Or:

```bash
uv run python -m xtb_lab_harness.server
```

## Example (Python API, no MCP)

```python
from xtb_lab_harness.tools.optimize import calculate_candidate

result = calculate_candidate("water", "examples/water.xyz")
print(result.model_dump_json(indent=2))
```

## Project scope (MVP)

**In scope**

- xTB CLI wrapper + parser
- MCP tool registration
- JSON schemas + evidence logs under `data/runs/`
- Batch comparison + markdown evidence tables

**Out of scope (for now)**

- Next.js / web UI
- FastAPI
- Database / auth
- Gemini API inside the server (MAS stays on the client)

## Research context

Full system design: [Research Plan.md](Research%20Plan.md)

## License

MIT
