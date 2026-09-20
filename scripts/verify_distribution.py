"""Install each distribution in a fresh venv and exercise CLI away from the checkout."""

import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    artifacts = sorted((root / "dist").glob("*.whl")) + sorted((root / "dist").glob("*.tar.gz"))
    if not any(p.suffix == ".whl" for p in artifacts) or not any(
        p.name.endswith(".tar.gz") for p in artifacts
    ):
        raise SystemExit("Build wheel and sdist first: python -m build")
    for artifact in artifacts:
        with tempfile.TemporaryDirectory(prefix="gdguard-install-") as temporary:
            directory = Path(temporary)
            environment = directory / "venv"
            venv.EnvBuilder(with_pip=True).create(environment)
            bin_dir = environment / ("Scripts" if os.name == "nt" else "bin")
            python = bin_dir / ("python.exe" if os.name == "nt" else "python")
            cli = bin_dir / ("gdguard.exe" if os.name == "nt" else "gdguard")
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["PYTHONUTF8"] = "1"

            def run(command, directory=directory, env=env):
                result = subprocess.run(
                    [str(arg) for arg in command],
                    cwd=directory,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=180,
                )
                if result.returncode:
                    raise RuntimeError(result.stdout + result.stderr)
                return result.stdout

            run([python, "-m", "pip", "install", "--no-deps", artifact])
            run([cli, "--help"])
            version = run([cli, "--version"]).strip()
            location = run([python, "-c", "import gdguard; print(gdguard.__file__)"]).strip()
            assert Path(location).is_relative_to(environment), location
            report = json.loads(
                run([cli, "check", root / "tests/fixtures/valid_project", "--format", "json"])
            )
            assert report["result"] == "PASS"
            assert report["scope"]["mode"] == "static"
            assert report["summary"]["skipped"] >= 3
            demo = run([python, root / "scripts/demo.py"])
            assert "restored: PASS (exit 0)" in demo
            print(f"{artifact.name}: clean install, {version}, CLI and demo PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
