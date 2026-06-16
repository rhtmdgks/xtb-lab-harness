from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.xtb.parser import (
    _parse_dipole_debye,
    _parse_total_energy_hartree,
    parse_charges_file,
    summarize_charges,
)


def test_parse_total_energy() -> None:
    text = "   TOTAL ENERGY              -5.0701048 Eh\n"
    assert _parse_total_energy_hartree(text) == -5.0701048


def test_parse_dipole() -> None:
    text = """
molecular dipole:
         total          1.85 (  0.00,  0.00,  1.85) debye
"""
    assert _parse_dipole_debye(text) == 1.85


def test_summarize_charges() -> None:
    summary = summarize_charges([0.31, -0.62, 0.31])
    assert summary.max_positive_charge == 0.31
    assert summary.max_negative_charge == -0.62


def test_parse_charges_file(tmp_path: Path) -> None:
    charges = tmp_path / "charges"
    charges.write_text(
        "    #   Z          covCN         q\n"
        "     1   8        1.000000    -0.6195\n"
        "     2   1        1.000000     0.3098\n",
        encoding="utf-8",
    )
    assert parse_charges_file(charges) == [-0.6195, 0.3098]
