# Architecture

```text
[LLM / MAS Runtime]          MCP client (Cursor, Claude Desktop, Gemini, custom)
        |
        |  stdio MCP
        v
[xTB Lab Harness MCP Server]
  - calculate_candidate
  - calculate_candidate_batch
  - generate_evidence_table
        |
        |  subprocess
        v
[xTB CLI]
  - geometry optimization (--opt)
  - GFN-x (--gfn 2)
        |
        v
[data/runs/<candidate_id>/]
  - stdout.log / stderr.log
  - xtbopt.xyz
  - charges
```

## Design principles

1. **MCP server = pure calculation tool.** No Gemini API, no web UI, no DB.
2. **MAS lives on the client.** Orchestrator prompts and agent debate run outside this repo.
3. **Evidence preservation.** Every tool returns `raw_evidence` paths for auditability.
4. **MVP input = pre-built `.xyz`.** No SMILES→3D conversion in scope.

## Package layout

| Path | Role |
| --- | --- |
| `server.py` | MCP entrypoint (stdio) |
| `xtb/runner.py` | subprocess wrapper |
| `xtb/parser.py` | stdout / charges parsing |
| `xtb/schemas.py` | Pydantic JSON contracts |
| `tools/optimize.py` | single-candidate pipeline |
| `tools/analyze.py` | batch pipeline |
| `tools/compare.py` | evidence table + ranking |
| `agents/prompts.py` | optional MAS prompt snippets for clients |
| `reports/markdown.py` | persist markdown tables |
