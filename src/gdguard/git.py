from __future__ import annotations

from pathlib import Path

from gdguard.models import GitInfo
from gdguard.process import run_command


def inspect_git(project_root: Path) -> GitInfo | None:
    git_dir = _find_git_dir(project_root)
    if git_dir is None:
        return None
    branch = _run_git(project_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    status = _run_git(project_root, ["status", "--porcelain"])
    dirty = None if status is None else bool(status.strip())
    return GitInfo(branch=branch, dirty=dirty)


def _find_git_dir(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        git_dir = candidate / ".git"
        if git_dir.exists():
            return git_dir
    return None


def _run_git(cwd: Path, args: list[str]) -> str | None:
    try:
        completed = run_command(["git", *args], cwd=cwd, timeout=8)
    except (OSError, TimeoutError):
        return None
    if completed.returncode != 0:
        return None
    return (completed.stdout or "").strip() or None
