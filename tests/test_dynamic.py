import subprocess
from pathlib import Path

import pytest

from gdguard.checks.dotnet import check_dotnet
from gdguard.godot import run_headless_check
from gdguard.models import GodotBinary, Status


@pytest.mark.parametrize(
    "outcome,status",
    [
        (subprocess.CompletedProcess([], 0, "", ""), Status.PASS),
        (subprocess.CompletedProcess([], 1, "", ""), Status.FAIL),
        (subprocess.CompletedProcess([], 0, "", "SCRIPT ERROR: Parse Error"), Status.FAIL),
        (subprocess.TimeoutExpired(["godot"], 30), Status.FAIL),
        (OSError("cannot start"), Status.FAIL),
    ],
)
def test_headless_outcomes(tmp_path, monkeypatch, outcome, status):
    def run(command, **kwargs):
        assert command[1:] == ["--headless", "--quit-after", "1", "--path", str(tmp_path)]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("gdguard.godot.run_command", run)
    result = run_headless_check(tmp_path, GodotBinary(Path("godot"), "4.4"))
    assert result.status is status
    if status is Status.PASS:
        assert "main" in result.message.lower()


@pytest.mark.parametrize(
    "outcome,status",
    [
        (subprocess.CompletedProcess([], 0, "Build succeeded.", ""), Status.PASS),
        (subprocess.CompletedProcess([], 1, "", "build failed"), Status.FAIL),
        (subprocess.CompletedProcess([], 0, "X.cs(1): error CS1002: ; expected", ""), Status.FAIL),
        (subprocess.TimeoutExpired(["dotnet"], 60), Status.FAIL),
        (OSError("cannot start"), Status.FAIL),
    ],
)
def test_dotnet_outcomes(tmp_path, monkeypatch, outcome, status):
    (tmp_path / "Game.csproj").write_text("<Project />")
    monkeypatch.setattr("shutil.which", lambda _: "dotnet")

    def run(command, **kwargs):
        assert command[:3] == ["dotnet", "build", str(tmp_path / "Game.csproj")]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("gdguard.checks.dotnet.run_command", run)
    assert check_dotnet(tmp_path, True).status is status


def test_requested_build_without_target_fails(tmp_path):
    assert check_dotnet(tmp_path, False).status is Status.FAIL


@pytest.mark.parametrize("version", [None, "3.5.stable", "not-an-engine"])
def test_unknown_engine_version_cannot_validate_import(tmp_path, monkeypatch, version):
    from gdguard.godot import run_import_check

    def forbidden(*args, **kwargs):
        pytest.fail("unsupported engine must not be treated as an import validator")

    monkeypatch.setattr("gdguard.godot.run_command", forbidden)
    result = run_import_check(tmp_path, GodotBinary(Path("godot"), version))
    assert result.status is Status.FAIL
    assert result.extra["executed"] is False
