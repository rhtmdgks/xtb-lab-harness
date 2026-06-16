# MCP Tools

## `calculate_candidate`

Run xTB geometry optimization and parse properties for one `.xyz` file.

| Argument | Type | Required | Description |
| --- | --- | --- | --- |
| `candidate_id` | string | yes | Label for logs and JSON output |
| `xyz_path` | string | yes | Absolute or repo-relative path to input `.xyz` |
| `gfn` | int | no | GFN level (default `2`) |
| `charge` | int | no | Molecular charge (`--chrg`) |
| `uhf` | int | no | UHF (`--uhf`) |

## `calculate_candidate_batch`

Same as above for multiple candidates.

```json
[
  {"candidate_id": "water", "xyz_path": "examples/water.xyz"},
  {"candidate_id": "ethanol", "xyz_path": "examples/ethanol.xyz", "charge": 0}
]
```

## `generate_evidence_table`

Rank successful candidates by total energy and emit a markdown table.

| Argument | Type | Required | Description |
| --- | --- | --- | --- |
| `results` | array | yes | List of `CandidateResult` dicts from prior tool calls |
| `reference_candidate_id` | string | no | Energy reference for ΔE column |
| `save_report_path` | string | no | Write markdown to `data/reports/...` |

## Cursor / Claude Desktop config (stdio)

```json
{
  "mcpServers": {
    "xtb-lab-harness": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/xtb-lab-harness",
        "xtb-lab-harness"
      ],
      "env": {
        "XTB_DATA_DIR": "/absolute/path/to/xtb-lab-harness/data"
      }
    }
  }
}
```

Alternative without `uv`:

```json
{
  "command": "python",
  "args": ["-m", "xtb_lab_harness.server"],
  "cwd": "/absolute/path/to/xtb-lab-harness",
  "env": { "PYTHONPATH": "src" }
}
```
