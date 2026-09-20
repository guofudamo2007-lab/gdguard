from __future__ import annotations

from pathlib import Path

from gdguard.checks.dotnet import check_dotnet
from gdguard.checks.project import check_project_file
from gdguard.checks.resources import check_resource_references
from gdguard.checks.scripts import check_gdscript_files
from gdguard.checks.secrets import check_sensitive_files
from gdguard.godot import discover_godot, run_headless_check, run_import_check
from gdguard.models import CheckResult, ScanReport, Severity, Status
from gdguard.project import load_project_info, resolve_project_root


def scan_project(
    path: Path,
    godot_path: str | None = None,
    *,
    import_project: bool = False,
    headless: bool = False,
    dotnet_build: bool = False,
) -> ScanReport:
    root = resolve_project_root(path)
    requested = [
        name
        for name, enabled in (
            ("project import", import_project),
            ("Godot headless check", headless),
            ("dotnet build", dotnet_build),
        )
        if enabled
    ]
    try:
        project = load_project_info(root)
    except OSError as exc:
        return ScanReport(
            None,
            None,
            None,
            [CheckResult("project files", Status.FAIL, str(exc), severity=Severity.ERROR)],
            dynamic_requested=requested,
        )
    binary = discover_godot(godot_path) if import_project or headless else None

    def static_check(callback, *args):
        try:
            return callback(*args)
        except OSError as exc:
            return CheckResult(callback.__name__, Status.FAIL, str(exc), severity=Severity.ERROR)

    checks = [
        check_project_file(project),
        static_check(check_gdscript_files, root),
        *check_resource_references(root),
        run_import_check(root, binary)
        if import_project
        else _not_requested("project import", "--import"),
        run_headless_check(root, binary)
        if headless
        else _not_requested("Godot headless check", "--headless"),
        static_check(check_sensitive_files, root),
        static_check(check_dotnet, root, project.csharp_detected)
        if dotnet_build
        else _not_requested("dotnet build", "--dotnet-build"),
    ]
    return ScanReport(
        project=project,
        git=None,
        godot_executable=str(binary.path) if binary else None,
        checks=checks,
        dynamic_requested=requested,
    )


def _not_requested(name: str, flag: str) -> CheckResult:
    return CheckResult(
        name,
        Status.SKIPPED,
        f"Not requested; enable {flag} only for a trusted project",
    )
