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

Layout of every page object (one class per file):

* methods grouped under ``####`` banners that name the area of the page (``# Scope: ...``);
* a docstring on every public method and property;
* a ``# --- Locators ---`` section at the BOTTOM of the class: XPath strings, grouped by area.
"""
import contextlib
import logging
import re
from collections.abc import Iterator

from playwright.sync_api import Locator, Page, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from helper_utility.helpers import Helper


class BasePage:
    path = "/"
    BOT_CHECK_TITLES = ("Verifying your connection", "Just a moment")  # the store's bot protection page

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(type(self).__name__)  # in the report of a failed test
        self._helper = Helper()  # locators, prices, test data

    ############################################################################
    # Navigation methods
    # Scope: Every page
    ############################################################################
    def open_page(self, path: str | None = None):
        """Go to ``path`` on the store (default: this page's own path).

        :param path: path after the base URL, e.g. "/cart"
        """
        self.logger.info("Open %s", path or self.path)
        with self._report_timeout("Opening", path or self.path):
            self.page.goto(path or self.path)  # relative: pytest-playwright gives every context the --base-url
        self._verify_not_bot_check(f"opening {path or self.path}")

    def wait_until_url_contains(self, fragment: str):
        """Wait until the address contains ``fragment``, for example "/search"."""
        with self._report_timeout("Waiting for the URL to contain", fragment):
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
        with self._report_timeout("Clicking", locator):
            self.find_element(locator).click()

    def click_and_wait_for_new_page(self, locator: str):
        """Click a form button and wait for the resulting navigation to finish.

        wait_for_load_state() alone returns at once (the old page is already loaded), so the next
        goto() could cancel the POST. Unit 1 hit this as findings F7/F8; both units wait here.

        :param locator: XPath locator of the submit button
        """
        with self._report_timeout("Waiting for the page loaded by clicking", locator):
            with self.page.expect_navigation(wait_until="domcontentloaded"):
                self.click_element(locator)

    def click_and_wait_for_response(self, locator: str, url_part: str, method: str = "POST") -> Response:
        """Click and wait for the server's answer to the request this click sends (Day 6: network-aware wait).

        :param locator: XPath locator of the element to click
        :param url_part: part of the request URL, e.g. "/cart/add"
        :param method: HTTP method of that request
        :return: the Playwright Response
        """
        with self._report_timeout(f"Waiting for the {method} {url_part} answer to clicking", locator):
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
        with self._report_timeout("Typing into", locator):
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
    # Scope: Every page > Header (cart link, search box, account links)
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
        self._verify_not_bot_check(f"searching for {keyword!r}")

    def is_customer_logged_in(self) -> bool:
        """True when a customer is logged in: the header no longer offers "Log In"."""
        return not self.is_element_visible(self._login_link)

    def open_login_page_from_header(self):
        """Click the header's "Log In" link and wait for the login page."""
        self.click_and_wait_for_new_page(self._login_link)

    def open_register_page_from_header(self):
        """Click the header's "Sign up" link and wait for the registration page."""
        self.click_and_wait_for_new_page(self._register_link)

    def logout(self):
        """Log the customer out: open /account/logout (where the header's Log Out link goes)."""
        self.open_page(self._logout_path)

    def _verify_not_bot_check(self, action: str):
        """Stop with a clear error when the store shows its bot check (Cloudflare) instead of the page.

        The check is never bypassed. It usually means too many requests from this network in a short
        time: the store asks a human to confirm, which an automated test cannot and must not do.

        :param action: what the test was doing, e.g. "opening /cart"
        """
        title = self.page.title()
        if any(check in title for check in self.BOT_CHECK_TITLES):
            self.logger.error("The store showed its bot check (%r) instead of %s", title, action)
            raise AssertionError(f"The store asked to verify a human ({title!r}) instead of {action}: too many "
                                 f"requests from this network. Wait a few minutes, then run the suite again")

    @contextlib.contextmanager
    def _report_timeout(self, action: str, target: str) -> Iterator[None]:
        """Turn a Playwright timeout into an ERROR log line and an error that names the target and the page.

        Playwright's own message lists its call log; this one says first what the test was doing,
        e.g. "Clicking '//*[@id='checkout']' timed out on https://.../cart".
        """
        try:
            yield
        except PlaywrightTimeoutError as error:
            message = f"{action} {target!r} timed out on {self.page.url}"
            self.logger.error(message)
            raise PlaywrightTimeoutError(f"{message}\n{error}") from error

    # --- Locators -------------------------------------------------------------
    # Header (on every page). Desktop and mobile cart links both say "My Cart (N)"; the first is the desktop one.
    _header_cart_link = "//a[contains(normalize-space(),'My Cart')]"
    _search_box = "//input[@name='q']"
    # Header account links: desktop "Log In" / "Sign up" come first, the hidden mobile ones after
    _login_link = "//a[contains(@href,'/account/login')]"
    _register_link = "//a[contains(@href,'/account/register')]"
    _logout_path = "/account/logout"
