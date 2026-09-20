import subprocess
import sys
import zlib
from pathlib import Path

from tests.conftest import VALID_PROJECT


def test_fixture_texture_has_valid_png_chunks():
    data = (VALID_PROJECT / "assets" / "player.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    kinds = []
    while pos < len(data):
        size = int.from_bytes(data[pos : pos + 4], "big")
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + size]
        checksum = int.from_bytes(data[pos + 8 + size : pos + 12 + size], "big")
        assert zlib.crc32(kind + body) == checksum
        if kind == b"IDAT":
            assert zlib.decompress(body) == b"\x00\xff\x00\x00"
        kinds.append(kind)
        pos += size + 12
    assert kinds == [b"IHDR", b"IDAT", b"IEND"]


def test_demo_real_cli_and_preserves_fixture():
    root = Path(__file__).resolve().parents[1]
    before = {
        p.relative_to(VALID_PROJECT): p.read_bytes()
        for p in VALID_PROJECT.rglob("*")
        if p.is_file()
    }
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(root / "scripts" / "demo.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "healthy: PASS (exit 0)" in result.stdout
    assert "broken: FAIL (exit 1)" in result.stdout
    assert "restored: PASS (exit 0)" in result.stdout
    after = {
        p.relative_to(VALID_PROJECT): p.read_bytes()
        for p in VALID_PROJECT.rglob("*")
        if p.is_file()
    }
    assert before == after
