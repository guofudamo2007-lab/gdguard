from __future__ import annotations

import re
from pathlib import Path

from gdguard.errors import GDGuardError
from gdguard.fs import iter_files, validate_local_file
from gdguard.models import ProjectInfo

PROJECT_FILE = "project.godot"
_CONFIG_VERSION_RE = re.compile(r"^config_version\s*=\s*(\d+)\s*$", re.MULTILINE)
_CONFIG_NAME_RE = re.compile(r'^config/name\s*=\s*"([^"]*)"\s*$', re.MULTILINE)
_FEATURE_RE = re.compile(r"^config/features\s*=\s*PackedStringArray\((.*)\)\s*$", re.MULTILINE)


def resolve_project_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.exists():
        raise GDGuardError(f"Path does not exist: {path}")
    if root.is_file():
        root = root.parent
    if not (root / PROJECT_FILE).is_file():
        raise GDGuardError(
            "No Godot project found.\nExpected project.godot in the target directory."
        )
    return root


def load_project_info(root: Path) -> ProjectInfo:
    project_file = root / PROJECT_FILE
    try:
        validate_local_file(root, project_file)
        text = project_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return ProjectInfo(
            root=root,
            name=root.name,
            godot_version="unknown",
            config_version=None,
            csharp_detected=_detect_csharp(root),
            readable=False,
            damaged=True,
        )

    damaged = _looks_damaged(text)
    name = _extract_name(text) or root.name
    config_version = _extract_config_version(text)
    godot_version = _extract_godot_version(text)
    return ProjectInfo(
        root=root,
        name=name,
        godot_version=godot_version,
        config_version=config_version,
        csharp_detected=_detect_csharp(root),
        readable=True,
        damaged=damaged,
    )


def _looks_damaged(text: str) -> bool:
    if not text.strip():
        return True
    if not _CONFIG_VERSION_RE.search(text) or "\x00" in text:
        return True
    if "[" not in text:
        return True
    return False


def _extract_name(text: str) -> str | None:
    match = _CONFIG_NAME_RE.search(text)
    return match.group(1) if match else None


def _extract_config_version(text: str) -> int | None:
    match = _CONFIG_VERSION_RE.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _extract_godot_version(text: str) -> str:
    match = _FEATURE_RE.search(text)
    if not match:
        return "unknown"
    features = [part.strip().strip('"') for part in match.group(1).split(",") if part.strip()]
    for feature in features:
        if re.fullmatch(r"4\.\d+", feature) or re.fullmatch(r"3\.\d+", feature):
            return feature
    return "unknown"


def _detect_csharp(root: Path) -> bool:
    return any(iter_files(root, suffixes=(".csproj", ".sln", ".cs")))
