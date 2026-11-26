"""Base Page Object (Playwright, sync API).

Locator strategy (Day 5): role/label/text first, then stable attributes (name, form action).
No sleeps: Playwright auto-waits on actions and `expect()` retries assertions.

Layout of every page object (one class per file), checked by tests/unit/test_page_objects_layout.py:

* methods grouped under ``####`` banners that name the area of the page (``# Scope: ...``);
* a docstring on every public method and property;
* a ``# --- Locators ---`` section at the BOTTOM of the class. Methods use those names; a selector
  that depends on data is a template filled with ``.format(...)``. No selector is written inline.
"""
import re

from playwright.sync_api import Locator, Page

MONEY = re.compile(r"£\s?([\d,]+\.\d{2})")


def money_to_float(text: str) -> float:
    """'£1,120.00' -> 1120.0"""
    match = MONEY.search(text)
    if not match:
        raise ValueError(f"No £ amount found in: {text!r}")
    return float(match.group(1).replace(",", ""))


class BasePage:
    path = "/"

    def __init__(self, page: Page):
        self.page = page

    ############################################################################
    # Navigation methods
    # Scope: Every page
    ############################################################################
    def open(self, path: str | None = None):
        """Go to ``path`` (default: this page's own path) on the store."""
        # Relative URL: pytest-playwright gives every context the --base-url.
        self.page.goto(path or self.path)
        return self

    def submit(self, button: Locator):
        """Click a form button and wait for the resulting navigation to finish.

        wait_for_load_state() alone returns at once (the old page is already loaded), so the next
        goto() could cancel the POST. Unit 1 hit this as findings F7/F8; both units now wait here.
        """
        with self.page.expect_navigation(wait_until="domcontentloaded"):
            button.click()

    ############################################################################
    # Header methods
    # Scope: Every page > Header (mini-cart, search box)
    ############################################################################
    @property
    def mini_cart(self) -> Locator:
        """The header link "My Cart (N)"."""
        return self.page.locator(self._mini_cart).first

    def mini_cart_count(self) -> int:
        """N in "My Cart (N)", read now (use expect() to wait for a change)."""
        return int(re.search(r"\((\d+)\)", self.mini_cart.inner_text()).group(1))

    @property
    def search_box(self) -> Locator:
        """The header search box."""
        return self.page.locator(self._search_box).first

    def search(self, keyword: str):
        """Search for ``keyword`` and wait for the results page."""
        self.search_box.fill(keyword)
        self.search_box.press("Enter")
        self.page.wait_for_url(re.compile(r"/search"))
        return self

    # --- Locators -------------------------------------------------------------
    # Header (on every page)
    _mini_cart = r"role=link[name=/My Cart \(\d+\)/]"
    _search_box = "input[name='q']"
