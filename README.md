# GDGuard

Godot-native project validation and CI checks.

GDGuard is a local CLI and CI quality gate for Godot repositories. It inspects `project.godot`, scene/resource references, scripts, obvious secrets, and optional Godot/dotnet tooling without uploading project files anywhere.

AI-assisted PR review is planned. It is not part of v0.1.0.

## Why GDGuard?

Godot repositories are more than source code.

They contain:

- GDScript / C#
- serialized scenes
- resources
- imports
- project configuration
- export configuration

Traditional code-oriented CI may miss broken `res://` references and other project-specific problems. GDGuard aims to provide a lightweight quality gate specifically for Godot repositories.

## Overview

v0.1.0 is a deterministic, fully local checker:

- Works without a Godot installation for static checks
- Works without an OpenAI / Codex API key
- Sends no telemetry
- Never uploads your project

If Godot or `dotnet` are available, GDGuard can run those extra checks. If they are not, the extra checks are marked `SKIPPED` instead of failing the project.

## Features

- Detect a Godot project from `project.godot`
- Read project name and Godot feature version when present
- Scan `.tscn` / `.tres` files for conservative `res://` references
- Report missing resources and missing script references
- Scan `.gd` files for readability
- Warn about obvious sensitive files such as `.keystore` and private keys
- Optionally run Godot headless validation
- Optionally run `dotnet build` for C# Godot projects
- Text and JSON reports
- CI-friendly exit codes

## Installation

Requires Python 3.11+.

From a clone:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

From GitHub:

```bash
python -m pip install "gdguard @ git+https://github.com/guofudamo2007-lab/gdguard.git"
```

PyPI publication is not part of this repository yet, so `pip install gdguard` only works after this package is published.

## Quick Start

```bash
cd my-godot-project
gdguard check
```

Or from any directory:

```bash
gdguard check /path/to/project
```

## CLI Usage

```text
gdguard --help
gdguard --version
gdguard check
gdguard check .
gdguard check /path/to/project
gdguard check . --format json
gdguard check . --godot /path/to/godot
gdguard check . --verbose
```

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Checks passed. Warnings are allowed. |
| 1 | One or more project checks failed. |
| 2 | GDGuard could not run: bad arguments, missing project, or an environment error. |

## Example Output

```text
GDGuard

Project:
my-game

Godot:
4.3

Checks

OK project.godot
OK script scan
OK scene resources
OK script references
-- project import
  SKIPPED -- Godot executable not found
-- Godot headless check
  SKIPPED -- Godot executable not found
OK sensitive files
-- dotnet build
  SKIPPED -- no C# project files detected

Warnings: 0
Errors: 0

Result: PASS
```

JSON mode prints only JSON to stdout:

```bash
gdguard check . --format json
```

## GitHub Actions

This repository runs Ruff and pytest on every push and pull request.

To check a Godot project in another workflow, install from this repository and run the CLI:

```yaml
- name: Install GDGuard
  run: pip install "gdguard @ git+https://github.com/guofudamo2007-lab/gdguard.git"

- name: Check Godot project
  run: gdguard check .
```

If you later publish to PyPI, the install step can become `pip install gdguard`.

A composite Action is also included:

```yaml
- uses: guofudamo2007-lab/gdguard@main
  with:
    path: .
```

## What GDGuard Checks

| Check | Default result without extra tools |
| --- | --- |
| `project.godot` exists and is readable | PASS or FAIL |
| GDScript file readability | PASS or FAIL |
| Scene/resource `res://` existence | PASS or FAIL |
| Script `res://*.gd` / `res://*.cs` existence | PASS or FAIL |
| Obvious sensitive files | WARNING, does not fail the scan |
| Godot headless load | SKIPPED if Godot is not installed |
| `dotnet build` | SKIPPED if the project is not C#, or if `dotnet` is missing |

Missing Godot is never treated as a project failure.

## Privacy

All v0.1.0 checks are local.

- No telemetry
- No cloud calls
- No OpenAI API key
- No upload of project files

Future AI review must be optional and explicit opt-in.

## Current Limitations

- Resource scanning is conservative. It looks for quoted `res://` paths in `.tscn` and `.tres` files. It is not a full Godot resource parser.
- Uncertain or interpolated paths are skipped rather than reported.
- GDScript is not parsed as a language unless Godot itself is available.
- Godot headless support depends on the installed Godot binary and uses `--headless --quit-after 1 --path <project>`.
- C# checking is a timeout-bounded `dotnet build`, not a Godot-specific analyzer.
- Git is inspected only enough to report branch and dirty state.

## Roadmap

### v0.1

- Project discovery
- Resource validation
- Godot headless validation
- JSON reports
- Basic CI integration

### v0.2

- Git diff-aware checks
- GitHub annotations
- GUT / GdUnit detection
- Export configuration checks

### v0.3

- Optional Codex-powered PR review
- Failure explanation
- Issue triage assistance

Dates are intentionally omitted.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
