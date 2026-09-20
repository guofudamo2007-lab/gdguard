# Release and trial checklist

Candidate: 0.2.0rc1. Nothing in this checklist publishes automatically.

## Before publishing

- [ ] Review git diff/status, code and privacy; confirm version agrees in pyproject.toml
      and src/gdguard/__init__.py and changelog matches the final changes.
- [ ] Run lint, formatting, pytest, demo, build and clean install commands in CONTRIBUTING.
- [ ] Review Windows/Linux remote CI results for the exact commit after an authorized push.
- [ ] Run the opt-in Godot test with a real supported editor and record OS/version/output.
      Decide/document actual tested engine versions; documentation references are not evidence.
- [ ] Validate real links on Linux or a permitted Windows host; record genuine skips.
- [ ] Have a developer try a sanitized real project, including false-positive review.
- [ ] Review wheel/sdist contents and README metadata.
- [ ] Obtain explicit authorization for the intended remote operations. Local validation
      alone does not authorize push, tags, Releases, settings changes or PyPI uploads.

## Future commands (do not run until approved)

From a reviewed source checkout in the activated environment:

```sh
python -m build
python scripts/verify_distribution.py
python -m pip install twine
python -m twine check dist/gdguard-0.2.0rc1-py3-none-any.whl dist/gdguard-0.2.0rc1.tar.gz
```

After review, commit the intended files using explicit git add paths. For an approved
commit, publishing commands are:

```sh
git tag -a v0.2.0rc1 -m "GDGuard 0.2.0rc1"
git push origin HEAD
git push origin v0.2.0rc1
gh release create v0.2.0rc1 --verify-tag --prerelease --title "GDGuard 0.2.0rc1" --notes-file CHANGELOG.md dist/gdguard-0.2.0rc1-py3-none-any.whl dist/gdguard-0.2.0rc1.tar.gz
python -m twine upload dist/gdguard-0.2.0rc1-py3-none-any.whl dist/gdguard-0.2.0rc1.tar.gz
```

Confirm PyPI project ownership/name availability and credentials separately. Only run
the destinations actually approved; a GitHub prerelease does not require a PyPI upload.
These tag/artifact names describe the prepared candidate, not existing remote assets.

## Real developer trial

Invite a willing Godot developer after P0/P1 validation. Supply a reviewed revision and
the clone installation steps. Ask them to run `gdguard --version`,
`gdguard check "/path/to/project" --format json`, and optionally our demo.
Keep their project local; dynamic checks need a separate conscious opt-in.

Collect OS, Godot/tool versions, exact command, sanitized diagnostic excerpts, skipped
reasons, expected/actual behavior and consent for any public attribution. Turn confirmed
false positives/negatives into a self-contained licensed fixture and failing regression.
Record date, revision, real report/issue link and reproduction/fix outcome; do not invent
users, downloads or adoption counts.

Invitation draft (not sent):
> Would you try GDGuard's local static resource checker on a Godot project? It needs no
> API key and does not upload your files. I would value sanitized false-positive/negative
> reports, your tool/OS versions and a tiny public-safe reproduction.

中文草稿（未发送）：
> 想邀请你试用 GDGuard 的本地 Godot 资源检查。默认不执行游戏、不需要 API Key，
> 也不上传项目。希望收集脱敏的误报/漏报、版本与系统信息，以及可公开的最小复现。

Evidence for a future Codex for OSS application: repository code, reproducible tests,
local demo and package validation are engineering evidence. External trials, useful
bug reports, fixes validated by others, reviewed CI runs and sustained maintenance still
need real records. There is no funding guarantee. AI review remains unimplemented.

