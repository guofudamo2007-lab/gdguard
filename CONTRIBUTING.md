# Contributing

GDGuard is a small Python CLI. Keep changes deterministic, local, and low-false-positive.

## Setup

Python 3.11+ is required.

```bash
python -m pip install -e ".[dev]"
```

## Tests

```bash
pytest
```

Static checks must pass without a Godot binary. Do not add tests that require a local Godot install unless they are mocked or clearly optional.

## Lint

```bash
ruff check .
```

Optional format:

```bash
ruff format .
```

## Project layout

- `src/gdguard/` CLI, models, scanner, reporters
- `src/gdguard/checks/` individual checks
- `tests/fixtures/` tiny Godot projects used by tests

Checkers return structured `CheckResult` values. They should not print.

## Pull requests

1. Open an issue if the change is large.
2. Keep the diff focused.
3. Add or update tests for behavior changes.
4. Fill in the pull request template.

Do not add telemetry, network calls, or required API keys.
