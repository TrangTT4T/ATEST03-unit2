"""Base Page Object (Playwright, sync API): navigation and the custom element methods every page uses.

Locators are plain XPath strings that describe the element, grouped under a comment that names the
area of the page, at the bottom of each class (the same layout as Unit 1):

    # Cart list
    _cart_items = "//*[@data-test='inventory-item']"
    # Product cards
    _product_card = "//*[@data-test='inventory-item'][.//*[normalize-space()='{}']]"   # .format(name)

Swag Labs marks its elements with ``data-test`` attributes (made for test automation), so most
locators read ``//*[@data-test='...']``. ``Helper.by_locator()`` (helper_utility/helpers.py) turns a
locator into a Playwright selector: plain XPath by default, or "id=...", "name=...", "css=...".

Pages never call ``self.page.locator`` or ``goto`` themselves: they call the BasePage methods, which
log the action and name the locator in their errors. Playwright waits on every action and
``expect()`` retries, so nothing here sleeps for a fixed time.

Swag Labs is a single-page app: a click changes the address without loading a new page, so the
pages wait for the address (``wait_until_url_contains``) rather than for a page load.

Layout of every page object (one class per file):

* methods grouped under ``####`` banners that name the area of the page (``# Scope: ...``);
* a docstring on every public method and property;
* a ``# --- Locators ---`` section at the BOTTOM of the class: XPath strings, grouped by area.
"""
import contextlib
import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from helper_utility.helpers import Helper


