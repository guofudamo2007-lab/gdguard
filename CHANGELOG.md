# Changelog

## 0.2.0rc1 — Unreleased candidate

### Changed
- Default checks are static and start no external commands, even if Godot/dotnet
  are installed. Opt in independently with --import, --headless, --dotnet-build.
  --godot alone selects a path without running it.
- Explicit missing tools/build targets and launch errors now fail (exit 1);
  unrequested checks remain SKIPPED. The top-level result/exit-code schema is retained.
- Add report scope and text skipped counts; print explanations for passed checks.
  GDScript readability and one-iteration smoke results no longer imply syntax/all-game validation.
- Default Git probing is disabled; the compatible JSON git field is null.
- Resource scanning reads external declarations instead of arbitrary quoted res://
  strings; includes source line, relative paths, exact case and project boundary checks.
  Literal dollar/percent/brace/dot filenames are no longer silently ignored.
- Child links/junctions are rejected; unreadable, invalid UTF-8, NUL, truncated
  declarations and traversal failures no longer silently pass.
- UID resolution and unsupported schemes are explicitly unverified. A stale fallback
  with a UID is not asserted to be a definitely missing engine resource.

### Fixed
- Replace the tool-existence-only project import PASS with a real opt-in import command.
- Catch subprocess.TimeoutExpired and report recognized zero-exit engine/build errors.
- Sensitive-file sampling is bounded and reports read failures; no claim of Git tracking.
- Repair corrupt self-authored 1x1 PNG fixture (checksum/compressed stream).
- Pass Action inputs via environment variables, install the Action checkout, and
  isolate module loading from project paths.

### Added
- Safety, parser, CLI, timeout, scope and filesystem regression tests.
- Real temporary-copy CLI demonstration: healthy -> missing texture -> restored.
- Windows/Linux static CI matrix, distribution builds/clean installation checks,
  Action exit propagation checks and a separate opt-in Godot integration test.
- Release and external trial checklists. No release, PyPI upload or outreach performed.

## 0.1.0 — Initial local implementation

Project detection, resource/reference scans, GDScript readability, sensitive-file
warnings, Godot/dotnet command support, text/JSON reports and initial Python tests.
This entry records the prior source baseline, not a claim of a published release.
