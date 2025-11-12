"""Utilities for exporting raw source code of the planner application."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


def iter_source_files() -> Iterator[Path]:
    """Yield Python source files that make up the planner application."""

    yield PROJECT_ROOT / "main.py"

    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        if path.name == "__pycache__":
            continue
        yield path


def dump_raw_code() -> str:
    """Return the concatenated contents of all source files."""

    contents = []
    for path in iter_source_files():
        if path.exists():
            contents.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(contents)
