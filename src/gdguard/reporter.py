from __future__ import annotations

import json

from gdguard.models import CheckResult, ScanReport, Status

_STATUS_MARK = {
    Status.PASS: "OK",
    Status.WARNING: "!!",
    Status.FAIL: "XX",
    Status.SKIPPED: "--",
}


def render_text(report: ScanReport) -> str:
    project_name = report.project.name if report.project else "unknown"
    godot_version = report.project.godot_version if report.project else "unknown"
    lines = [
        "GDGuard",
        "",
        "Project:",
        project_name,
        "",
        "Godot:",
        godot_version,
        "",
        "Checks",
        "",
    ]
    for check in report.checks:
        mark = _STATUS_MARK[check.status]
        lines.append(f"{mark} {check.name}")
        for detail_line in _message_lines(check):
            lines.append(f"  {detail_line}")
    lines.extend(
        [
            "",
            f"Warnings: {report.warning_count}",
            f"Errors: {report.error_count}",
            f"Skipped: {report.summary['skipped']}",
            f"Scope: {report.scope['mode']}; {report.scope['result_meaning']}",
            "",
            f"Result: {report.result}",
        ]
    )
    if report.git is not None and (report.git.branch or report.git.dirty is not None):
        branch = report.git.branch or "unknown"
        dirty = "dirty" if report.git.dirty else "clean"
        if report.git.dirty is None:
            dirty = "unknown"
        lines.extend(["", f"Git: {branch} ({dirty})"])
    return "\n".join(lines) + "\n"


def render_json(report: ScanReport) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n"


def _message_lines(check: CheckResult) -> list[str]:
    lines = [part for part in check.message.splitlines() if part]
    for detail in check.details:
        lines.extend(detail.splitlines() or [detail])
    return lines
