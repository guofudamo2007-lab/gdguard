from __future__ import annotations

from pathlib import Path

from gdguard.checks.dotnet import check_dotnet
from gdguard.checks.project import check_project_file
from gdguard.checks.resources import check_resource_references
from gdguard.checks.scripts import check_gdscript_files
from gdguard.checks.secrets import check_sensitive_files
from gdguard.git import inspect_git
from gdguard.godot import discover_godot, run_headless_check
from gdguard.models import CheckResult, GodotBinary, ProjectInfo, ScanReport, Status
from gdguard.project import load_project_info, resolve_project_root


def scan_project(path: Path, godot_path: str | None = None) -> ScanReport:
    root = resolve_project_root(path)
    project = load_project_info(root)
    binary = discover_godot(godot_path)
    project = _with_runtime_version(project, binary)
    checks: list[CheckResult] = [
        check_project_file(project),
        check_gdscript_files(root, godot_available=binary is not None),
        *check_resource_references(root),
        _project_import_check(binary),
        run_headless_check(root, binary),
        check_sensitive_files(root),
        check_dotnet(root, project.csharp_detected),
    ]
    return ScanReport(
        project=project,
        git=inspect_git(root),
        godot_executable=str(binary.path) if binary else None,
        checks=checks,
    )


def _with_runtime_version(project: ProjectInfo, binary: GodotBinary | None) -> ProjectInfo:
    if not binary or not binary.version:
        return project
    return ProjectInfo(
        root=project.root,
        name=project.name,
        godot_version=binary.version,
        config_version=project.config_version,
        csharp_detected=project.csharp_detected,
        readable=project.readable,
        damaged=project.damaged,
    )


def _project_import_check(binary: GodotBinary | None) -> CheckResult:
    name = "project import"
    if binary is None:
        return CheckResult(
            name=name,
            status=Status.SKIPPED,
            message="SKIPPED -- Godot executable not found",
        )
    details = [f"executable: {binary.path}"]
    if binary.version:
        details.append(f"version: {binary.version}")
    return CheckResult(
        name=name,
        status=Status.PASS,
        message="Godot is available for import and headless validation",
        details=details,
    )
