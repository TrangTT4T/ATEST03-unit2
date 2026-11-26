"""Markers on the real tests: every browser test proves exactly one requirement, no typos.

Read from the source (no browser). --strict-markers in pytest.ini rejects an undeclared marker; these
tests keep pytest.ini and dataset/requirements.json (the Unit 1 requirements) in step.
"""
import ast
import configparser
import json
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]
ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = json.loads((ROOT / "dataset" / "requirements.json").read_text(encoding="utf-8"))["requirements"]
TEST_FILES = sorted((ROOT / "tests").glob("test_*.py"))


def _declared_markers() -> set:
    ini = configparser.ConfigParser()
    ini.read(ROOT / "pytest.ini", encoding="utf-8")
    return {line.split(":")[0].strip() for line in ini["pytest"]["markers"].strip().splitlines()}


def _marker_names(nodes: list) -> set:
    names = set()
    for node in nodes:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Attribute) and sub.value.attr == "mark":
                names.add(sub.attr)
    return names


def _tests_and_markers():
    for path in TEST_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module_marks = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "pytestmark" for t in node.targets):
                module_marks |= _marker_names([node.value])
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                yield f"{path.name}::{node.name}", module_marks | _marker_names(node.decorator_list)


TESTS = dict(_tests_and_markers())


@pytest.mark.parametrize("test", sorted(TESTS))
def test_every_browser_test_proves_exactly_one_requirement(test):
    assert len(TESTS[test] & REQUIREMENTS.keys()) == 1, f"mark it with one of {sorted(REQUIREMENTS)}"


def test_every_requirement_has_a_test():
    covered = set().union(*TESTS.values())
    assert sorted(REQUIREMENTS.keys() - covered) == []


def test_every_requirement_marker_is_declared_in_pytest_ini():
    assert sorted(REQUIREMENTS.keys() - _declared_markers()) == [], "add it under markers in pytest.ini"


def test_a_marker_typo_is_an_error(pytester: pytest.Pytester):
    pytester.makeini("[pytest]\naddopts = -p no:cacheprovider -p no:playwright --strict-markers\n")
    pytester.makepyfile("import pytest\n\n@pytest.mark.add_to_card\ndef test_x():\n    pass\n")
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*'add_to_card' not found in `markers` configuration option*"])

