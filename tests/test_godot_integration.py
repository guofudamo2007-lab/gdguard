"""Opt-in real engine tests; mocks elsewhere are not integration evidence."""

import os
import shutil
from pathlib import Path

import pytest

from gdguard.scanner import scan_project
from tests.conftest import VALID_PROJECT

pytestmark = pytest.mark.godot


def test_real_godot_import_and_main_scene(tmp_path):
    executable = os.environ.get("GDGUARD_TEST_GODOT")
    if not executable:
        pytest.skip("Set GDGUARD_TEST_GODOT to explicitly run a trusted fixture with Godot")
    root = tmp_path / "game"
    shutil.copytree(VALID_PROJECT, root, ignore=shutil.ignore_patterns(".godot"))
    report = scan_project(root, godot_path=executable, import_project=True, headless=True)
    assert report.result == "PASS", report.to_dict()
    for name in ("project import", "Godot headless check"):
        result = next(c for c in report.checks if c.name == name)
        assert result.extra["executed"] is True
        assert result.extra["returncode"] == 0
    (Path(root) / "scripts/player.gd").write_text("extends Node\nfunc broken(\n")
    report = scan_project(root, godot_path=executable, headless=True)
    assert report.result == "FAIL", report.to_dict()
