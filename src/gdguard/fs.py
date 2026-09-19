from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".godot",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
}


def iter_files(root: Path, suffixes: tuple[str, ...] | None = None) -> Iterator[Path]:
    """Walk a Godot project without leaving the target tree or scanning Git internals."""
    root = root.resolve()
    wanted = tuple(suffix.lower() for suffix in suffixes) if suffixes else None
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            path = current / filename
            if wanted is not None and path.suffix.lower() not in wanted:
                continue
            yield path
