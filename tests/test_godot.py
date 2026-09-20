from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from gdguard.godot import discover_godot, run_headless_check
from gdguard.models import GodotBinary, Status


def test_discover_godot_uses_explicit_file(tmp_path: Path) -> None:
    binary = tmp_path / "godot.exe"
    binary.write_text("", encoding="utf-8")
    with patch("gdguard.godot._query_version", return_value="4.3.stable"):
        found = discover_godot(str(binary))
    assert found is not None
    assert found.path == binary
    assert found.version == "4.3.stable"


def test_discover_godot_returns_none_when_missing() -> None:
    with patch("gdguard.godot.shutil.which", return_value=None):
        assert discover_godot() is None


def test_requested_headless_check_fails_without_godot(tmp_path: Path) -> None:
    result = run_headless_check(tmp_path, None)
    assert result.status is Status.FAIL
    assert "Godot executable not found" in result.message


def test_headless_check_summarizes_godot_errors(tmp_path: Path) -> None:
    binary = GodotBinary(path=tmp_path / "godot", version="4.3")

    class Completed:
        returncode = 1
        stdout = ""
        stderr = "ERROR: Failed to load resource res://missing.png\nINFO: unrelated"

    with patch("gdguard.godot.run_command", return_value=Completed()):
        result = run_headless_check(tmp_path, binary)
    assert result.status is Status.FAIL
    assert any("Failed to load" in detail for detail in result.details)
    assert all("unrelated" not in detail for detail in result.details)
