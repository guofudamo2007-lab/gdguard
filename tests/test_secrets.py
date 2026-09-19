from __future__ import annotations

from pathlib import Path

from gdguard.checks.secrets import check_sensitive_files
from gdguard.models import Status


def test_keystore_is_a_warning_not_a_failure(tmp_path: Path) -> None:
    (tmp_path / "android").mkdir()
    (tmp_path / "android" / "release.keystore").write_bytes(b"not-a-real-key")
    result = check_sensitive_files(tmp_path)
    assert result.status is Status.WARNING
    assert "android/release.keystore" in result.details


def test_private_key_marker_is_detected(tmp_path: Path) -> None:
    (tmp_path / "debug.pem").write_text("-----BEGIN PRIVATE KEY-----\nabc\n", encoding="utf-8")
    result = check_sensitive_files(tmp_path)
    assert result.status is Status.WARNING
    assert "debug.pem" in result.details


def test_ordinary_assets_are_not_flagged(tmp_path: Path) -> None:
    (tmp_path / "player.png").write_bytes(b"PNG")
    result = check_sensitive_files(tmp_path)
    assert result.status is Status.PASS
