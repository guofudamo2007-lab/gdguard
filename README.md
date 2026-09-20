# GDGuard

Catch broken Godot scene/resource file references locally, before a commit, merge, or release.

GDGuard is a dependency-free Python CLI and CI quality gate. Default checks read local
files, start no external commands, use no API keys, and send no telemetry or project data.
This checkout prepares **0.2.0rc1**; it has not been published by this work.

## Install and try

Python 3.11+ is required. From this repository's root:

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell, or
`source .venv/bin/activate` on Linux/macOS, then:

```sh
python -m pip install .
gdguard --version
gdguard check tests/fixtures/valid_project
gdguard check tests/fixtures/valid_project --format json
python scripts/demo.py
```

For development use `python -m pip install -e ".[dev]"`.
Use this checkout or a reviewed source archive; no PyPI availability is claimed.
`pip install gdguard` is not the installation method for this unpublished candidate.

To check your own project: `gdguard check "/path/to/my game"`, or run
`gdguard check` from its root. `python -m gdguard` also works.
Use `gdguard check --help` for all parameters.

## Reproduce a failure and recovery

`python scripts/demo.py` copies our self-authored MIT fixture to a temporary directory,
runs the real CLI, deletes its referenced texture, checks the failure, restores it,
and checks again. It asserts exit codes, JSON scope and the diagnostic location.
It never modifies the original fixture or your game, and needs neither Godot nor a key.

Actual local output excerpt (Windows, Python 3.14.6):

```text
healthy: PASS (exit 0)
broken: FAIL (exit 1)
  res://scenes/player.tscn:4: res://assets/player.png: missing file
restored: PASS (exit 0)
```

This is a project-owned test example, not external adoption evidence.

## What is checked

| Check | Scope |
| --- | --- |
| `project.godot` | Readability, UTF-8, basic config marker/section presence |
| `script scan` | GDScript UTF-8 readability and NUL bytes, **not syntax** |
| `scene resources` / `script references` | `[ext_resource ... path="..."]` declarations in .tscn/.tres; file existence, exact path case and project boundary |
| `sensitive files` | Obvious filenames and private-key markers in the first 4096 bytes of selected text files; warning only, not a secret-scanner guarantee |
| `project import` | SKIPPED unless `--import` was requested |
| `Godot headless check` | SKIPPED unless `--headless` was requested |
| `dotnet build` | SKIPPED unless `--dotnet-build` was requested |

Resource diagnostics include source, declaration line, target and reason. Both `res://`
and paths relative to the source file are supported. Comments, explanatory strings,
and resource IDs are not treated as file declarations. Chinese, spaces, `$`, `%`,
braces and leading dots are literal filename characters, not interpolation syntax.

References must stay within the project and point to regular files. Child symlinks
and junctions are rejected without reading their contents, including internal links.
Unreadable inputs and traversal failures are reported as failures.
Cache, Git and conventional virtual-environment directories are excluded.

UIDs are **not resolved**. UID-only references are SKIPPED. For a declaration containing
a UID and a fallback file path, a missing/case-mismatched fallback is marked unverified
because the engine may locate a moved resource by UID. Even when the path exists, UID
resolution remains unverified. Review skipped details; exit 0 does not verify them.

## Explicit dynamic checks

Only enable these for a project you trust:

```sh
gdguard check "/path/to/my game" --import --godot "/path/to/godot"
gdguard check "/path/to/my game" --headless --godot "/path/to/godot"
gdguard check "/path/to/my game" --dotnet-build
```

These commands require an identifiable Godot 4 binary (editor for import).
Flags are independent and can be combined. `--godot` selects a binary; it does not
enable execution on its own. Without it, explicit Godot checks search PATH.

- Import executes `godot --headless --editor --import --path PROJECT` (60s timeout).
- Smoke executes `godot --headless --quit-after 1 --path PROJECT` (30s timeout).
  Completion covers only this main-scene command, not all scenes/scripts or gameplay.
- Build executes `dotnet build TARGET --nologo -v q` (60s timeout).
  The first lexically sorted .sln is selected, otherwise the first .csproj.
  The selected target and command are recorded; other targets are not verified.

These commands can execute project/editor/build code, write caches or other files,
and access the network (including package restore). **Headless is not a sandbox.**
GDGuard itself does not upload files, but it cannot constrain code run by external tools.
Timeouts terminate the direct process; descendant-process cleanup is not guaranteed.
A missing tool, unavailable build target, launch failure, timeout, nonzero exit, or
recognized error log is a FAIL when explicitly requested. Recognition of error logs
is heuristic and not exhaustive. Command arguments are passed as a list without a shell.

## Reports and exit codes

Text prints every check's explanation, scope and skipped count. JSON mode writes a
single JSON report to stdout; captured engine/build logs remain in the report.
Usage/discovery errors use stderr and may produce no JSON document.

- **PASS**: this concrete check completed without a blocking finding.
- **WARNING**: a nonblocking finding was detected.
- **FAIL**: a blocking finding, incomplete inspection, or requested execution failure.
- **SKIPPED**: not executed/unverified, with a reason.

The compatible top-level `result` is PASS if there are no failed checks. It refers
to **executed checks only**, never complete game validation. Consult `summary.skipped`,
each check's details, and `scope` (`static` or `static+dynamic` with requested checks).

| Exit | Meaning |
| --- | --- |
| 0 | No FAIL checks; warnings and skipped checks may remain |
| 1 | At least one FAIL, including requested tools that cannot run |
| 2 | Bad arguments, project not found, or unexpected tool/environment error |

## GitHub Actions

After these changes are committed to the revision you choose, use the composite Action:

```yaml
name: Godot static checks
on: [push, pull_request]
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: guofudamo2007-lab/gdguard@main
        with:
          path: "my game"
```

Pin a reviewed commit SHA for reproducibility; no candidate release tag is assumed
to exist. The Action installs its own checkout, runs static checks using that Python,
quotes inputs through environment variables, and propagates failure exit codes.
The repository CI is configured for Windows/Linux, Python 3.11/3.14, Ruff, pytest,
the demo, wheel/sdist builds, clean installs and Action success/failure cases.
Configuration is not evidence that remote CI has run: see [validation](docs/VALIDATION.md).

## Boundaries and feedback

The scanner targets Godot 4 text resource declarations; this is not a complete Godot
parser. It does not validate property types, ExtResource IDs, script syntax, binary
.scn/.res files, runtime load/preload expressions, main-scene/project setting paths,
export presets, resource decoding, or all UID/import relationships. A present image
may still be corrupt. Unsupported URI schemes are reported unverified. Unrecognized
string escapes or malformed external declarations fail inspection conservatively.

File inspection is not an OS security boundary: concurrent filesystem changes are
not protected against. Use a stable local copy. Known exclusion names include .git,
.godot, .venv, venv, env, node_modules, __pycache__, .ruff_cache, .pytest_cache and
.mypy_cache; no custom ignore/config language is implemented.
Git branch/dirty probing is disabled in the default scanner (`git` is null in JSON).

Local verification and untested environments are listed in [VALIDATION.md](docs/VALIDATION.md).
Engine semantics and rationale are in [development notes](docs/DEVELOPMENT.md).
AI assistance is not implemented and is not needed for any check.

Please report tool version, OS, Godot version (or absent), exact command, sanitized
output and a tiny reproduction. Do not upload API keys, secrets or private game assets.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [release preparation](docs/RELEASE.md).

MIT — including the self-authored example. See [LICENSE](LICENSE).
