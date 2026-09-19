from __future__ import annotations

from gdguard.models import CheckResult, ProjectInfo, Severity, Status


def check_project_file(project: ProjectInfo) -> CheckResult:
    name = "project.godot"
    if not project.readable:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="project.godot exists but could not be read",
            severity=Severity.ERROR,
        )
    if project.damaged:
        return CheckResult(
            name=name,
            status=Status.FAIL,
            message="project.godot appears damaged or incomplete",
            details=["Expected a readable Godot project file with config_version and sections."],
            severity=Severity.ERROR,
        )
    details = [f"config_version={project.config_version}"] if project.config_version else []
    if project.csharp_detected:
        details.append("C# project detected")
    return CheckResult(
        name=name,
        status=Status.PASS,
        message="project.godot is present and readable",
        details=details,
    )
