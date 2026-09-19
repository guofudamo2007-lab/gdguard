from __future__ import annotations

import os
import shutil
from pathlib import Path

from gdguard.models import CheckResult, GodotBinary, Severity, Status
from gdguard.process import run_command

CANDIDATES = ("godot", "godot4", "godot.exe", "godot4.exe")
HEADLESS_TIMEOUT_SECONDS = 30


def discover_godot(explicit: str | None = None) -> GodotBinary | None:
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists() and path.is_file():
            return GodotBinary(path=path, version=_query_version(path))
        found = shutil.which(explicit)
        if found:
            resolved = Path(found)
            return GodotBinary(path=resolved, version=_query_version(resolved))
        return None

    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            resolved = Path(found)
            return GodotBinary(path=resolved, version=_query_version(resolved))
    return None


def _query_version(path: Path) -> str | None:
    try:
        completed = run_command([str(path), "--version"], timeout=8, env=_safe_env())
    except (OSError, TimeoutError):
        return None
    output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip().splitlines()
    if not output:
        return None
    return output[0].strip() or None


def _safe_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("GODOT_SILENCE_ROOT_WARNING", "1")
    return env


def run_headless_check(project_root: Path, binary: GodotBinary | None) -> CheckResult:
    name = "Godot headless check"
    if binary is None:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- Godot executable not found",
        )

    command = [
        str(binary.path),
        "--headless",
        "--quit-after",
        "1",
        "--path",
        str(project_root),
    ]
    try:
        completed = run_command(
            command,
            timeout=HEADLESS_TIMEOUT_SECONDS,
            env=_safe_env(),
        )
    except TimeoutError:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"Godot headless validation timed out after {HEADLESS_TIMEOUT_SECONDS}s",
            details=[f"command: {' '.join(command)}"],
            severity=Severity.ERROR,
        )
    except OSError as exc:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- Godot executable could not be started",
            details=[str(exc)],
        )

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    combined = "\n".join(part for part in (stdout, stderr) if part)
    errors = _extract_godot_errors(combined)
    extra = {
        "returncode": completed.returncode,
        "executable": str(binary.path),
        "version": binary.version,
    }
    if completed.returncode != 0 or errors:
        details = errors[:8] or [f"Godot exited with code {completed.returncode}"]
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="Godot headless validation failed",
            details=details,
            severity=Severity.ERROR,
            extra=extra,
        )
    return CheckResult(
        name=name,
        status=Status.PASS,
        message="Godot loaded the project in headless mode",
        details=[f"Godot {binary.version}"] if binary.version else [],
        extra=extra,
    )


def _extract_godot_errors(output: str) -> list[str]:
    interesting: list[str] = []
    markers = ("ERROR:", "SCRIPT ERROR:", "Parse Error", "Failed to load")
    for line in output.splitlines():
        stripped = line.strip()
        if any(marker.lower() in stripped.lower() for marker in markers):
            interesting.append(stripped)
    return interesting
