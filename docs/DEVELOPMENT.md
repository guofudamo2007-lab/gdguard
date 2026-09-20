# Check semantics and implementation boundaries

The current scope is Godot 4 text external-resource declarations, not a complete parser.
The compatibility reference used for this change is **Godot 4.4 documentation**;
consulting documentation is not real-engine integration verification.

- [TSCN format](https://docs.godotengine.org/en/4.4/contributing/development/file_formats/tscn.html):
  external resources declare paths; paths relative to the source are valid as well as
  res:// paths. The scanner masks strings/comments before locating headers so quoted
  prose cannot become a declaration. Property values are not generally parsed.
- [ResourceUID](https://docs.godotengine.org/en/4.4/classes/class_resourceuid.html):
  UID mappings can survive moves/renames. GDGuard does not resolve them. An existing
  fallback path proves only that path exists; a missing fallback with UID stays unverified.
- [Filesystem](https://docs.godotengine.org/en/4.4/tutorials/scripting/filesystem.html)
  and [troubleshooting](https://docs.godotengine.org/en/4.4/tutorials/troubleshooting.html):
  host filesystem case behavior can differ from the exported PCK. GDGuard intentionally
  enforces exact spelling on all hosts as a portability gate, even if a Windows editor
  could open the differently cased file.
- [Command-line interface](https://docs.godotengine.org/en/4.4/tutorials/editor/command_line_tutorial.html):
  --import waits for editor imports and exits; --quit-after limits main-loop iterations.
  Neither implies whole-game validation. A Godot editor binary is required for import.

Paths are normalized within the selected root. Links/junctions are conservatively
rejected, including links to internal files. No external content is read. This is a
stable-filesystem policy, not a race-proof sandbox. Ignored cache/venv directories
are not enumerated. Traversal errors block a scan rather than implying completeness.

The existing result string and exit-code interface are preserved. Scope/skipped details
are additive. Requesting a dynamic check which cannot execute deliberately yields FAIL,
with executed=false where known, so an explicit CI gate cannot silently downgrade.

Initial baseline: clean Git checkout, 22 tests passed, Ruff lint passed, one existing
format failure in test_scan.py. Defects were reproduced before fixing. Four legacy
expectations were updated because the requested behavior changed: unrequested checks
now explain opt-in, requested missing Godot fails, and dollar filenames are literal.

Runtime dependencies remain empty. The existing package/modules are retained.
The version advances to 0.2.0rc1 because safer defaults and stricter resource handling
are observable behavior changes. It is a local candidate, not an existing release.

