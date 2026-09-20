"""Self-authored MIT fixture: real static CLI checks, mutations only in a temporary copy."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable, help="Installed GDGuard interpreter")
    args = parser.parse_args()
    fixture = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "valid_project"
    with tempfile.TemporaryDirectory(prefix="gdguard-demo-") as temporary:
        root = Path(temporary) / "demo project"
        shutil.copytree(fixture, root, ignore=shutil.ignore_patterns(".godot"))
        texture = root / "assets" / "player.png"
        original = texture.read_bytes()

        def check(stage, expected):
            result = subprocess.run(
                [args.python, "-m", "gdguard", "check", str(root), "--format", "json"],
                cwd=temporary,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            assert result.returncode == expected, result.stdout + result.stderr
            assert result.stderr == "", result.stderr
            report = json.loads(result.stdout)
            assert report["scope"]["mode"] == "static"
            assert report["summary"]["skipped"] >= 3
            assert report["result"] == ("FAIL" if expected else "PASS")
            print(f"{stage}: {report['result']} (exit {result.returncode})")
            if expected:
                resource = next(c for c in report["checks"] if c["name"] == "scene resources")
                assert resource["status"] == "FAIL"
                detail = next(d for d in resource["details"] if "res://assets/player.png" in d)
                assert "res://scenes/player.tscn:4" in detail
                assert "missing file" in detail
                print(f"  {detail}")
            else:
                assert report["summary"]["failed"] == 0

        check("healthy", 0)
        texture.unlink()
        check("broken", 1)
        texture.write_bytes(original)
        check("restored", 0)
    print("Static checks only; no Godot or dotnet executed. Original fixture unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
