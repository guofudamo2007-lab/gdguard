from __future__ import annotations

import json
import re
from pathlib import Path

from gdguard.fs import iter_files, validate_local_file
from gdguard.models import CheckResult, Severity, Status

_HEADER = re.compile(r"(?m)^[ \t]*\[(\w+)\b[^\]]*\]")
_ATTR = re.compile(r'(\w+)\s*=\s*("(?:\\.|[^"\\])*"|[^\s]+)', re.DOTALL)
_SCRIPT_SUFFIXES = {".gd", ".cs"}


def _mask(text: str) -> str:
    """Mask comments and complete strings, preserving offsets and line numbers."""
    masked = list(text)
    i = 0
    while i < len(text):
        if text[i] == ";":
            while i < len(text) and text[i] != "\n":
                masked[i] = " "
                i += 1
        elif text[i] == '"':
            masked[i] = " "
            i += 1
            while i < len(text):
                char = text[i]
                masked[i] = "\n" if char == "\n" else " "
                i += 1
                if char == "\\" and i < len(text):
                    masked[i] = "\n" if text[i] == "\n" else " "
                    i += 1
                elif char == '"':
                    break
            else:
                raise ValueError("unterminated string")
        else:
            i += 1
    return "".join(masked)


def _declarations(text: str, suffix: str):
    if "\x00" in text:
        raise ValueError("NUL bytes in resource text")
    masked = _mask(text)
    headers = list(_HEADER.finditer(masked))
    expected = "gd_scene" if suffix.lower() == ".tscn" else "gd_resource"
    if not headers or headers[0].group(1) != expected:
        raise ValueError(f"missing [{expected}] header")
    starts = list(re.finditer(r"(?m)^[ \t]*\[ext_resource\b", masked))
    external = [h for h in headers if h.group(1) == "ext_resource"]
    if len(starts) != len(external):
        raise ValueError("incomplete external resource declaration")
    for header in external:
        raw = text[header.start() : header.end()]
        # Remove comments outside strings while retaining the attribute values.
        tokens = re.findall(r'"(?:\\.|[^"\\])*"|;[^\n]*|[^";]+', raw, re.DOTALL)
        raw = "".join(token for token in tokens if not token.startswith(";"))
        body = raw[raw.index("ext_resource") + len("ext_resource") : -1]
        attrs = {}
        end = 0
        for match in _ATTR.finditer(body):
            if body[end : match.start()].strip() or match[1] in attrs:
                raise ValueError("malformed external resource attributes")
            attrs[match[1]] = match[2]
            end = match.end()
        if body[end:].strip():
            raise ValueError("malformed external resource attributes")
        line = text.count("\n", 0, header.start()) + 1
        path = attrs.get("path")
        uid = attrs.get("uid")
        if path is None and uid is None:
            raise ValueError(f"external resource at line {line} has no path or UID")
        try:
            reference = json.loads(path) if path is not None else None
            identifier = json.loads(uid) if uid is not None else None
        except (ValueError, TypeError) as exc:
            raise ValueError(f"unsupported or malformed path/UID string at line {line}") from exc
        if not isinstance(reference, (str, type(None))) or not isinstance(
            identifier, (str, type(None))
        ):
            raise ValueError(f"path/UID must be a string at line {line}")
        yield line, reference, identifier


def _target_reason(root: Path, source: Path, reference: str) -> str | None:
    if not reference:
        return "empty path"
    if reference.startswith("res://"):
        relative = reference[6:]
        parts = []
    else:
        relative = reference
        parts = list(source.parent.relative_to(root).parts)
    if relative.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", relative):
        return "outside project root (absolute path)"
    if "\\" in relative:
        return "backslash path is unsupported; use Godot forward slashes"
    for part in relative.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return "outside project root"
            parts.pop()
        else:
            parts.append(part)
    target = root.joinpath(*parts)
    try:
        # Inspect each component before descending: never enumerate a linked directory.
        current = root
        for part in parts:
            names = {entry.name for entry in current.iterdir()}
            if part not in names:
                if any(name.casefold() == part.casefold() for name in names):
                    return "path case mismatch (not portable to case-sensitive filesystems)"
                return "missing file"
            current /= part
            validate_local_file(root, current, directory=True)
        validate_local_file(root, target)
    except (OSError, ValueError, RuntimeError) as exc:
        return str(exc)
    return None


def check_resource_references(project_root: Path) -> list[CheckResult]:
    root = project_root.resolve()
    failures: dict[str, list[str]] = {"scene resources": [], "script references": []}
    counts = dict.fromkeys(failures, 0)
    skipped: list[str] = []
    scanned = 0
    incomplete = False
    try:
        for source in iter_files(root, suffixes=(".tscn", ".tres")):
            scanned += 1
            location = f"res://{source.relative_to(root).as_posix()}"
            try:
                text = source.read_text(encoding="utf-8-sig")
                declarations = list(_declarations(text, source.suffix))
            except (OSError, UnicodeError, ValueError) as exc:
                incomplete = True
                failures["scene resources"].append(f"{location}: unable to inspect: {exc}")
                continue
            for line, reference, uid in declarations:
                item = f"{location}:{line}: {reference or uid}"
                if reference is None or reference.startswith("uid://"):
                    skipped.append(f"{item}: UID resolution not verified")
                    continue
                if "://" in reference and not reference.startswith("res://"):
                    skipped.append(f"{item}: unsupported URI scheme; not verified")
                    continue
                kind = (
                    "script references"
                    if Path(reference).suffix.lower() in _SCRIPT_SUFFIXES
                    else "scene resources"
                )
                reason = _target_reason(root, source, reference)
                if uid:
                    skipped.append(f"{item}: UID {uid} resolution not verified")
                if reason:
                    # Godot may resolve a moved resource by UID despite a stale fallback path.
                    if uid and (reason == "missing file" or reason.startswith("path case")):
                        skipped.append(f"{item}: fallback path {reason}; UID may resolve elsewhere")
                    else:
                        failures[kind].append(f"{item}: {reason}")
                else:
                    counts[kind] += 1
    except OSError as exc:
        incomplete = True
        failures["scene resources"].append(f"Traversal incomplete: {exc}")

    results = []
    for name, details in failures.items():
        status = (
            Status.FAIL
            if details
            else (Status.SKIPPED if incomplete or not scanned else Status.PASS)
        )
        message = f"Inspected {scanned} resource file(s); {counts[name]} file path(s) verified"
        if details:
            message = "Reference inspection failed"
        elif incomplete:
            message = "Reference inspection incomplete; see resource input/traversal failures"
        elif not scanned:
            message = "No .tscn/.tres files found; reference inspection not executed"
        results.append(
            CheckResult(
                name,
                status,
                message,
                details,
                Severity.ERROR if details else Severity.INFO,
                {"scanned_files": scanned, "verified_paths": counts[name]},
            )
        )
    if skipped:
        results.append(
            CheckResult(
                "unverified resource references",
                Status.SKIPPED,
                f"{len(skipped)} unresolved reference detail(s)",
                skipped,
            )
        )
    return results
