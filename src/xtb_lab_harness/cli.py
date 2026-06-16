from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from xtb_lab_harness.agents.orchestrator import Orchestrator, load_manifest
from xtb_lab_harness.client.gemini_mas import run_with_optional_gemini


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run xTB Lab Harness MAS pipeline (xTB + agent evaluation + report)",
    )
    parser.add_argument(
        "--manifest",
        "-m",
        required=True,
        help="Path to experiment manifest JSON",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/reports/latest_report.md",
        help="Output markdown report path",
    )
    parser.add_argument(
        "--reference",
        help="Reference candidate ID for relative energy in evidence table",
    )
    parser.add_argument(
        "--gemini",
        action="store_true",
        help="Enrich report sections 10–14 via Gemini API (requires GEMINI_API_KEY)",
    )
    parser.add_argument(
        "--gemini-model",
        default=None,
        help="Gemini model name (default: gemini-2.0-flash or GEMINI_MODEL env)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print ExperimentRunResult JSON to stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    if args.gemini:
        result = run_with_optional_gemini(
            str(manifest_path),
            output_path=args.output,
            reference_candidate_id=args.reference,
            use_gemini=True,
            model=args.gemini_model,
        )
    else:
        manifest = load_manifest(manifest_path)
        result = Orchestrator().run(
            manifest,
            report_output_path=args.output,
            reference_candidate_id=args.reference,
        )

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        print(f"Report written: {result.report_path}")
        ranked = [e for e in result.evaluations if e.rank is not None]
        if ranked:
            print(f"Top candidate: {ranked[0].candidate_id} (score={ranked[0].final_score:.3f})")
        else:
            print("No ranked candidates — check xTB installation and inputs.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
