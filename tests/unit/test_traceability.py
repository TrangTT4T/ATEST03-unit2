"""Traceability: the matrix logic, the markers on the real tests, and the pytest plugin."""
import ast
import json
from pathlib import Path

import pytest

from helper_utility.traceability import (
    Requirement,
    RunResult,
    build_matrix,
    load_requirements,
    to_csv,
    to_markdown,
    untraced,
)

pytest_plugins = ["pytester"]
ROOT = Path(__file__).resolve().parents[2]
REQS = {
    "add_to_cart": Requirement("add_to_cart", "REQ-01", "Cart", "R01", "Critical"),
    "secure_login": Requirement("secure_login", "REQ-02", "Login", "R02", "High"),
    "search_products": Requirement("search_products", "REQ-03", "Search", "R03", "Medium"),
    "create_account": Requirement("create_account", "REQ-04", "Account", "R04", "Medium"),
}


def result(name, status, *marks):
    return RunResult("test_x.py", name, frozenset(marks), status)


# --- the matrix --------------------------------------------------------------------------------
def test_the_worst_test_decides():
    rows = build_matrix(REQS, [
        result("a", "passed", "add_to_cart"), result("b", "failed", "add_to_cart"),       # -> FAIL
        result("c", "passed", "secure_login"), result("d", "skipped", "secure_login"),    # -> PASS
        result("e", "skipped", "search_products", "manual"),                              # -> NOT RUN
    ])                                                                                     # create_account: NO TEST
    assert [r.status for r in rows] == ["FAIL", "PASS", "NOT RUN", "NO TEST"]


def test_a_setup_error_is_a_failure():
    assert build_matrix(REQS, [result("a", "error", "add_to_cart")])[0].status == "FAIL"


def test_reports():
    results = [result("a", "passed", "add_to_cart"), result("orphan", "passed", "smoke")]
    rows = build_matrix(REQS, results)
    assert [r.name for r in untraced(REQS, results)] == ["orphan"]
    assert "| REQ-01 | @add_to_cart | Cart | R01 | Critical | 1 | 1 | 0 | 0 | PASS |" in to_markdown(rows, [])
    assert to_csv(rows).splitlines()[1] == "REQ-01,@add_to_cart,Cart,R01,Critical,1,1,0,0,PASS"


# --- the real tests against the real registry (read from the source: no browser) ----------------
REQUIREMENTS = load_requirements(ROOT / "dataset" / "requirements.json")
TEST_FILES = sorted((ROOT / "tests").glob("test_*.py"))


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
def test_every_product_test_proves_exactly_one_requirement(test):
    assert len(TESTS[test] & REQUIREMENTS.keys()) == 1, f"mark it with one of {sorted(REQUIREMENTS)}"


def test_every_requirement_has_a_test():
    covered = set().union(*TESTS.values())
    assert sorted(REQUIREMENTS.keys() - covered) == []


# --- the plugin, end to end in a sandbox (no browser) ------------------------------------------
TESTS_IN_SANDBOX = """
import pytest

@pytest.mark.add_to_cart
def test_adding_works():
    pass

@pytest.mark.add_to_cart
def test_adding_is_broken():
    raise AssertionError("broken")

@pytest.mark.data_creating
@pytest.mark.create_account
def test_creates_a_real_account():
    pass

def test_without_requirement():
    pass
"""


@pytest.fixture
def sandbox(pytester: pytest.Pytester) -> pytest.Pytester:
    pytester.makeini(
        "[pytest]\naddopts = -p no:cacheprovider -p no:playwright --strict-markers\n"
        "markers =\n    data_creating: creates data\n"
    )
    pytester.makeconftest(f"import sys; sys.path[:0] = [{str(ROOT)!r}, {str(ROOT / 'tests')!r}]\n"
                          'pytest_plugins = ["traceability_plugin"]\n')
    (pytester.path / "dataset").mkdir()
    (pytester.path / "dataset" / "requirements.json").write_text(json.dumps({"requirements": {
        "add_to_cart": {"id": "REQ-01", "title": "Cart", "risk": "R01", "level": "Critical"},
        "create_account": {"id": "REQ-07", "title": "Account", "risk": "R06", "level": "Medium"},
        "search_products": {"id": "REQ-08", "title": "Search", "risk": "R07", "level": "Medium"},
    }}), encoding="utf-8")
    (pytester.path / "test_sandbox.py").write_text(TESTS_IN_SANDBOX, encoding="utf-8")
    return pytester


EXPECTED = [
    "REQ-01,@add_to_cart,Cart,R01,Critical,2,1,1,0,FAIL",
    "REQ-07,@create_account,Account,R06,Medium,1,0,0,1,NOT RUN",  # deselected by -m, still listed
    "REQ-08,@search_products,Search,R07,Medium,0,0,0,0,NO TEST",
]


@pytest.mark.parametrize("parallel", [[], ["-n", "2"]], ids=["serial", "xdist"])
def test_the_plugin_writes_the_matrix_including_deselected_tests(sandbox: pytest.Pytester, parallel):
    result = sandbox.runpytest_subprocess("-m", "not data_creating", *parallel)

    assert result.parseoutcomes()["passed"] == 2 and result.parseoutcomes()["failed"] == 1
    csv = (sandbox.path / "reports" / "traceability.csv").read_text(encoding="utf-8").splitlines()
    assert csv[1:] == EXPECTED
    markdown = (sandbox.path / "reports" / "traceability.md").read_text(encoding="utf-8")
    assert "test_sandbox.py: test_without_requirement" in markdown  # listed as untraced
    result.stdout.fnmatch_lines(["*Requirement traceability*", "*@add_to_cart FAIL*"])


def test_a_marker_typo_is_an_error(sandbox: pytest.Pytester):
    (sandbox.path / "test_typo.py").write_text("import pytest\n\n@pytest.mark.add_to_card\ndef test_x():\n    pass\n")
    result = sandbox.runpytest_subprocess("test_typo.py")
    result.stdout.fnmatch_lines(["*'add_to_card' not found in `markers` configuration option*"])
