from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Status(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: Status
    message: str
    details: list[str] = field(default_factory=list)
    severity: Severity = Severity.INFO
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": list(self.details),
            "severity": self.severity.value,
        }
        if self.extra:
            payload["extra"] = dict(self.extra)
        return payload


@dataclass(frozen=True)
class GitInfo:
    branch: str | None
    dirty: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {"branch": self.branch, "dirty": self.dirty}


@dataclass(frozen=True)
class GodotBinary:
    path: Path
    version: str | None


@dataclass(frozen=True)
class ProjectInfo:
    root: Path
    name: str
    godot_version: str
    config_version: int | None
    csharp_detected: bool
    readable: bool
    damaged: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.root),
            "godot_version": self.godot_version,
            "config_version": self.config_version,
            "csharp_detected": self.csharp_detected,
        }


@dataclass
class ScanReport:
    project: ProjectInfo | None
    git: GitInfo | None
    godot_executable: str | None
    checks: list[CheckResult] = field(default_factory=list)
    dynamic_requested: list[str] = field(default_factory=list)

    @property
    def scope(self) -> dict[str, Any]:
        return {
            "mode": "static+dynamic" if self.dynamic_requested else "static",
            "dynamic_requested": self.dynamic_requested,
            "result_meaning": "executed checks only; not full game validation",
        }

    @property
    def summary(self) -> dict[str, int]:
        counts = {"passed": 0, "warnings": 0, "failed": 0, "skipped": 0}
        for check in self.checks:
            if check.status is Status.PASS:
                counts["passed"] += 1
            elif check.status is Status.WARNING:
                counts["warnings"] += 1
            elif check.status is Status.FAIL:
                counts["failed"] += 1
            elif check.status is Status.SKIPPED:
                counts["skipped"] += 1
        return counts

    @property
    def error_count(self) -> int:
        return sum(1 for check in self.checks if check.status is Status.FAIL)

    @property
    def warning_count(self) -> int:
        return sum(1 for check in self.checks if check.status is Status.WARNING)

    @property
    def result(self) -> str:
        return "FAIL" if self.error_count else "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project.to_dict() if self.project else None,
            "git": self.git.to_dict() if self.git else None,
            "godot_executable": self.godot_executable,
            "summary": self.summary,
            "scope": self.scope,
            "result": self.result,
            "checks": [check.to_dict() for check in self.checks],
        }
