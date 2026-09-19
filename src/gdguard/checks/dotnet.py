from __future__ import annotations

import shutil
from pathlib import Path

from gdguard.fs import iter_files
from gdguard.models import CheckResult, Severity, Status
from gdguard.process import run_command

DOTNET_TIMEOUT_SECONDS = 60


def check_dotnet(project_root: Path, csharp_detected: bool) -> CheckResult:
    name = "dotnet build"
    if not csharp_detected:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- no C# project files detected",
        )

    dotnet = shutil.which("dotnet")
    if not dotnet:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- dotnet executable not found",
            details=["C# project detected"],
        )

    project_file = _find_build_target(project_root)
    if project_file is None:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- C# files found but no .csproj/.sln to build",
            details=["C# project detected"],
        )

    command = [dotnet, "build", str(project_file), "--nologo", "-v", "q"]
    try:
        completed = run_command(command, timeout=DOTNET_TIMEOUT_SECONDS)
    except TimeoutError:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message=f"dotnet build timed out after {DOTNET_TIMEOUT_SECONDS}s",
            severity=Severity.ERROR,
        )
    except OSError as exc:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- dotnet could not be started",
            details=[str(exc)],
        )

    if completed.returncode != 0:
        combined = f"{completed.stderr or ''}\n{completed.stdout or ''}"
        details = [line.strip() for line in combined.splitlines() if line.strip()]
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="dotnet build failed",
            details=details[:8] or [f"dotnet exited with code {completed.returncode}"],
            severity=Severity.ERROR,
        )
    return CheckResult(
        name=name,
        status=Status.PASS,
        message="dotnet build succeeded",
        details=["C# project detected"],
    )


def _find_build_target(project_root: Path) -> Path | None:
    solutions = list(iter_files(project_root, suffixes=(".sln",)))
    if solutions:
        return solutions[0]
    projects = list(iter_files(project_root, suffixes=(".csproj",)))
    if projects:
        return projects[0]
    return None
