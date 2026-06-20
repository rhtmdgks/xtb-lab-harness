from __future__ import annotations

from pathlib import Path


def resolve_xyz_path(xyz_path: str, manifest_path: Path) -> str:
    """Resolve candidate .xyz paths relative to cwd or project root."""
    candidate = Path(xyz_path).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve())

    if candidate.exists():
        return str(candidate.resolve())

    manifest_dir = manifest_path.parent.resolve()
    from_manifest = manifest_dir / candidate
    if from_manifest.exists():
        return str(from_manifest.resolve())

    from_project = manifest_dir.parent / candidate
    if from_project.exists():
        return str(from_project.resolve())

    return str(candidate.resolve())
