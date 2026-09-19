from __future__ import annotations

from pathlib import Path

import pytest

from gdguard.errors import GDGuardError
from gdguard.project import load_project_info, resolve_project_root
from tests.conftest import VALID_PROJECT


def test_resolves_godot_project_root() -> None:
    root = resolve_project_root(VALID_PROJECT)
    assert root == VALID_PROJECT.resolve()
    assert (root / "project.godot").is_file()


def test_missing_project_godot_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(GDGuardError, match="No Godot project found"):
        resolve_project_root(tmp_path)


def test_loads_project_name_and_feature_version() -> None:
    info = load_project_info(VALID_PROJECT)
    assert info.name == "my-game"
    assert info.godot_version == "4.3"
    assert info.config_version == 5
    assert info.readable is True
    assert info.damaged is False


def test_unknown_version_when_features_are_missing(tmp_path: Path) -> None:
    (tmp_path / "project.godot").write_text("config_version=5\n[application]\n", encoding="utf-8")
    info = load_project_info(tmp_path)
    assert info.godot_version == "unknown"
