from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".godot",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
}


def iter_files(root: Path, suffixes: tuple[str, ...] | None = None) -> Iterator[Path]:
    """Stable traversal; fail visibly on inaccessible directories and links."""
    root = root.resolve()
    wanted = tuple(suffix.lower() for suffix in suffixes) if suffixes else None

    def onerror(error: OSError) -> None:
        raise error

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False, onerror=onerror):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        current = Path(dirpath)
        for name in dirnames:
            validate_local_file(root, current / name, directory=True)
        for filename in sorted(filenames):
            path = current / filename
            if wanted is not None and path.suffix.lower() not in wanted:
                continue
            validate_local_file(root, path)
            yield path


def validate_local_file(root: Path, path: Path, *, directory: bool = False) -> None:
    """Reject links/junctions, including internal links, before reading."""
    root = root.resolve()
    try:
        relative = path.absolute().relative_to(root)
    except ValueError as exc:
        raise OSError(f"{path}: outside project root") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink() or (
            getattr(current.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise OSError(f"{path}: symbolic link/junction not scanned")
        if not current.resolve().is_relative_to(root):
            raise OSError(f"{path}: outside project root")
    if not directory and not path.is_file():
        raise OSError(f"{path}: not a regular file")
