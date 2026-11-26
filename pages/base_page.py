"""Base Page Object (Playwright, sync API): navigation and the custom element methods every page uses.

Locators are STRINGS with a strategy prefix, the same syntax as the Unit 1 (Selenium) repository:

    _search_box = "name=q"
    _mini_cart  = r"role=link[name=/My Cart \\(\\d+\\)/]"
    _tile       = "css=a[href*='/products/{handle}']"      # a template, filled with locator()

``parse_locator()`` below turns the string into a Playwright selector. Prefixes:

* Playwright's own engines, passed through: css, xpath, text, role, id, data-testid;
* Unit 1 strategies, translated: name -> css=[name='...'], tag -> css=..., class -> css=.<class>,
  link -> role=link[name='...' s] (exact), partial_link -> role=link[name=/.../] (contains);
* no prefix: a value starting with "//", "(/" or "./" is XPath, anything else is CSS.

Pages never call ``self.page.locator``, ``goto`` or ``expect_*`` themselves: they pass locator strings
to the BasePage methods, which log the action and fail with a message that names the locator.
Playwright waits on every action; checks use ``expect()`` (retries until the timeout), so nothing
here sleeps for a fixed time.

Layout of every page object (one class per file), checked by tests/unit/test_page_objects_layout.py:

* methods grouped under ``####`` banners that name the area of the page (``# Scope: ...``);
* a docstring on every public method and property;
* a ``# --- Locators ---`` section at the BOTTOM of the class, with locator strings only.
"""
import logging
import re
from collections.abc import Callable

from playwright.sync_api import Locator, Page, Response, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

MONEY = re.compile(r"£\s?([\d,]+\.\d{2})")


