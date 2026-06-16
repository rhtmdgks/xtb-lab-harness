from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """Load .env then .env.local (local overrides)."""
    root = Path.cwd()
    load_dotenv(root / ".env", override=False)
    load_dotenv(root / ".env.local", override=True)
