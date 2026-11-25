"""Search results page: /search?q=<keyword>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class SearchPage(BasePage):
    @property
    def result_links(self) -> Locator:
        return self.page.locator(self._result_links)

    # --- Locators -------------------------------------------------------------
    _result_links = "a[href*='/products/']"
