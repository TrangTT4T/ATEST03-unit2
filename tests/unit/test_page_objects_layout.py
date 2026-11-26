"""Layout rules for page objects, checked on every run.

* one class per file in pages/;
* its methods are grouped under ``####`` banners, each naming its area with ``# Scope: ...``;
* every public method and property has a docstring;
* its selectors are declared at the BOTTOM of the class, after the last method;
* methods never write a selector inline (no string literal passed to locator(), no get_by_*()).
"""
import ast
import re
from pathlib import Path

import pytest

BANNER = re.compile(r"^\s*#{20,}\n\s*# .+\n\s*# Scope: .+\n\s*#{20,}$", re.MULTILINE)
PAGES = sorted(p for p in (Path(__file__).resolve().parents[2] / "pages").glob("*.py") if p.name != "__init__.py")


def layout_problems(source: str) -> list[str]:
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    problems = [] if len(classes) == 1 else [f"{len(classes)} classes; a page file holds exactly one"]
    lines = source.splitlines()
    for cls in classes:
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
        if methods and not BANNER.search("\n".join(lines[cls.lineno - 1:cls.end_lineno])):
            problems.append(f"{cls.name}: no '####' banner with '# Scope: ...' above its methods")
        for method in methods:
            if not method.name.startswith("_") and ast.get_docstring(method) is None:
                problems.append(f"line {method.lineno}: {cls.name}.{method.name} has no docstring")
        last_method = max((m.end_lineno for m in methods), default=cls.lineno)
        for node in cls.body:
            is_locator = isinstance(node, ast.Assign) and all(
                isinstance(t, ast.Name) and t.id.startswith("_") for t in node.targets
            )
            if is_locator and node.lineno < last_method:
                problems.append(f"line {node.lineno}: selector above a method; move it to the bottom")
        for method in methods:
            for call in (n for n in ast.walk(method) if isinstance(n, ast.Call)):
                name = call.func.attr if isinstance(call.func, ast.Attribute) else ""
                literal = bool(call.args) and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str)
                if name.startswith("get_by_") or (name == "locator" and literal):
                    problems.append(f"line {call.lineno}: selector written inline in {cls.name}.{method.name}")
    return problems


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_file_layout(path: Path) -> None:
    assert layout_problems(path.read_text(encoding="utf-8")) == []


def test_the_rule_catches_violations() -> None:
    sample = (
        "class A:\n"
        "    _title = 'h1'\n"  # 2: above a method
        "    def read(self):\n"  # 3: no docstring; and no banner in the class
        "        return self.page.locator('#x')\n"  # 4: inline selector
        "class B:\n"  # second class
        "    pass\n"
    )
    problems = layout_problems(sample)
    assert problems[0] == "2 classes; a page file holds exactly one"
    assert problems[1] == "A: no '####' banner with '# Scope: ...' above its methods"
    assert [p.split(":")[0] for p in problems[2:]] == ["line 3", "line 2", "line 4"]


def test_a_banner_and_docstrings_satisfy_the_rule() -> None:
    sample = (
        "class A:\n"
        "    ######################################################\n"
        "    # Header methods\n"
        "    # Scope: Every page > Header\n"
        "    ######################################################\n"
        "    def read(self):\n"
        "        \"\"\"Read the title.\"\"\"\n"
        "        return self.page.locator(self._title)\n"
        "\n"
        "    # --- Locators ---\n"
        "    _title = 'h1'\n"
    )
    assert layout_problems(sample) == []
