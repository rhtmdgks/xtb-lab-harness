from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from xtb_lab_harness.client.gemini_health import check_gemini, format_health_report
from xtb_lab_harness.client.gemini_mas import run_mas_pipeline
from xtb_lab_harness.config.env import load_project_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run xTB Lab Harness MAS pipeline (LLM plan → parallel agents → debate → report)",
    )
    parser.add_argument(
        "--check-gemini",
        action="store_true",
        help="Verify GEMINI_API_KEY / GOOGLE_API_KEY and test a minimal API call",
    )
    parser.add_argument(
        "--manifest",
        "-m",
        help="Path to experiment manifest JSON",
    )
    parser.add_argument(
        "--command",
        "-c",
        help="Natural language user command (LLM orchestrator parses and assigns agents)",
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
        help="Enable LLM orchestrator + debate + full report synthesis (needs GEMINI_API_KEY)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM even if API key present (rule-based debate only)",
    )
    parser.add_argument(
        "--gemini-model",
        default=None,
        help="Gemini model name (default: gemini-2.0-flash or GEMINI_MODEL env)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON to stdout (ExperimentRunResult or Gemini health result)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_project_env()
    args = build_parser().parse_args(argv)

    if args.check_gemini:
        result = check_gemini(model=args.gemini_model)
        print(format_health_report(result))
        if args.json:
            print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
        return 0 if result.status == "ok" else 1

    if not args.manifest:
        print("Error: --manifest / -m is required (unless using --check-gemini).", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    use_llm = args.gemini and not args.no_llm
    if args.gemini_model:
        import os

        os.environ["GEMINI_MODEL"] = args.gemini_model

    if use_llm or args.command:
        result = run_mas_pipeline(
            str(manifest_path),
            user_command=args.command,
            output_path=args.output,
            reference_candidate_id=args.reference,
            use_llm=use_llm or bool(args.command),
        )
    else:
        from xtb_lab_harness.agents.orchestrator import Orchestrator, load_manifest

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
        if result.task_plan:
            print(f"Assigned agents: {', '.join(result.task_plan.assigned_agents)}")
        print(f"Debates: {len(result.debates)}")
        ranked = sorted(
            [e for e in result.evaluations if e.rank is not None],
            key=lambda e: e.rank or 999,
        )
        if ranked:
            print(f"Top candidate: {ranked[0].candidate_id} (score={ranked[0].final_score:.3f})")
        else:
            print("No ranked candidates — check xTB installation and inputs.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
