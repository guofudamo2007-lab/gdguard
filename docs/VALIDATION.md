# Local validation — 2026-09-20

Candidate: 0.2.0rc1. Host: Windows 11 (10.0.26200), Python 3.14.6.
This is local evidence, not a remote CI result or external adoption record.

## Baseline

The working tree was clean before this task. The configured origin was
guofudamo2007-lab/gdguard. No applicable AGENTS.md was found in the project/drive root.

- `python -m pytest -q`: 22 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: one pre-existing formatting failure in test_scan.py.
- New resource/trust regressions initially produced 21 failures; dynamic-error tests
  reproduced uncaught TimeoutExpired, launch errors reported as SKIPPED, and zero-exit
  dotnet error logs reported as PASS.
- The original valid fixture PNG failed CRC/decompression checks; its self-authored
  1x1 RGB data was repaired and a decoding regression added.

Default process launch initially failed before starting the shell with
helper_unknown_error / setup refresh had errors. Explicitly authorized elevated tool
execution worked; no system security settings were changed.

## Commands and results

Commands below were run from the repository root using
`.venv\Scripts\python` as the interpreter. The venv was created with
`python -m venv .venv` and populated with `python -m pip install -e ".[dev]" build`.
PyYAML was installed only in that venv to parse the workflow and issue templates;
it is not a GDGuard dependency.

| Command | Actual result |
| --- | --- |
| `python -m ruff check .` | Passed |
| `python -m ruff format --check .` | 40 Python files already formatted |
| `python -m pytest -q` | 80 passed, 4 skipped |
| `python scripts/demo.py` | PASS exit 0 -> FAIL exit 1 -> PASS exit 0 |
| `python -m build` | Built wheel and sdist for 0.2.0rc1; wheel built from sdist |
| `python scripts/verify_distribution.py` | Both artifacts installed in separate fresh venvs; CLI help/version, static JSON and demo passed |
| `git diff --check` | Passed (Git line-ending normalization notices are informational) |
| YAML parsing with PyYAML | action.yml, workflow and both issue templates parsed; configured matrix/minimum permissions checked |

The distribution verifier runs from a temporary working directory, removes PYTHONPATH,
checks the imported module belongs to the new venv, invokes the installed console script,
and runs the real demo. It therefore does not mistake editable source imports for an
installed-package check. Source installation can download isolated build requirements.

## What was not verified

- Real Godot import/smoke: no Godot binary in PATH and no explicitly configured test
  binary. The opt-in integration test is SKIPPED. Command simulations are not engine
  compatibility evidence; no engine version is claimed integration-tested.
- Three real symlink tests: Windows returned WinError 1314 (creation privilege absent).
  Link detection/no-content-read has a separate passing simulated regression; that
  does not replace the real filesystem test. Linux CI is configured to exercise it.
- Real Godot C# build: not run. dotnet command outcomes are simulated; the presence
  of dotnet.exe on the host is not build integration evidence.
- Linux, Python 3.11/3.12/3.13, remote Actions runtime: not run locally.
  The new Windows/Linux 3.11/3.14 matrix and Action success/failure scenarios await a push
  authorized by the maintainer. YAML parsing is not GitHub Actions execution.
- PyPI/Twine upload, public Release, tag/push, repository setting edits, outreach
  and funding applications: not performed.

## Scope and remaining evidence

The static gate covers specific file/declaration checks and can still miss engine
syntax/type/resource-decoding and runtime defects. UID relationships remain unverified.
Review skipped results even when exit code is 0. Dynamic checks can execute code, write
files and use the network; neither headless nor GDGuard is an OS sandbox.

All repository edits are confined to GDGuard. No private game code, story, characters
or media were copied. The demo only mutates its own temporary fixture copy.
No existing user changes were reset and no commit or remote mutation was performed.

Release checklist and an unsent developer invitation are in [RELEASE.md](RELEASE.md).
External trial reports, independently confirmed fixes, actual CI runs and sustained
maintenance evidence remain to be collected. No funding outcome is implied.