class BasePage:
    path = "/"

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(type(self).__name__)  # in the report of a failed test
        self._helper = Helper()  # locators, prices, test data

    ############################################################################
    # Navigation methods
    # Scope: Every page
    ############################################################################
    def open_page(self, path: str | None = None):
        """Go to ``path`` on the shop (default: this page's own path).

        :param path: path after the base URL, e.g. "/cart.html"
        """
        self.logger.info("Open %s", path or self.path)
        with self._report_timeout("Opening", path or self.path):
            self.page.goto(path or self.path)  # relative: pytest-playwright gives every context the --base-url

    def add_login_cookies(self, login_state_file: Path):
        """Put the cookies of a saved login state (context.storage_state) into this page's context.

        The next page opened is then logged in, without the login form. Only the cookies: the
        localStorage of the saved state (Swag Labs keeps the cart there) is left out.
        """
        cookies = json.loads(Path(login_state_file).read_text(encoding="utf-8"))["cookies"]
        self.page.context.add_cookies(cookies)
        self.logger.info("Use the saved login of %s", Path(login_state_file).name)

    def wait_until_url_contains(self, fragment: str):
        """Wait until the address contains ``fragment``, for example "/cart.html"."""
        with self._report_timeout("Waiting for the URL to contain", fragment):
            self.page.wait_for_url(re.compile(re.escape(fragment)))

    def wait_until_url_ends_with(self, suffix: str):
        """Wait until the address ends with ``suffix``, for example "/" for the login page."""
        with self._report_timeout("Waiting for the URL to end with", suffix):
            self.page.wait_for_url(re.compile(re.escape(suffix) + "$"))

    ############################################################################
    # Locator methods
    # Scope: Every page > locators -> Playwright locators
    ############################################################################
    def find_element(self, locator: str) -> Locator:
        """The first element matching ``locator``.

        Playwright locators are lazy: nothing is searched until an action or expect() uses the
        result, and then it waits for the element.

        :param locator: XPath locator, e.g. "//*[@data-test='checkout']"
        :return: a Playwright Locator
        """
        return self.find_elements(locator).first

    def find_elements(self, locator: str) -> Locator:
        """Every element matching ``locator`` (count it, filter it, or expect a count).

        :param locator: XPath locator
        :return: a Playwright Locator for all matches
        """
        return self.page.locator(self._helper.by_locator(locator))

    def get_texts(self, locator: str) -> list[str]:
        """The visible text of every element matching ``locator``, in page order.

        :param locator: XPath locator, e.g. the name of every product card
        :return: the texts, stripped
        """
        return [text.strip() for text in self.find_elements(locator).all_inner_texts()]

    ############################################################################
    # Action methods
    # Scope: Every page > click, type, select
    ############################################################################
    def click_element(self, locator: str):
        """Click the element; Playwright first waits until it is visible, stable and enabled.

        :param locator: XPath locator
        """
        self.logger.info("Click %s", locator)
        with self._report_timeout("Clicking", locator):
            self.find_element(locator).click()

    def type_text(self, locator: str, text: str, secret: bool = False):
        """Replace the field's text with ``text``.

        :param locator: XPath locator of the input
        :param text: text to type
        :param secret: a password: the log shows *** instead of the text
        """
        self.logger.info("Type %r into %s", "***" if secret else text, locator)
        with self._report_timeout("Typing into", locator):
            self.find_element(locator).fill(text)

    def click_and_download(self, locator: str, folder: Path) -> Path:
        """Click an element that starts a download and save the file in ``folder`` under its own name.

        :param locator: XPath locator of the button or link
        :param folder: where to save the file (e.g. pytest's tmp_path)
        :return: the path of the saved file
        """
        with self._report_timeout("Waiting for the download started by clicking", locator):
            with self.page.expect_download() as download_info:
                self.click_element(locator)
        download = download_info.value
        path = Path(folder) / download.suggested_filename
        download.save_as(path)
        self.logger.info("Downloaded %s", path.name)
        return path

    def select_option(self, locator: str, label: str):
        """Choose the option labelled ``label`` in a drop-down list.

        :param locator: XPath locator of the <select>
        :param label: the visible text of the option, e.g. "Price (low to high)"
        """
        self.logger.info("Select %r in %s", label, locator)
        with self._report_timeout(f"Selecting {label!r} in", locator):
            self.find_element(locator).select_option(label=label)

    def is_wider_than_the_screen(self) -> bool:
        """True when the page scrolls sideways: its content is wider than the screen (a layout defect on a phone)."""
        return self.page.evaluate("document.documentElement.scrollWidth > window.innerWidth")

    def get_screen_width(self) -> int:
        """The width of the browser's viewport in CSS pixels, e.g. 390 on an iPhone 13."""
        return self.page.evaluate("window.innerWidth")

    def take_screenshot(self) -> bytes:
        """A full-page PNG once the page has settled: no network traffic, web fonts loaded, no animation."""
        self.logger.info("Screenshot of %s", self.page.url)
        self.page.wait_for_load_state("networkidle")
        self.page.evaluate("document.fonts.ready")
        return self.page.screenshot(full_page=True, animations="disabled", caret="hide")

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
    # Scope: Every page after login > Header (title, cart badge, cart link)
    ############################################################################
    @property
    def page_title(self) -> Locator:
        """The title under the header, e.g. "Products", "Your Cart", "Checkout: Overview"."""
        return self.find_element(self._page_title)

    @property
    def cart_badge(self) -> Locator:
        """The number on the cart icon; absent when the cart is empty."""
        return self.find_element(self._cart_badge)

    def get_cart_badge_count(self) -> int:
        """The number on the cart icon, 0 when the cart is empty (the badge is then absent)."""
        if not self.is_element_visible(self._cart_badge):
            return 0
        return int(self.cart_badge.inner_text())

    def open_cart(self):
        """Click the cart icon and wait for the cart page."""
        self.click_element(self._cart_link)
        self.wait_until_url_contains("/cart.html")

    ############################################################################
    # Menu methods
    # Scope: Every page after login > Side menu (Logout, Reset App State)
    ############################################################################
    def logout(self):
        """Open the side menu, click Logout and wait for the login page."""
        self.click_element(self._menu_button)
        self.click_element(self._logout_link)
        self.wait_until_url_ends_with("/")  # the login page is the root of the shop

    def reset_app_state(self):
        """Open the side menu, click Reset App State (empties the cart) and close the menu."""
        self.click_element(self._menu_button)
        self.click_element(self._reset_link)
        self.click_element(self._close_menu_button)

    @contextlib.contextmanager
    def _report_timeout(self, action: str, target: str) -> Iterator[None]:
        """Turn a Playwright timeout into an ERROR log line and an error that names the target and the page.

        Playwright's own message lists its call log; this one says first what the test was doing,
        e.g. "Clicking '//*[@data-test='checkout']' timed out on https://.../cart.html".
        """
        try:
            yield
        except PlaywrightTimeoutError as error:
            message = f"{action} {target!r} timed out on {self.page.url}"
            self.logger.error(message)
            raise PlaywrightTimeoutError(f"{message}\n{error}") from error

    # --- Locators -------------------------------------------------------------
    # Header
    _page_title = "//*[@data-test='title']"
    _cart_link = "//*[@data-test='shopping-cart-link']"
    _cart_badge = "//*[@data-test='shopping-cart-badge']"
    # Side menu
    _menu_button = "//*[@id='react-burger-menu-btn']"
    _close_menu_button = "//*[@id='react-burger-cross-btn']"
    _logout_link = "//*[@data-test='logout-sidebar-link']"
    _reset_link = "//*[@data-test='reset-sidebar-link']"
