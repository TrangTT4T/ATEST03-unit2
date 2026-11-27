"""Base Page Object (Playwright, sync API): navigation and the custom element methods every page uses.

Locators are plain XPath strings that describe the element, grouped under a comment that names the
area of the page, at the bottom of each class (the same layout as Unit 1):

    # Cart table
    _cart_form = "//*[@id='cart']"
    # Product tiles
    _tile = "//a[contains(@href,'/products/{}')]"   # a template: self._tile.format(path_name)

``Helper.by_locator()`` (helper_utility/helpers.py) turns a locator into a Playwright selector:
plain XPath by default, or "id=...", "name=...", "css=..." when needed.

Pages never call ``self.page.locator``, ``goto`` or ``expect_*`` themselves: they call the BasePage
methods, which log the action and name the locator in their errors. Playwright waits on every action
and ``expect()`` retries, so nothing here sleeps for a fixed time.

Layout of every page object (one class per file), checked by tests/unit/test_page_objects_layout.py:

* methods grouped under ``####`` banners that name the area of the page (``# Scope: ...``);
* a docstring on every public method and property;
* a ``# --- Locators ---`` section at the BOTTOM of the class: XPath strings, grouped by area.
"""
import logging
import re

from playwright.sync_api import Locator, Page, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from helper_utility.helpers import Helper


class BasePage:
    path = "/"
    MONEY_PATTERN = re.compile(r"£\s?([\d,]+\.\d{2})")  # a text pattern, not a locator

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(type(self).__name__)  # in the report of a failed test
        self._helper = Helper()  # reads locators: locator string -> Playwright selector

    ############################################################################
    # Data helpers (no browser needed)
    # Scope: Every page > prices
    ############################################################################
    @staticmethod
    def money_to_float(text: str) -> float:
        """'£1,120.00' -> 1120.0

        :param text: any text with one £ amount in it
        :return: the amount as a float
        """
        match = BasePage.MONEY_PATTERN.search(text)
        if not match:
            raise ValueError(f"No £ amount found in: {text!r}")
        return float(match.group(1).replace(",", ""))

    ############################################################################
    # Navigation methods
    # Scope: Every page
    ############################################################################
    def open_page(self, path: str | None = None):
        """Go to ``path`` on the store (default: this page's own path).

        :param path: path after the base URL, e.g. "/cart"
        """
        self.logger.info("Open %s", path or self.path)
        self.page.goto(path or self.path)  # relative: pytest-playwright gives every context the --base-url

    def wait_until_url_contains(self, fragment: str):
        """Wait until the address contains ``fragment``, for example "/search"."""
        self.page.wait_for_url(re.compile(re.escape(fragment)))

    ############################################################################
    # Locator methods
    # Scope: Every page > locators -> Playwright locators
    ############################################################################
    def find_element(self, locator: str) -> Locator:
        """The first element matching ``locator``.

        Playwright locators are lazy: nothing is searched until an action or expect() uses the
        result, and then it waits for the element.

        :param locator: XPath locator, e.g. "//*[@id='cart']"
        :return: a Playwright Locator
        """
        return self.find_elements(locator).first

    def find_elements(self, locator: str) -> Locator:
        """Every element matching ``locator`` (count it, filter it, or expect a count).

        :param locator: XPath locator
        :return: a Playwright Locator for all matches
        """
        return self.page.locator(self._helper.by_locator(locator))

    ############################################################################
    # Action methods
    # Scope: Every page > click, type, submit
    ############################################################################
    def click_element(self, locator: str):
        """Click the element; Playwright first waits until it is visible, stable and enabled.

        :param locator: XPath locator
        """
        self.logger.info("Click %s", locator)
        self.find_element(locator).click()

    def click_and_wait_for_new_page(self, locator: str):
        """Click a form button and wait for the resulting navigation to finish.

        wait_for_load_state() alone returns at once (the old page is already loaded), so the next
        goto() could cancel the POST. Unit 1 hit this as findings F7/F8; both units wait here.

        :param locator: XPath locator of the submit button
        """
        with self.page.expect_navigation(wait_until="domcontentloaded"):
            self.click_element(locator)

    def click_and_wait_for_response(self, locator: str, url_part: str, method: str = "POST") -> Response:
        """Click and wait for the server's answer to the request this click sends (Day 6: network-aware wait).

        :param locator: XPath locator of the element to click
        :param url_part: part of the request URL, e.g. "/cart/add"
        :param method: HTTP method of that request
        :return: the Playwright Response
        """
        with self.page.expect_response(lambda r: url_part in r.url and r.request.method == method) as answer:
            self.click_element(locator)
        self.logger.info("%s %s -> HTTP %s", method, url_part, answer.value.status)
        return answer.value

    def type_text(self, locator: str, text: str, secret: bool = False):
        """Replace the field's text with ``text``.

        :param locator: XPath locator of the input
        :param text: text to type
        :param secret: a password: the log shows *** instead of the text
        """
        self.logger.info("Type %r into %s", "***" if secret else text, locator)
        self.find_element(locator).fill(text)

    ############################################################################
    # State methods
    # Scope: Every page > element state
    ############################################################################
    def is_element_visible(self, locator: str, timeout: float = 0) -> bool:
        """True when the element is visible, waiting up to ``timeout`` seconds (0: check now).

        :param locator: XPath locator
        :param timeout: seconds to wait for the state; never a fixed sleep
        :return: True or False, never an exception
        """
        element = self.find_element(locator)
        if not timeout:
            return element.is_visible()
        try:
            element.wait_for(state="visible", timeout=timeout * 1000)
        except PlaywrightTimeoutError:
            self.logger.info("Element %s is not visible", locator)
            return False
        return True

    ############################################################################
    # Header methods
    # Scope: Every page > Header (cart link, search box)
    ############################################################################
    @property
    def header_cart_link(self) -> Locator:
        """The header link "My Cart (N)"."""
        return self.find_element(self._header_cart_link)

    def search_for(self, keyword: str):
        """Search for ``keyword`` from the header and wait for the results page."""
        self.type_text(self._search_box, keyword)
        self.find_element(self._search_box).press("Enter")
        self.wait_until_url_contains("/search")

    # --- Locators -------------------------------------------------------------
    # Header (on every page). Desktop and mobile cart links both say "My Cart (N)"; the first is the desktop one.
    _header_cart_link = "//a[contains(normalize-space(),'My Cart')]"
    _search_box = "//input[@name='q']"
