from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from gdguard.models import CheckResult, GodotBinary, Severity, Status
from gdguard.process import run_command

CANDIDATES = ("godot", "godot4", "godot.exe", "godot4.exe")
HEADLESS_TIMEOUT_SECONDS = 30
IMPORT_TIMEOUT_SECONDS = 60


def discover_godot(explicit: str | None = None) -> GodotBinary | None:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            path = path.resolve()
            return GodotBinary(path, _query_version(path))
        found = shutil.which(explicit)
        if found:
            path = Path(found).resolve()
            return GodotBinary(path, _query_version(path))
        return None
    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            path = Path(found).resolve()
            return GodotBinary(path, _query_version(path))
    return None


def _query_version(path: Path) -> str | None:
    try:
        completed = run_command([str(path), "--version"], timeout=8, env=_safe_env())
    except (OSError, TimeoutError, subprocess.TimeoutExpired):
        return None
    if completed.returncode:
        return None
    output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip().splitlines()
    return output[0].strip() if output else None


def _safe_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("GODOT_SILENCE_ROOT_WARNING", "1")
    return env


def run_import_check(project_root: Path, binary: GodotBinary | None) -> CheckResult:
    return _run_check(
        project_root,
        binary,
        "project import",
        ["--headless", "--editor", "--import"],
        IMPORT_TIMEOUT_SECONDS,
        "Godot editor import completed; not full scene/script or gameplay validation",
    )


def run_headless_check(project_root: Path, binary: GodotBinary | None) -> CheckResult:
    return _run_check(
        project_root,
        binary,
        "Godot headless check",
        ["--headless", "--quit-after", "1"],
        HEADLESS_TIMEOUT_SECONDS,
        "Main-scene smoke command completed for one iteration; not all scenes/scripts",
    )


def _run_check(root, binary, name, flags, timeout, success):
    if binary is None:
        return CheckResult(
            name,
            Status.FAIL,
            "Requested check: Godot executable not found",
            severity=Severity.ERROR,
            extra={"executed": False},
        )
    if not re.match(r"^4\.\d+(?:\.|$)", binary.version or ""):
        return CheckResult(
            name,
            Status.FAIL,
            "Requested check requires an identifiable Godot 4 editor",
            severity=Severity.ERROR,
            extra={"executed": False, "version": binary.version},
        )
    command = [str(binary.path), *flags, "--path", str(root)]
    extra = {
        "command": command,
        "executable": str(binary.path),
        "version": binary.version,
        "timeout_seconds": timeout,
        "executed": False,
    }
    try:
        completed = run_command(command, cwd=root, timeout=timeout, env=_safe_env())
    except (TimeoutError, subprocess.TimeoutExpired):
        extra["executed"] = True
        return CheckResult(
            name,
            Status.FAIL,
            f"{name} timed out after {timeout}s",
            severity=Severity.ERROR,
            extra=extra,
        )
    except OSError as exc:
        return CheckResult(
            name, Status.FAIL, f"{name} could not be started", [str(exc)], Severity.ERROR, extra
        )
    extra.update(returncode=completed.returncode, executed=True)
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    errors = _extract_godot_errors(output)
    if completed.returncode != 0 or errors:
        return CheckResult(
            name,
            Status.FAIL,
            f"{name} failed",
            errors[:8] or [f"Godot exited with code {completed.returncode}"],
            Severity.ERROR,
            extra,
        )
    return CheckResult(name, Status.PASS, success, extra=extra)


def _extract_godot_errors(output: str) -> list[str]:
    markers = ("ERROR:", "SCRIPT ERROR:", "Parse Error", "Failed to load")
    return [
        line.strip()
        for line in output.splitlines()
        if any(marker.lower() in line.lower() for marker in markers)
    ]
