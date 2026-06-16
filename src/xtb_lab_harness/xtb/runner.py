from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess, run


class XtbNotFoundError(RuntimeError):
    """Raised when the xTB executable is not available on PATH."""


class XtbRunError(RuntimeError):
    """Raised when xTB exits with a non-zero status."""


@dataclass(frozen=True)
class XtbRunArtifacts:
    run_dir: Path
    input_xyz: Path
    stdout_log: Path
    stderr_log: Path
    optimized_xyz: Path | None
    returncode: int
    stdout_text: str
    stderr_text: str


def resolve_xtb_binary() -> str:
    binary = os.environ.get("XTB_BIN", "xtb")
    resolved = shutil.which(binary)
    if resolved is None:
        raise XtbNotFoundError(
            f"xTB executable not found: '{binary}'. "
            "Install xTB and ensure it is on PATH, or set XTB_BIN."
        )
    return resolved


def prepare_run_directory(base_dir: Path, candidate_id: str) -> Path:
    run_dir = base_dir / candidate_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def copy_input_xyz(source: Path, run_dir: Path, candidate_id: str) -> Path:
    destination = run_dir / f"{candidate_id}.xyz"
    shutil.copy2(source, destination)
    return destination


def run_xtb_optimization(
    input_xyz: Path,
    run_dir: Path,
    *,
    gfn: int = 2,
    charge: int | None = None,
    uhf: int | None = None,
    opt: bool = True,
    timeout_seconds: int | None = None,
) -> XtbRunArtifacts:
    """Run xTB on ``input_xyz`` inside ``run_dir`` and persist logs."""
    xtb_bin = resolve_xtb_binary()
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [xtb_bin, input_xyz.name, "--gfn", str(gfn)]
    if opt:
        cmd.append("--opt")
    if charge is not None:
        cmd.extend(["--chrg", str(charge)])
    if uhf is not None:
        cmd.extend(["--uhf", str(uhf)])

    stdout_log = run_dir / "stdout.log"
    stderr_log = run_dir / "stderr.log"

    completed: CompletedProcess[str] = run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    stdout_log.write_text(completed.stdout, encoding="utf-8")
    stderr_log.write_text(completed.stderr, encoding="utf-8")

    optimized_xyz = run_dir / "xtbopt.xyz"
    if not optimized_xyz.exists():
        optimized_xyz = None

    return XtbRunArtifacts(
        run_dir=run_dir,
        input_xyz=input_xyz,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        optimized_xyz=optimized_xyz,
        returncode=completed.returncode,
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
    )


def extract_warnings(stdout_text: str, stderr_text: str) -> list[str]:
    warnings: list[str] = []
    for line in (stdout_text + "\n" + stderr_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"\bwarn(ing)?\b", stripped, flags=re.IGNORECASE):
            warnings.append(stripped)
    return warnings
