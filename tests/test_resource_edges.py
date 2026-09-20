import pytest

from gdguard.checks.resources import check_resource_references
from gdguard.models import Status


def scene(root, body):
    (root / "scene.tscn").write_text("[gd_scene format=3]\n" + body, encoding="utf-8")


def test_comment_and_multiline_string_are_not_declarations(tmp_path):
    scene(
        tmp_path,
        '; [ext_resource path="res://comment.tres" id="1"]\n'
        '[node name="Example" type="Node"]\n'
        'text = "res://ordinary.txt\n'
        '[ext_resource path=\\"res://inside.tres\\" id=\\"2\\"]\n"\n',
    )
    assert all(c.status is Status.PASS for c in check_resource_references(tmp_path))


@pytest.mark.parametrize("name", ["中文 空格.tres", "$theme.tres", "a%b{c}.tres", ".hidden.tres"])
def test_legal_names_are_checked_not_ignored(tmp_path, name):
    scene(tmp_path, f'[ext_resource path="res://{name}" id="1"]\n')
    results = check_resource_references(tmp_path)
    assert any(c.status is Status.FAIL for c in results)
    (tmp_path / name).write_text('[gd_resource type="Resource" format=3]\n[resource]\n')
    assert all(c.status is Status.PASS for c in check_resource_references(tmp_path))


@pytest.mark.parametrize(
    "reference,reason",
    [
        ("res://../outside.tres", "outside"),
        ("res://folder", "file"),
        ("res://a/../../outside.tres", "outside"),
    ],
)
def test_bad_target_reports_source_line_and_reason(tmp_path, reference, reason):
    (tmp_path / "folder").mkdir()
    scene(tmp_path, f'[ext_resource path="{reference}" id="1"]\n')
    failures = [c for c in check_resource_references(tmp_path) if c.status is Status.FAIL]
    assert failures
    text = str([c.to_dict() for c in failures])
    assert "scene.tscn:2" in text
    assert reference in text
    assert reason in text


def test_case_mismatch_fails_on_every_platform(tmp_path):
    (tmp_path / "Actual.tres").write_text('[gd_resource type="Resource" format=3]\n')
    scene(tmp_path, '[ext_resource path="res://actual.tres" id="1"]\n')
    assert any(c.status is Status.FAIL for c in check_resource_references(tmp_path))


@pytest.mark.parametrize(
    "declaration",
    [
        '[ext_resource path="uid://abc" id="1"]',
        '[ext_resource uid="uid://abc" path="res://moved.tres" id="1"]',
    ],
)
def test_uid_is_unverified_not_missing(tmp_path, declaration):
    scene(tmp_path, declaration + "\n")
    results = check_resource_references(tmp_path)
    assert not any(c.status is Status.FAIL for c in results)
    assert any(c.status is Status.SKIPPED for c in results)


@pytest.mark.parametrize(
    "content", ["", "garbage", '[gd_scene format=3]\n[ext_resource path="res://x']
)
def test_damaged_resource_does_not_pass(tmp_path, content):
    (tmp_path / "scene.tscn").write_text(content)
    assert any(c.status is Status.FAIL for c in check_resource_references(tmp_path))


def test_relative_reference_is_resolved_from_source(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "scene.tscn").write_text(
        '[gd_scene format=3]\n[ext_resource path="../missing.tres" id="1"]\n'
    )
    assert any(c.status is Status.FAIL for c in check_resource_references(tmp_path))


def test_failed_resource_read_does_not_validate_script_references(tmp_path):
    (tmp_path / "bad.tscn").write_bytes(b"\xff")
    results = check_resource_references(tmp_path)
    script = next(c for c in results if c.name == "script references")
    assert script.status is Status.SKIPPED


def test_multiline_declaration_and_escaped_path(tmp_path):
    name = "literal$%{x};[y].tres"
    (tmp_path / name).write_text('[gd_resource type="Resource" format=3]\n')
    scene(tmp_path, f'[ext_resource\n type="Resource"\n path="res://{name}"\n id="1"]\n')
    assert all(c.status is Status.PASS for c in check_resource_references(tmp_path))
