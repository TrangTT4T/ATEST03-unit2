"""Layout rules for the browser tests, checked on every run (the workplace style: data, then steps).

Every ``test_*`` function in tests/test_*.py:

* has a docstring saying what it proves (shown in the reports);
* optionally starts with ``# Test data``: plain assignments only;
* then ``# Execution steps``: only ``with step("..."):`` blocks - every action and check is a
  numbered step, so a failure names the step and the Allure report reads as a step list.
"""
import ast
from pathlib import Path

import pytest

TEST_FILES = sorted((Path(__file__).resolve().parents[1]).glob("test_*.py"))


def _is_step(node: ast.stmt) -> bool:
    if not isinstance(node, ast.With) or len(node.items) != 1:
        return False
    call = node.items[0].context_expr
    return isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "step"


def layout_problems(source: str) -> list[str]:
    lines = source.splitlines()
    problems = []
    tests = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    for test in tests:
        if ast.get_docstring(test) is None:
            problems.append(f"{test.name}: no docstring")
        body = test.body[1:] if ast.get_docstring(test) is not None else test.body
        data = [n for n in body if isinstance(n, (ast.Assign, ast.AnnAssign))]
        steps = [n for n in body if _is_step(n)]
        if not steps:
            problems.append(f"{test.name}: no 'with step(...)' block")
        for node in body:
            if node not in data and node not in steps:
                problems.append(f"line {node.lineno}: {test.name}: put this statement inside a step")
        if data and steps and max(n.lineno for n in data) > steps[0].lineno:
            problems.append(f"{test.name}: test data after the first step; move it under '# Test data'")
        text = "\n".join(lines[test.lineno - 1:test.end_lineno])
        if data and "# Test data" not in text:
            problems.append(f"{test.name}: missing the '# Test data' comment")
        if steps and "# Execution steps" not in text:
            problems.append(f"{test.name}: missing the '# Execution steps' comment")
    return problems


@pytest.mark.parametrize("path", TEST_FILES, ids=lambda p: p.name)
def test_browser_tests_read_as_numbered_steps(path: Path) -> None:
    assert layout_problems(path.read_text(encoding="utf-8")) == []


def test_the_rule_catches_violations() -> None:
    sample = (
        "def test_a(shop, step):\n"  # no docstring
        "    with step('Open'):\n"
        "        shop.home.open()\n"
        "    name = 'x'\n"  # 4: data after a step
        "    shop.home.search(name)\n"  # 5: action outside a step
    )
    assert layout_problems(sample) == [
        "test_a: no docstring",
        "line 5: test_a: put this statement inside a step",
        "test_a: test data after the first step; move it under '# Test data'",
        "test_a: missing the '# Test data' comment",
        "test_a: missing the '# Execution steps' comment",
    ]


def test_the_expected_layout_passes() -> None:
    sample = (
        "def test_a(shop, step):\n"
        "    \"\"\"Searching finds the product.\"\"\"\n"
        "    # Test data\n"
        "    name = 'x'\n"
        "\n"
        "    # Execution steps\n"
        "    with step('Search'):\n"
        "        shop.home.search(name)\n"
    )
    assert layout_problems(sample) == []
