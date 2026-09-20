from __future__ import annotations

from pathlib import Path

from gdguard.fs import iter_files
from gdguard.models import CheckResult, Severity, Status

_SECRET_SUFFIXES = {".keystore", ".jks", ".p12", ".pfx"}
_SECRET_NAMES = {".env", ".env.local", ".env.production"}
_PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
)
_TEXT_SUFFIXES = {".pem", ".key", ".env", ".txt", ""}


def check_sensitive_files(project_root: Path) -> CheckResult:
    name = "sensitive files"
    hits: list[str] = []
    for path in iter_files(project_root):
        relative = path.relative_to(project_root).as_posix()
        if _looks_secret_name(path):
            hits.append(relative)
            continue
        if path.suffix.lower() in _TEXT_SUFFIXES and _contains_private_key(path):
            hits.append(relative)

    if hits:
        return CheckResult(
            name=name,
            status=Status.WARNING,
            message="WARNING\nPotential sensitive file in project (Git tracking not checked):",
            details=hits,
            severity=Severity.WARNING,
        )
    return CheckResult(
        name=name,
        status=Status.PASS,
        message="No obvious sensitive files found",
    )


def _looks_secret_name(path: Path) -> bool:
    if path.name.lower() in _SECRET_NAMES:
        return True
    return path.suffix.lower() in _SECRET_SUFFIXES


def _contains_private_key(path: Path) -> bool:
    with path.open("rb") as stream:
        sample = stream.read(4096)
    return any(marker in sample for marker in _PRIVATE_KEY_MARKERS)
