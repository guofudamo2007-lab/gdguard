from __future__ import annotations

from pathlib import Path

from gdguard.models import Status
from gdguard.scanner import scan_project
from tests.conftest import VALID_PROJECT


def test_scan_records_csharp_and_skips_dotnet_when_missing(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="cs-game"\n',
        encoding="utf-8",
    )
    (tmp_path / "Game.csproj").write_text("<Project></Project>\n", encoding="utf-8")
    monkeypatch.setattr("gdguard.scanner.discover_godot", lambda _explicit=None: None)
    monkeypatch.setattr("gdguard.checks.dotnet.shutil.which", lambda _name: None)
    report = scan_project(tmp_path)
    assert report.project is not None
    assert report.project.csharp_detected is True
    dotnet = next(check for check in report.checks if check.name == "dotnet build")
    assert dotnet.status is Status.SKIPPED
    assert "dotnet executable not found" in dotnet.message


def test_valid_fixture_has_no_errors_without_godot(no_godot) -> None:
    report = scan_project(VALID_PROJECT)
    assert report.result == "PASS"
    names = [check.name for check in report.checks]
    assert "project.godot" in names
    assert "script scan" in names
    assert "scene resources" in names
