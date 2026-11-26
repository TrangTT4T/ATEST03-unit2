"""Search results page: /search?q=<keyword>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class SearchPage(BasePage):
    @property
    def result_links(self) -> Locator:
        return self.page.locator(self._result_links)

    @property
    def no_results_message(self) -> Locator:
        return self.page.locator(self._no_results_message)

    # --- Locators -------------------------------------------------------------
    _result_links = "a[href*='/products/']"
    _no_results_message = "text=No results found for"
