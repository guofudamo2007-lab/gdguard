import json
import subprocess
import sys
from pathlib import Path

import pytest

from gdguard.checks.resources import check_resource_references
from gdguard.cli import main
from gdguard.process import run_command
from gdguard.scanner import scan_project


def make_project(root):
    (root / "project.godot").write_text("config_version=5\n[application]\n")


@pytest.mark.parametrize("kind", ["file", "directory", "project"])
def test_links_are_not_read(tmp_path, kind):
    root = tmp_path / "project"
    root.mkdir()
    make_project(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "data.tscn"
    target.write_text("[gd_scene format=3]\n")
    link = root / ("project.godot" if kind == "project" else "linked")
    if kind == "file":
        link = link.with_suffix(".tscn")
    if kind == "project":
        link.unlink()
    try:
        link.symlink_to(
            outside if kind == "directory" else target, target_is_directory=kind == "directory"
        )
    except OSError as exc:
        pytest.skip(f"Creating symlinks unavailable on this host: {exc}")
    report = scan_project(root)
    assert report.result == "FAIL"
    assert "symbolic link" in str(report.to_dict()) or "could not be read" in str(report.to_dict())


def test_secret_read_failure_is_not_pass(tmp_path, monkeypatch):
    make_project(tmp_path)
    target = tmp_path / "candidate.pem"
    target.write_text("example")
    original = Path.open

    def opened(path, *args, **kwargs):
        if path == target:
            raise PermissionError("candidate.pem denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    assert scan_project(tmp_path).result == "FAIL"


def test_walk_failure_cannot_be_silenced(tmp_path, monkeypatch):
    make_project(tmp_path)

    def walk(root, **kwargs):
        kwargs["onerror"](PermissionError("unreadable folder"))
        return iter(())

    monkeypatch.setattr("gdguard.fs.os.walk", walk)
    assert scan_project(tmp_path).result == "FAIL"


def test_ignored_caches_and_venvs_are_not_scanned(tmp_path):
    make_project(tmp_path)
    for name in (".godot", ".git", ".venv", "venv", "env", "__pycache__"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "bad.tscn").write_bytes(b"\xff")
    assert scan_project(tmp_path).result == "PASS"


def test_reference_order_is_stable_and_keeps_both_sources(tmp_path):
    for name in ("z.tscn", "a.tscn"):
        (tmp_path / name).write_text(
            '[gd_scene format=3]\n[ext_resource path="res://missing.png" id="1"]\n'
        )
    result = check_resource_references(tmp_path)[0]
    assert len(result.details) == 2
    assert "a.tscn:2" in result.details[0]
    assert "z.tscn:2" in result.details[1]


def test_default_does_not_discover_tools(tmp_path, monkeypatch):
    make_project(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("static check attempted tool discovery")

    monkeypatch.setattr("gdguard.scanner.discover_godot", forbidden)
    assert scan_project(tmp_path, godot_path="present-godot").result == "PASS"


@pytest.mark.parametrize(
    "option,flags",
    [
        ("--import", ["--headless", "--editor", "--import"]),
        ("--headless", ["--headless", "--quit-after", "1"]),
    ],
)
@pytest.mark.parametrize("outcome", ["ok", "error", "timeout", "launch"])
def test_requested_godot_command_evidence(tmp_path, monkeypatch, capsys, option, flags, outcome):
    make_project(tmp_path)
    executable = tmp_path / "Godot with spaces.exe"
    executable.write_text("")

    def run(command, **kwargs):
        if command[1:] == ["--version"]:
            return subprocess.CompletedProcess(command, 0, "4.4.stable", "")
        assert command == [str(executable), *flags, "--path", str(tmp_path)]
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(command, 60)
        if outcome == "launch":
            raise OSError("cannot start")
        return subprocess.CompletedProcess(
            command, 0, "", "ERROR: simulated engine failure" if outcome == "error" else ""
        )

    monkeypatch.setattr("gdguard.godot.run_command", run)
    code = main(["check", str(tmp_path), option, "--godot", str(executable), "--format", "json"])
    captured = capsys.readouterr()
    assert captured.err == ""
    report = json.loads(captured.out)
    assert code == (0 if outcome == "ok" else 1)
    name = "project import" if option == "--import" else "Godot headless check"
    check = next(c for c in report["checks"] if c["name"] == name)
    assert check["extra"]["command"] == [str(executable), *flags, "--path", str(tmp_path)]
    assert check["extra"]["executed"] is (outcome != "launch")


def test_real_process_timeout():
    # A trusted Python process, not a Godot integration test.
    with pytest.raises(subprocess.TimeoutExpired):
        run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.1)


def test_link_detection_does_not_open_the_target(tmp_path, monkeypatch):
    make_project(tmp_path)
    source = tmp_path / "scene.tscn"
    source.write_text("[gd_scene format=3]\n")
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda p: p == source or original(p))
    original_read = Path.read_text

    def read(path, *args, **kwargs):
        if path == source:
            pytest.fail("linked source contents must not be read")
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    assert scan_project(tmp_path).result == "FAIL"


def test_readme_gdguard_command_arguments():
    import shlex

    from gdguard.cli import _build_parser

    readme = Path(__file__).resolve().parents[1] / "README.md"
    commands = [
        line
        for line in readme.read_text(encoding="utf-8").splitlines()
        if line.startswith("gdguard check ")
    ]
    assert commands
    for command in commands:
        _build_parser().parse_args(shlex.split(command)[1:])
