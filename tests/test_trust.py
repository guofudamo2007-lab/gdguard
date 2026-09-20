"""Regressions for execution consent and truthful reports (no real engine)."""

import json
import subprocess
from pathlib import Path

import pytest

from gdguard.cli import main
from gdguard.models import Status
from gdguard.scanner import scan_project


@pytest.fixture
def project(tmp_path):
    (tmp_path / "project.godot").write_text("config_version=5\n[application]\n")
    (tmp_path / "Game.csproj").write_text("<Project />")
    return tmp_path


def test_default_never_starts_a_process(project, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("default static scan attempted an external command")

    monkeypatch.setattr(subprocess, "run", forbidden)
    report = scan_project(project, godot_path="godot")
    dynamic = [
        c
        for c in report.checks
        if c.name in {"project import", "Godot headless check", "dotnet build"}
    ]
    assert len(dynamic) == 3
    assert all(c.status is Status.SKIPPED for c in dynamic)


@pytest.mark.parametrize("option", ["--import", "--headless", "--dotnet-build"])
def test_requested_missing_tool_is_failure(project, monkeypatch, capsys, option):
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert main(["check", str(project), option, "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["failed"] >= 1


def test_report_describes_only_executed_scope(project, capsys):
    assert main(["check", str(project), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["scope"]["mode"] == "static"
    assert payload["summary"]["skipped"] >= 3
    assert main(["check", str(project)]) == 0
    output = capsys.readouterr().out
    assert "Skipped:" in output
    assert "executed checks only" in output


@pytest.mark.parametrize("filename", ["project.godot", "bad.gd", "bad.tscn"])
def test_invalid_utf8_is_a_check_failure(project, filename):
    (project / filename).write_bytes(b"\xff\xfe\x00")
    report = scan_project(project)
    assert report.result == "FAIL"


def test_resource_read_error_is_visible(project, monkeypatch):
    source = project / "bad.tscn"
    source.write_text("[gd_scene format=3]\n")
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path == source:
            raise PermissionError("test denied read")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    report = scan_project(project)
    assert report.result == "FAIL"
    assert "bad.tscn" in str(report.to_dict())
