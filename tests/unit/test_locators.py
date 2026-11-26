"""Locator strings -> Playwright selectors: parse_locator() in pages/base_page.py (no browser)."""
import pytest

from pages.base_page import parse_locator


@pytest.mark.parametrize("locator, selector", [
    # Playwright's own engines: passed through
    ("css=#cart", "css=#cart"),
    ("xpath=//a[contains(., 'My Cart')]", "xpath=//a[contains(., 'My Cart')]"),
    ("text=No results found for", "text=No results found for"),
    ("role=button[name='Sold Out']", "role=button[name='Sold Out']"),
    ("id=product-price", "id=product-price"),
    ("data-testid=buy", "data-testid=buy"),
    # Unit 1 (Selenium) strategies: translated, so both repositories write locators the same way
    ("name=q", "css=[name='q']"),
    ("name=customer[email]", "css=[name='customer[email]']"),
    ("tag=html", "css=html"),
    ("class=errors", "css=.errors"),
    ("link=Forgot your password?", "role=link[name='Forgot your password?' s]"),
    ("partial_link=Forgot", "role=link[name=/Forgot/]"),
    ("partial_link=your password?", "role=link[name=/your\\ password\\?/]"),
    ("partial_link=a/b", "role=link[name=/a\\/b/]"),
    ("link=Rock 'n' roll", "role=link[name='Rock \\'n\\' roll' s]"),
    # No prefix
    ("//h1", "xpath=//h1"),
    ("(//a)[1]", "xpath=(//a)[1]"),
    ("input[name='q']", "css=input[name='q']"),
])
def test_parse_locator(locator: str, selector: str) -> None:
    assert parse_locator(locator) == selector


@pytest.mark.parametrize("bad", ["", "   ", "css=", "name=", ("css", "#cart")])
def test_bad_locators_fail_loudly(bad) -> None:
    with pytest.raises(ValueError):
        parse_locator(bad)
