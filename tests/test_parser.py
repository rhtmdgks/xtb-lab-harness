from __future__ import annotations

from pathlib import Path

import pytest

from xtb_lab_harness.xtb.parser import (
    _parse_dipole_debye,
    _parse_total_energy_hartree,
    parse_charges_file,
    parse_charges_from_text,
    parse_xtb_artifacts,
    summarize_charges,
)
from xtb_lab_harness.xtb.runner import XtbRunArtifacts

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_total_energy_legacy() -> None:
    text = "   TOTAL ENERGY              -5.0701048 Eh\n"
    assert _parse_total_energy_hartree(text) == -5.0701048


def test_parse_total_energy_uses_last_match() -> None:
    text = """
         :: total energy              -5.070222286727 Eh    ::
          | TOTAL ENERGY               -5.070544351073 Eh   |
    """
    assert _parse_total_energy_hartree(text) == -5.070544351073


def test_parse_dipole_legacy() -> None:
    text = """
molecular dipole:
         total          1.85 (  0.00,  0.00,  1.85) debye
"""
    assert _parse_dipole_debye(text) == 1.85


def test_parse_dipole_modern_xtb() -> None:
    text = (FIXTURES / "water_stdout_tail.txt").read_text(encoding="utf-8")
    assert _parse_dipole_debye(text) == pytest.approx(2.216)


def test_parse_charges_single_column_file(tmp_path: Path) -> None:
    charges = tmp_path / "charges"
    charges.write_text(
        "   -0.56476049\n    0.28238024\n    0.28238024\n",
        encoding="utf-8",
    )
    parsed = parse_charges_file(charges)
    assert parsed == pytest.approx([-0.56476049, 0.28238024, 0.28238024])


def test_parse_charges_tabular_file(tmp_path: Path) -> None:
    charges = tmp_path / "charges"
    charges.write_text(
        "    #   Z          covCN         q\n"
        "     1   8        1.000000    -0.6195\n"
        "     2   1        1.000000     0.3098\n",
        encoding="utf-8",
    )
    assert parse_charges_file(charges) == pytest.approx([-0.6195, 0.3098])


def test_parse_charges_from_stdout_table() -> None:
    text = (FIXTURES / "water_stdout_tail.txt").read_text(encoding="utf-8")
    assert parse_charges_from_text(text) == pytest.approx([-0.565, 0.282, 0.282], rel=1e-3)


def test_summarize_charges() -> None:
    summary = summarize_charges([0.31, -0.62, 0.31])
    assert summary.max_positive_charge == 0.31
    assert summary.max_negative_charge == -0.62
    assert summary.charge_distribution_note == "polarized structure"


def test_parse_xtb_artifacts_integration(tmp_path: Path) -> None:
    run_dir = tmp_path / "water"
    run_dir.mkdir()
    stdout = (FIXTURES / "water_stdout_tail.txt").read_text(encoding="utf-8")
    full_stdout = (
        "GEOMETRY OPTIMIZATION CONVERGED\n"
        "         :: total energy              -5.070222286727 Eh    ::\n"
        + stdout
    )
    stdout_log = run_dir / "stdout.log"
    stderr_log = run_dir / "stderr.log"
    stdout_log.write_text(full_stdout, encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    (run_dir / "charges").write_text(
        "   -0.56476049\n    0.28238024\n    0.28238024\n",
        encoding="utf-8",
    )
    opt_xyz = run_dir / "xtbopt.xyz"
    opt_xyz.write_text("placeholder\n", encoding="utf-8")
    input_xyz = run_dir / "water.xyz"
    input_xyz.write_text("placeholder\n", encoding="utf-8")

    artifacts = XtbRunArtifacts(
        run_dir=run_dir,
        input_xyz=input_xyz,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        optimized_xyz=opt_xyz,
        returncode=0,
        stdout_text=full_stdout,
        stderr_text="",
    )
    result = parse_xtb_artifacts("water", artifacts)
    assert result.calculation_status.value == "success"
    assert result.geometry_optimized is True
    assert result.total_energy_hartree == pytest.approx(-5.070544351073)
    assert result.dipole_moment_debye == pytest.approx(2.216)
    assert result.charge_summary.max_positive_charge == pytest.approx(0.28238024)
    assert result.charge_summary.max_negative_charge == pytest.approx(-0.56476049)
