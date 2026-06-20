# MCP Tools

## Calculation tools

### `calculate_candidate`

Run xTB geometry optimization and parse properties for one `.xyz` file.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `candidate_id` | string | required | Label for logs and JSON |
| `xyz_path` | string | required | Path to input `.xyz` |
| `gfn` | int | `2` | GFN level |
| `charge` | int | null | `--chrg` |
| `uhf` | int | null | `--uhf` |

### `calculate_candidate_batch`

```json
[
  {"candidate_id": "water", "xyz_path": "examples/water.xyz", "gfn": 2, "charge": 0}
]
```

### `generate_evidence_table`

| Argument | Description |
| --- | --- |
| `results` | `CandidateResult` dicts |
| `reference_candidate_id` | ΔE reference |
| `save_report_path` | Optional markdown path |

## MAS tools

### `evaluate_candidates`

Run specialist agents on existing xTB JSON (no re-calculation).

| Argument | Description |
| --- | --- |
| `experiment_objective` | Natural language objective |
| `candidate_specs` | Manifest candidate entries |
| `xtb_results` | Output from `calculate_candidate_batch` |

Returns scored `CandidateEvaluation` list with agent reviews.

### `run_experiment_pipeline`

End-to-end from manifest JSON:

```json
{
  "manifest_path": "examples/candidates.json",
  "report_output_path": "data/reports/latest_report.md",
  "reference_candidate_id": "water"
}
```

### `generate_experiment_report`

Build standardized experiment report (`report-harness-v1.2`, 한글 우선 표 헤더). See `docs/report-format.md` for the single-source / no-duplication spec.

## CLI equivalent

```bash
uv run xtb-lab-run -m examples/candidates.json -o data/reports/latest_report.md --json
```

## Cursor / Claude Desktop (stdio)

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