def parse_locator(locator: str) -> str:
    """'name=q' -> "css=[name='q']";  '//h1' -> 'xpath=//h1';  'css=#cart' -> 'css=#cart'

    :param locator: a locator string, with or without a strategy prefix
    :return: a Playwright selector
    """

    def quoted(text: str) -> str:
        return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"

    def regex(text: str) -> str:
        return re.escape(text).replace("/", "\\/")

    playwright_engines = ("css", "xpath", "text", "role", "id", "data-testid")  # passed through
    unit1_strategies: dict[str, Callable[[str], str]] = {  # translated to a Playwright selector
        "name": lambda v: f"css=[name={quoted(v)}]",
        "tag": lambda v: f"css={v}",
        "class": lambda v: f"css=.{v}",
        "link": lambda v: f"role=link[name={quoted(v)} s]",  # exact
        "partial_link": lambda v: f"role=link[name=/{regex(v)}/]",  # contains, case-sensitive
    }
    if not isinstance(locator, str) or not locator.strip():
        raise ValueError(f"A locator is a non-empty string such as 'css=#cart', got {locator!r}")
    prefix, separator, value = locator.partition("=")
    prefix = prefix.strip()
    if separator and (prefix in playwright_engines or prefix in unit1_strategies):
        if not value.strip():
            raise ValueError(f"Locator {locator!r} has a strategy but no value")
        return f"{prefix}={value.strip()}" if prefix in playwright_engines else unit1_strategies[prefix](value.strip())
    if locator.startswith(("//", "(/", "./")):
        return f"xpath={locator}"
    return f"css={locator}"


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
        self.logger = logging.getLogger(type(self).__name__)  # in the report of a failed test

    ############################################################################
    # Navigation methods
    # Scope: Every page
    ############################################################################
    def open(self, path: str | None = None):
        """Go to ``path`` (default: this page's own path) on the store.

        :param path: path after the base URL, e.g. "/cart"
        :return: this page, for chaining
        """
        self.logger.info("Open %s", path or self.path)
        self.page.goto(path or self.path)  # relative: pytest-playwright gives every context the --base-url
        return self

    @property
    def url(self) -> str:
        """The current URL."""
        return self.page.url

    def wait_for_url_contains(self, fragment: str, timeout: float | None = None):
        """Wait until the URL contains ``fragment``.

        :param fragment: text the URL must contain, e.g. "/search"
        :param timeout: seconds; default is Playwright's (30 s for navigation)
        :return: this page
        """
        self.page.wait_for_url(re.compile(re.escape(fragment)), timeout=_ms(timeout))
        return self

    ############################################################################
    # Locator methods
    # Scope: Every page > locator strings -> Playwright locators
    ############################################################################
    @staticmethod
    def locator(template: str, **values) -> str:
        """Fill a locator template: ``locator(self._tile, handle="grey-jacket")``.

        :param template: locator string with ``{name}`` fields
        :return: the locator string with the fields filled in
        """
        return template.format(**values)

    def find_element(self, *locators: "str | Locator", first: bool = False) -> Locator:
        """The element(s) of ``locators``; several locators are chained, each inside the previous one.

        Playwright locators are lazy: nothing is searched until an action or expect() uses it, and
        then it waits. ``find_element(self._root, self._update_button)`` = the update button INSIDE
        the cart form. The first item may be a Locator (a scope that a string cannot express, e.g. a
        row found with ``filter(has=...)``); the others are locator strings.

        :param locators: a scope Locator and/or locator strings
        :param first: take the first match (several matches are otherwise an error on actions)
        :return: a Playwright Locator
        """
        if not locators:
            raise ValueError("find_element needs at least one locator")
        head, *inner = locators
        element = head if isinstance(head, Locator) else self.page.locator(parse_locator(head))
        for selector in inner:
            element = element.locator(parse_locator(selector))
        return element.first if first else element

    def count_elements(self, *locators: "str | Locator") -> int:
        """How many elements match right now (no wait; 0 is a valid answer)."""
        return self.find_element(*locators).count()

    def is_element_present(self, *locators: "str | Locator") -> bool:
        """True when at least one element matches right now (no wait)."""
        return self.count_elements(*locators) > 0

    ############################################################################
    # Action methods
    # Scope: Every page > click, type, submit
    ############################################################################
    def click_element(self, *locators: "str | Locator"):
        """Click the element; Playwright first waits until it is visible, stable and enabled.

        :param locators: locator string(s), chained as in find_element
        :return: this page
        """
        self.logger.info("Click %s", _describe(locators))
        self.find_element(*locators, first=True).click()
        return self

    def click_and_wait_for_new_page(self, *locators: "str | Locator"):
        """Click a form button and wait for the resulting navigation to finish.

        wait_for_load_state() alone returns at once (the old page is already loaded), so the next
        goto() could cancel the POST. Unit 1 hit this as findings F7/F8; both units wait here.

        :param locators: locator string(s) of the submit button
        :return: this page
        """
        with self.page.expect_navigation(wait_until="domcontentloaded"):
            self.click_element(*locators)
        return self

    def click_and_wait_for_response(self, *locators: "str | Locator", url_part: str, method: str = "POST") -> Response:
        """Click and wait for the server's answer to the request this click sends (Day 6: network-aware wait).

        :param locators: locator string(s) of the element to click
        :param url_part: part of the request URL, e.g. "/cart/add"
        :param method: HTTP method of that request
        :return: the Playwright Response
        """
        with self.page.expect_response(lambda r: url_part in r.url and r.request.method == method) as answer:
            self.click_element(*locators)
        self.logger.info("%s %s -> HTTP %s", method, url_part, answer.value.status)
        return answer.value

    def type_text(self, *locators: "str | Locator", text: str, secret: bool = False):
        """Replace the field's text with ``text``.

        :param locators: locator string(s) of the input
        :param text: text to type
        :param secret: a password: the log shows *** instead of the text
        :return: this page
        """
        self.logger.info("Type %r into %s", "***" if secret else text, _describe(locators))
        self.find_element(*locators, first=True).fill(text)
        return self

    def press_enter(self, *locators: "str | Locator"):
        """Press Enter in a field (e.g. submit a search)."""
        self.find_element(*locators, first=True).press("Enter")
        return self

    ############################################################################
    # Read and state methods
    # Scope: Every page > element text and state
    ############################################################################
    def get_text(self, *locators: "str | Locator") -> str:
        """Visible text of the element (waits for it)."""
        return self.find_element(*locators, first=True).inner_text()

    def get_input_value(self, *locators: "str | Locator") -> str:
        """Current value of an input (waits for it)."""
        return self.find_element(*locators, first=True).input_value()

    def is_element_visible(self, *locators: "str | Locator", timeout: float = 0) -> bool:
        """True when the element is visible, waiting up to ``timeout`` seconds (0: check now).

        :param locators: locator string(s)
        :param timeout: seconds to wait for the state; never a fixed sleep
        :return: True or False, never an exception
        """
        element = self.find_element(*locators, first=True)
        if not timeout:
            return element.is_visible()
        try:
            element.wait_for(state="visible", timeout=_ms(timeout))
        except PlaywrightTimeoutError:
            self.logger.info("Element %s is not visible", _describe(locators))
            return False
        return True

    def is_element_enabled(self, *locators: "str | Locator", timeout: float = 0) -> bool:
        """True when the element exists and is enabled, waiting up to ``timeout`` seconds (0: check now).

        :param locators: locator string(s)
        :param timeout: seconds to wait for the state; never a fixed sleep
        :return: True or False, never an exception
        """
        try:
            expect(self.find_element(*locators, first=True)).to_be_enabled(timeout=_ms(timeout) or 1)
        except AssertionError:
            self.logger.info("Element %s is disabled or missing", _describe(locators))
            return False
        return True

    ############################################################################
    # Check methods (raise AssertionError, retrying until the expect timeout)
    # Scope: Every page > element state
    ############################################################################
    def element_should_be_visible(self, *locators: "str | Locator", error_msg: str | None = None):
        """Fail unless the element becomes visible.

        :param locators: locator string(s)
        :param error_msg: message to fail with; default names the locator
        :return: this page
        """
        message = error_msg or f"Element {_describe(locators)!r} is not visible"
        expect(self.find_element(*locators, first=True), message).to_be_visible()
        return self

    def element_should_be_disabled(self, *locators: "str | Locator", error_msg: str | None = None):
        """Fail unless the element is (or becomes) disabled."""
        message = error_msg or f"Element {_describe(locators)!r} is not disabled"
        expect(self.find_element(*locators, first=True), message).to_be_disabled()
        return self

    def element_should_contain_text(self, *locators: "str | Locator", text: str, error_msg: str | None = None):
        """Fail unless the element's text contains ``text``."""
        message = error_msg or f"Element {_describe(locators)!r} does not contain {text!r}"
        expect(self.find_element(*locators, first=True), message).to_contain_text(text)
        return self

    def element_should_have_count(self, *locators: "str | Locator", count: int, error_msg: str | None = None):
        """Fail unless exactly ``count`` elements match."""
        message = error_msg or f"Expected {count} element(s) {_describe(locators)!r}"
        expect(self.find_element(*locators), message).to_have_count(count)
        return self

    ############################################################################
    # Header methods
    # Scope: Every page > Header (mini-cart, search box)
    ############################################################################
    @property
    def mini_cart(self) -> Locator:
        """The header link "My Cart (N)"."""
        return self.find_element(self._mini_cart, first=True)

    def mini_cart_count(self) -> int:
        """N in "My Cart (N)", read now (use expect() to wait for a change)."""
        return int(re.search(r"\((\d+)\)", self.get_text(self._mini_cart)).group(1))

    @property
    def search_box(self) -> Locator:
        """The header search box."""
        return self.find_element(self._search_box, first=True)

    def search(self, keyword: str):
        """Search for ``keyword`` and wait for the results page."""
        self.type_text(self._search_box, text=keyword)
        self.press_enter(self._search_box)
        self.wait_for_url_contains("/search")
        return self

    # --- Locators -------------------------------------------------------------
    # Header (on every page)
    _mini_cart = r"role=link[name=/My Cart \(\d+\)/]"
    _search_box = "name=q"


def _describe(locators) -> str:
    """Locators as one readable string for logs and error messages."""
    return " >> ".join(item if isinstance(item, str) else "<scope>" for item in locators)


def _ms(seconds: float | None) -> float | None:
    """Seconds (the unit of every timeout here, as in Unit 1) -> Playwright milliseconds."""
    return None if seconds is None else seconds * 1000
