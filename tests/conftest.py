from __future__ import annotations

from pathlib import Path

import pytest

from gdguard.models import GodotBinary

FIXTURES = Path(__file__).parent / "fixtures"
VALID_PROJECT = FIXTURES / "valid_project"
MISSING_RESOURCE = FIXTURES / "missing_resource"


@pytest.fixture
def valid_project() -> Path:
    return VALID_PROJECT


@pytest.fixture
def missing_resource_project() -> Path:
    return MISSING_RESOURCE


@pytest.fixture
def no_godot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gdguard.scanner.discover_godot", lambda _explicit=None: None)
    monkeypatch.setattr("gdguard.godot.discover_godot", lambda _explicit=None: None)


@pytest.fixture
def fake_godot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> GodotBinary:
    binary = GodotBinary(path=tmp_path / "godot.exe", version="4.3.stable")
    monkeypatch.setattr("gdguard.scanner.discover_godot", lambda _explicit=None: binary)
    return binary
