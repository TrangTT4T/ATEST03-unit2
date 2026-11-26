"""Search results page: /search?q=<keyword>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class SearchPage(BasePage):
    ############################################################################
    # Search result methods
    # Scope: Search > Results page
    ############################################################################
    @property
    def result_links(self) -> Locator:
        """The links to the products found."""
        return self.page.locator(self._result_links)

    @property
    def no_results_message(self) -> Locator:
        """The "No results found for ..." message."""
        return self.page.locator(self._no_results_message)

    # --- Locators -------------------------------------------------------------
    _result_links = "a[href*='/products/']"
    _no_results_message = "text=No results found for"
