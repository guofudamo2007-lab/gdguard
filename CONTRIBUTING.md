# Contributing

Use Python 3.11+ in a virtual environment:

```sh
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest -m "not godot"
python scripts/demo.py
python -m build
python scripts/verify_distribution.py
```

Add a minimal failing regression before fixing a bug. Keep runtime dependencies small
and static scans independent of paid services and engine execution. Use only
self-authored or clearly licensed fixtures. Tests must preserve the original fixtures.

Command simulations test dispatch/error handling; they do not establish Godot integration.
For real engine testing, explicitly set GDGUARD_TEST_GODOT to a trusted binary, then
run `python -m pytest -m godot -v`. Only the temporary copy of our fixture is executed.
Without that variable the engine test is SKIPPED. Do not enable it for untrusted projects.
Record the actual engine version and platform with results.

For a bug report include GDGuard/OS/Godot versions, exact command, sanitized output,
expected result and a tiny reproduction. Never attach secrets, API keys, private
story/character content, or a full private game. Reduce a confirmed bug into a regression
test; keep real external reports separate from self-authored demonstrations.

See [development rationale](docs/DEVELOPMENT.md) and [release checklist](docs/RELEASE.md).
