from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from gdguard.fs import iter_files
from gdguard.models import CheckResult, Severity, Status
from gdguard.process import run_command

DOTNET_TIMEOUT_SECONDS = 60


def check_dotnet(project_root: Path, csharp_detected: bool) -> CheckResult:
    name = "dotnet build"

    def fail(message, details=None, extra=None):
        return CheckResult(
            name, Status.FAIL, message, details or [], Severity.ERROR, extra or {"executed": False}
        )

    if not csharp_detected:
        return fail("Requested build: no C# project files detected")
    dotnet = shutil.which("dotnet")
    if not dotnet:
        return fail("Requested build: dotnet executable not found")
    project_file = _find_build_target(project_root)
    if project_file is None:
        return fail("Requested build: no .csproj/.sln to build")
    command = [dotnet, "build", str(project_file), "--nologo", "-v", "q"]
    extra = {
        "command": command,
        "target": str(project_file),
        "executed": False,
        "timeout_seconds": DOTNET_TIMEOUT_SECONDS,
    }
    try:
        completed = run_command(command, cwd=project_root, timeout=DOTNET_TIMEOUT_SECONDS)
    except (TimeoutError, subprocess.TimeoutExpired):
        extra["executed"] = True
        return fail(f"dotnet build timed out after {DOTNET_TIMEOUT_SECONDS}s", extra=extra)
    except OSError as exc:
        return fail("dotnet could not be started", [str(exc)], extra)
    extra.update(returncode=completed.returncode, executed=True)
    combined = (completed.stdout or "") + "\n" + (completed.stderr or "")
    errors = [
        line.strip()
        for line in combined.splitlines()
        if re.search(r"\berror(?:\s+[A-Z]+\d+)?\s*:", line, re.IGNORECASE)
    ]
    if completed.returncode != 0 or errors:
        return fail(
            "dotnet build failed",
            errors[:8] or [f"dotnet exited with code {completed.returncode}"],
            extra,
        )
    return CheckResult(name, Status.PASS, "Selected dotnet build target succeeded", extra=extra)


def _find_build_target(project_root: Path) -> Path | None:
    solutions = sorted(iter_files(project_root, suffixes=(".sln",)))
    projects = sorted(iter_files(project_root, suffixes=(".csproj",)))
    targets = solutions or projects
    return targets[0] if targets else None
