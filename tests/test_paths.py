from __future__ import annotations

from pathlib import Path

from xtb_lab_harness.config.paths import resolve_xyz_path


def test_resolve_xyz_path_from_project_root() -> None:
    manifest = Path("examples/candidates.json").resolve()
    resolved = resolve_xyz_path("examples/water.xyz", manifest)
    assert Path(resolved).exists()
    assert resolved.endswith("water.xyz")


def test_resolve_xyz_path_absolute() -> None:
    manifest = Path("examples/candidates.json").resolve()
    water = Path("examples/water.xyz").resolve()
    assert resolve_xyz_path(str(water), manifest) == str(water)
