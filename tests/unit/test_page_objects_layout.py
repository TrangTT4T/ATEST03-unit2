"""Layout rules for page objects, checked on every run.

* one class per file in pages/, and NOTHING outside it: only the docstring, imports and that class
  (a helper function or constant at module level belongs inside the class, e.g. BasePage.money_to_float);
* its methods are grouped under ``####`` banners, each naming its area with ``# Scope: ...``;
* every public method and property has a docstring;
* its locators are declared at the BOTTOM of the class, after the last method, as locator STRINGS
  that Helper.by_locator() accepts (plain XPath such as "//*[@id='cart']", or "id=...", "name=..." ...);
* methods never write a selector inline (no string literal passed to locator(), no get_by_*());
* only BasePage talks to the Playwright page (``self.page``): every other page uses the BasePage
  methods (find_element, click_element, type_text, click_and_wait_for_new_page ...).
"""
import ast
import re
from pathlib import Path

import pytest

from helper_utility.helpers import Helper

BANNER = re.compile(r"^\s*#{20,}\n\s*# .+\n\s*# Scope: .+\n\s*#{20,}$", re.MULTILINE)
PAGES = sorted(p for p in (Path(__file__).resolve().parents[2] / "pages").glob("*.py") if p.name != "__init__.py")


def layout_problems(source: str, is_base_page: bool = False) -> list[str]:
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    problems = [] if len(classes) == 1 else [f"{len(classes)} classes; a page file holds exactly one"]
    for node in tree.body:
        is_docstring = isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        if not (is_docstring or isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef))):
            problems.append(f"line {node.lineno}: code outside the class; put it inside the page class")
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
            if not is_locator:
                continue
            if node.lineno < last_method:
                problems.append(f"line {node.lineno}: selector above a method; move it to the bottom")
            if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                problems.append(f"line {node.lineno}: a locator is a string such as 'css=...'")
            else:
                try:
                    Helper().by_locator(node.value.value)
                except ValueError as error:
                    problems.append(f"line {node.lineno}: {error}")
        for method in methods:
            for call in (n for n in ast.walk(method) if isinstance(n, ast.Call)):
                name = call.func.attr if isinstance(call.func, ast.Attribute) else ""
                literal = bool(call.args) and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str)
                if name.startswith("get_by_") or (name == "locator" and literal):
                    problems.append(f"line {call.lineno}: selector written inline in {cls.name}.{method.name}")
            if not is_base_page:
                for node in ast.walk(method):
                    if (isinstance(node, ast.Attribute) and node.attr == "page"
                            and isinstance(node.value, ast.Name) and node.value.id == "self"):
                        problems.append(f"line {node.lineno}: self.page in {cls.name}.{method.name}; "
                                        "use the BasePage methods")
    return problems


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_file_layout(path: Path) -> None:
    assert layout_problems(path.read_text(encoding="utf-8"), is_base_page=path.name == "base_page.py") == []


def test_the_rule_catches_violations() -> None:
    sample = (
        "class A:\n"
        "    _title = ('css', 'h1')\n"  # 2: above a method, and a tuple
        "    def read(self):\n"  # 3: no docstring; and no banner in the class
        "        return self.page.locator('#x')\n"  # 4: inline selector, self.page
        "class B:\n"  # second class
        "    pass\n"
        "def money_to_float(text):\n"  # 7: a helper outside the class
        "    return 1.0\n"
        "TOTAL = 1\n"  # 9: a constant outside the class
    )
    assert layout_problems(sample) == [
        "2 classes; a page file holds exactly one",
        "line 7: code outside the class; put it inside the page class",
        "line 9: code outside the class; put it inside the page class",
        "A: no '####' banner with '# Scope: ...' above its methods",
        "line 3: A.read has no docstring",
        "line 2: selector above a method; move it to the bottom",
        "line 2: a locator is a string such as 'css=...'",
        "line 4: selector written inline in A.read",
        "line 4: self.page in A.read; use the BasePage methods",
    ]


def test_a_banner_and_docstrings_satisfy_the_rule() -> None:
    sample = (
        "class A:\n"
        "    ######################################################\n"
        "    # Header methods\n"
        "    # Scope: Every page > Header\n"
        "    ######################################################\n"
        "    def read(self):\n"
        "        \"\"\"Read the title.\"\"\"\n"
        "        return self.find_element(self._title)\n"
        "\n"
        "    # --- Locators ---\n"
        "    _title = \"css=[itemprop='name']\"\n"
    )
    assert layout_problems(sample) == []
