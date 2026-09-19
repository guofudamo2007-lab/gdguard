from __future__ import annotations

import json
from pathlib import Path

from gdguard.cli import main
from tests.conftest import MISSING_RESOURCE, VALID_PROJECT


def _run(argv: list[str]) -> int:
    try:
        return main(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return int(code)


def test_help_and_version(capsys) -> None:
    assert _run(["--help"]) == 0
    help_out = capsys.readouterr().out
    assert "gdguard" in help_out
    assert "check" in help_out
    assert _run(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_valid_project_passes_without_godot(capsys, no_godot) -> None:
    code = _run(["check", str(VALID_PROJECT)])
    output = capsys.readouterr().out
    assert code == 0
    assert "Result: PASS" in output
    assert "my-game" in output
    assert "Godot executable not found" in output


def test_missing_resource_project_fails(capsys, no_godot) -> None:
    code = _run(["check", str(MISSING_RESOURCE)])
    output = capsys.readouterr().out
    assert code == 1
    assert "Result: FAIL" in output
    assert "res://assets/missing.png" in output


def test_json_output_is_parseable(capsys, no_godot) -> None:
    code = _run(["check", str(VALID_PROJECT), "--format", "json"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["project"]["name"] == "my-game"
    assert payload["result"] == "PASS"
    assert "passed" in payload["summary"]
    assert payload["summary"]["failed"] == 0


def test_missing_project_uses_exit_code_2(capsys, tmp_path: Path) -> None:
    code = _run(["check", str(tmp_path)])
    err = capsys.readouterr().err
    assert code == 2
    assert "No Godot project found" in err
    assert "Traceback" not in err
