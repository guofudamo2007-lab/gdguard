from __future__ import annotations

from pathlib import Path

from gdguard.fs import iter_files
from gdguard.models import CheckResult, Severity, Status


def check_gdscript_files(project_root: Path, godot_available: bool) -> CheckResult:
    name = "script scan"
    unreadable: list[str] = []
    scanned = 0
    for path in iter_files(project_root, suffixes=(".gd",)):
        scanned += 1
        try:
            data = path.read_bytes()
        except OSError:
            unreadable.append(f"res://{path.relative_to(project_root).as_posix()}")
            continue
        if b"\x00" in data:
            unreadable.append(
                f"res://{path.relative_to(project_root).as_posix()} contains NUL bytes"
            )

    if unreadable:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="One or more GDScript files could not be read as text",
            details=unreadable,
            severity=Severity.ERROR,
            extra={"scanned_files": scanned},
        )

    if scanned == 0:
        message = "No GDScript files found"
    elif godot_available:
        message = f"Found {scanned} GDScript file(s); parse checks use Godot"
    else:
        message = f"Found {scanned} readable GDScript file(s)"

    return CheckResult(
        name=name,
        status=Status.PASS,
        message=message,
        extra={"scanned_files": scanned},
    )
