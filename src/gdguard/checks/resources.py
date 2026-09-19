from __future__ import annotations

import re
from pathlib import Path

from gdguard.fs import iter_files
from gdguard.models import CheckResult, Severity, Status

_RES_PATH_RE = re.compile(r'"res://([^"]+)"')
_UNCERTAIN_CHARS = set("${}%")
_SCRIPT_SUFFIXES = {".gd", ".cs"}


def check_resource_references(project_root: Path) -> list[CheckResult]:
    missing_resources: list[str] = []
    missing_scripts: list[str] = []
    scanned = 0

    for source in iter_files(project_root, suffixes=(".tscn", ".tres")):
        scanned += 1
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for reference in _extract_res_paths(text):
            if not _is_certain_path(reference):
                continue
            target = _resolve_res_path(project_root, reference)
            if target.exists():
                continue
            rel_source = _res_uri(source, project_root)
            item = f"scene:\n{rel_source}\n\nreference:\nres://{reference}"
            if Path(reference).suffix.lower() in _SCRIPT_SUFFIXES:
                missing_scripts.append(item)
            else:
                missing_resources.append(item)

    results = [
        _build_result(
            name="scene resources",
            missing=missing_resources,
            scanned=scanned,
            kind="resource",
        ),
        _build_result(
            name="script references",
            missing=missing_scripts,
            scanned=scanned,
            kind="script",
        ),
    ]
    return results


def _build_result(name: str, missing: list[str], scanned: int, kind: str) -> CheckResult:
    if missing:
        label = "Missing script reference" if kind == "script" else "Missing resource"
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"ERROR\n{label}",
            details=missing,
            severity=Severity.ERROR,
            extra={"missing": len(missing), "scanned_files": scanned},
        )
    return CheckResult(
        name=name,
        status=Status.PASS,
        message=f"No missing {kind} references found",
        extra={"scanned_files": scanned},
    )


def _extract_res_paths(text: str) -> list[str]:
    return [match.group(1) for match in _RES_PATH_RE.finditer(text)]


def _is_certain_path(reference: str) -> bool:
    if not reference or reference.endswith("/"):
        return False
    if any(char in reference for char in _UNCERTAIN_CHARS):
        return False
    if "\\" in reference or "://" in reference:
        return False
    if reference.startswith("."):
        return False
    return True


def _resolve_res_path(project_root: Path, reference: str) -> Path:
    return project_root.joinpath(*Path(reference).parts)


def _res_uri(path: Path, project_root: Path) -> str:
    relative = path.relative_to(project_root).as_posix()
    return f"res://{relative}"
