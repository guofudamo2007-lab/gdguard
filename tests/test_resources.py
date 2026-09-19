from __future__ import annotations

from pathlib import Path

from gdguard.checks.resources import check_resource_references
from gdguard.models import Status
from tests.conftest import MISSING_RESOURCE, VALID_PROJECT


def _by_name(results: list, name: str):
    return next(result for result in results if result.name == name)


def test_existing_resource_and_script_references_pass() -> None:
    results = check_resource_references(VALID_PROJECT)
    assert _by_name(results, "scene resources").status is Status.PASS
    assert _by_name(results, "script references").status is Status.PASS


def test_missing_resource_is_reported() -> None:
    result = _by_name(check_resource_references(MISSING_RESOURCE), "scene resources")
    assert result.status is Status.FAIL
    joined = "\n".join(result.details)
    assert "res://scenes/player.tscn" in joined
    assert "res://assets/missing.png" in joined


def test_missing_script_reference_is_reported() -> None:
    result = _by_name(check_resource_references(MISSING_RESOURCE), "script references")
    assert result.status is Status.FAIL
    joined = "\n".join(result.details)
    assert "res://scripts/missing.gd" in joined


def test_uncertain_dynamic_paths_are_not_reported(tmp_path: Path) -> None:
    (tmp_path / "project.godot").write_text("config_version=5\n[application]\n", encoding="utf-8")
    (tmp_path / "scene.tscn").write_text(
        '[ext_resource path="res://$theme/icon.png" id="1"]\n',
        encoding="utf-8",
    )
    results = check_resource_references(tmp_path)
    assert all(result.status is Status.PASS for result in results)
